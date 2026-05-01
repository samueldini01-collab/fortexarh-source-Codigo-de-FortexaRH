"""Smart fiscal reminders — per-company computation + parallelized cron driver.

Public functions:
- ``_run_reminders_for_company(company_id)`` — used by the per-company endpoint.
- ``run_reminders_for_all_companies(...)`` — used by the daily APScheduler cron.

Endpoints:
- ``POST /calendar/run-reminders``       — manual trigger for the caller's company.
- ``POST /calendar/run-reminders-all``   — manual trigger for ALL companies (admin only).
"""
from __future__ import annotations

import asyncio
import logging
from calendar import monthrange
from datetime import datetime, timezone

from fastapi import Depends, HTTPException

from config import db
from routes.country_config import COUNTRY_PROFILES
from utils.auth import get_current_user

from . import router
from .catalog import FORMAT_DEADLINES, NATIVE_FORMATS

logger = logging.getLogger(__name__)


# ===================== PER-COMPANY HELPER =====================

async def _run_reminders_for_company(company_id: str) -> dict:
    """Compute and dispatch fiscal-deadline notifications for a single company."""
    # Local import to avoid load-time cycles with the notifications module.
    from routes.notifications_system import create_notification

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    company_country = (company or {}).get("country", "DO")

    today = datetime.now(timezone.utc).date()
    notifications_sent = 0
    skipped_filed = 0

    for country_code, formats in NATIVE_FORMATS.items():
        if country_code != company_country:
            continue
        profile = COUNTRY_PROFILES.get(country_code, {})
        for fmt in formats:
            if not fmt.get("implemented"):
                continue
            deadline_cfg = FORMAT_DEADLINES.get(fmt["code"])
            if not deadline_cfg:
                continue
            day = deadline_cfg["day"]
            offset = deadline_cfg["offset_months"]
            current_month = today.month
            current_year = today.year
            try_day = min(day, monthrange(current_year, current_month)[1])
            try_date = datetime(current_year, current_month, try_day, tzinfo=timezone.utc).date()
            if try_date < today:
                if current_month == 12:
                    next_year, next_month = current_year + 1, 1
                else:
                    next_year, next_month = current_year, current_month + 1
                try_day = min(day, monthrange(next_year, next_month)[1])
                try_date = datetime(next_year, next_month, try_day, tzinfo=timezone.utc).date()
            days_until = (try_date - today).days
            filing_month = try_date.month - offset
            filing_year = try_date.year
            while filing_month <= 0:
                filing_month += 12
                filing_year -= 1
            period_str = f"{filing_year}-{filing_month:02d}"

            already_filed = await db.fiscal_filings.find_one({
                "company_id": company_id,
                "country_code": country_code,
                "format_code": fmt["code"],
                "period": period_str,
            })
            if already_filed:
                skipped_filed += 1
                continue

            if days_until not in (7, 3, 1, 0, -1):
                continue

            urgency = "critical" if days_until <= 1 else ("warning" if days_until <= 3 else "normal")
            title = f"{profile.get('flag', '')} {fmt['name']} — vence en {days_until} día{'s' if days_until != 1 else ''}"
            if days_until <= 0:
                title = f"⚠️ {profile.get('flag', '')} {fmt['name']} — VENCIDO"
            message = (
                f"Tu empresa debe presentar {fmt['name']} ante {fmt['agency']} "
                f"el {try_date.isoformat()}. Período a declarar: {period_str}."
            )

            await create_notification(
                company_id=company_id,
                title=title,
                message=message,
                notification_type="fiscal_deadline",
                priority=urgency if urgency in ("critical", "warning") else "normal",
                link="/global-compliance",
                target_role="admin",
                metadata={
                    "country_code": country_code,
                    "format_code": fmt["code"],
                    "period": period_str,
                    "due_date": try_date.isoformat(),
                    "days_until_due": days_until,
                    "endpoint": fmt.get("endpoint"),
                },
            )
            notifications_sent += 1

    return {
        "company_id": company_id,
        "company_country": company_country,
        "notifications_sent": notifications_sent,
        "skipped_already_filed": skipped_filed,
    }


# ===================== GLOBAL CRON DRIVER (paginated + bounded concurrency) =====================

async def run_reminders_for_all_companies(
    batch_size: int = 100,
    max_concurrency: int = 10,
    queue_high_water: int = 200,
) -> dict:
    """Iterate every active company and dispatch fiscal-deadline reminders.

    Architecture: producer/consumer via ``asyncio.Queue`` for true backpressure.

    - **Producer**: an async task that streams companies from MongoDB
      (``cursor.batch_size``) and puts each ``company_id`` onto a bounded queue
      (``maxsize=queue_high_water``). When the queue is full the producer
      ``await``s, applying natural backpressure when consumers are slow.
    - **Consumers**: ``max_concurrency`` worker tasks pull from the queue and
      run ``_run_reminders_for_company`` per item. A sentinel ``None`` is
      placed by the producer for each worker on completion to signal shutdown.

    This pattern scales to hundreds of thousands of tenants without buffering
    every company in memory at once.
    """
    started_at = datetime.now(timezone.utc)
    queue: asyncio.Queue = asyncio.Queue(maxsize=queue_high_water)

    total_notifications = 0
    total_skipped = 0
    processed = 0
    errors: list[dict] = []
    _lock = asyncio.Lock()  # protect counters under concurrent updates

    async def _producer() -> int:
        """Stream companies onto the queue; returns count produced."""
        produced = 0
        cursor = db.companies.find({}, {"_id": 0, "company_id": 1}).batch_size(batch_size)
        async for company in cursor:
            cid = company.get("company_id")
            if not cid:
                continue
            await queue.put(cid)
            produced += 1
        # Sentinel per consumer to signal "no more work".
        for _ in range(max_concurrency):
            await queue.put(None)
        return produced

    async def _consumer(worker_id: int) -> None:
        nonlocal total_notifications, total_skipped, processed
        while True:
            cid = await queue.get()
            try:
                if cid is None:
                    return  # shutdown sentinel
                try:
                    res = await _run_reminders_for_company(cid)
                    async with _lock:
                        total_notifications += res["notifications_sent"]
                        total_skipped += res["skipped_already_filed"]
                        processed += 1
                except Exception as exc:  # noqa: BLE001
                    async with _lock:
                        errors.append({"company_id": cid, "error": str(exc)})
            finally:
                queue.task_done()

    # Run producer + N consumers concurrently.
    consumer_tasks = [
        asyncio.create_task(_consumer(i)) for i in range(max_concurrency)
    ]
    producer_task = asyncio.create_task(_producer())

    produced_count = await producer_task
    await asyncio.gather(*consumer_tasks)

    if errors:
        logger.warning(
            "Fiscal reminders: %d company error(s) during cron run "
            "(produced=%d processed=%d notifications=%d).",
            len(errors), produced_count, processed, total_notifications,
        )

    return {
        "success": True,
        "processed_companies": processed,
        "total_notifications_sent": total_notifications,
        "total_skipped_already_filed": total_skipped,
        "errors": errors,
        "ran_at": started_at.isoformat(),
        "duration_seconds": (datetime.now(timezone.utc) - started_at).total_seconds(),
        "batch_size": batch_size,
        "max_concurrency": max_concurrency,
        "queue_high_water": queue_high_water,
        "produced_companies": produced_count,
    }


# ===================== ENDPOINTS =====================

@router.post("/calendar/run-reminders")
async def run_calendar_reminders(current_user: dict = Depends(get_current_user)):
    """Manually trigger fiscal deadline reminders for the caller's company."""
    company_id = current_user.get("company_id")
    res = await _run_reminders_for_company(company_id)
    res["success"] = True
    res["checked_at"] = datetime.now(timezone.utc).isoformat()
    return res


@router.post("/calendar/run-reminders-all")
async def run_reminders_all_endpoint(current_user: dict = Depends(get_current_user)):
    """Manually trigger the global cron job (admin tool / debugging).

    In production the APScheduler daily job runs this automatically at 08:00 UTC.
    """
    if (current_user.get("role") or "").lower() not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar el cron global")
    return await run_reminders_for_all_companies()
