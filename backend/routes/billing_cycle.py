"""
Billing cycle automation for FortexaRH.

Daily cron tasks:
- `generate_pending_invoices_for_overdue_subs`: when a subscription's
  current_period_end is in the past and the next period has no invoice yet,
  create a "pending" invoice and mark the subscription as past_due.
- `suspend_overdue_subscriptions`: subscriptions past_due for more than
  GRACE_DAYS get status=suspended; the company is then routed to the
  /billing-required page on next login.

Endpoints (company-scoped, JWT auth):
- GET  /api/billing/status         → {has_pending, pending_invoice, is_blocked, grace_days_left}
- POST /api/billing/pay-pending    → {checkout_url} (Stripe Checkout)
- POST /api/billing/internal/run   → super_admin manual trigger of both crons
"""
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import stripe
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from config import db, SUBSCRIPTION_PLANS
from utils.auth import get_current_user

router = APIRouter(prefix="/billing", tags=["Billing"])
logger = logging.getLogger(__name__)


GRACE_DAYS = 3  # days after current_period_end before suspending the subscription


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


async def _compute_invoice_amount(company_id: str, plan_id: str) -> tuple[float, float, float, int]:
    """Return (base_price, per_employee, total, employee_count) for the given plan/company."""
    plan = SUBSCRIPTION_PLANS.get(plan_id) or {}
    base = float(plan.get("base_price", 0))
    per_emp = float(plan.get("price_per_employee", 0))
    employee_count = await db.employees.count_documents({
        "company_id": company_id,
        "status": {"$nin": ["inactive", "terminated", "fired"]},
    })
    total = round(base + (employee_count * per_emp), 2)
    return base, per_emp, total, employee_count


# -------------------- CRONS --------------------

async def generate_pending_invoices_for_overdue_subs() -> int:
    """Create a pending invoice for every active subscription past its period_end
    that doesn't already have one for the next cycle. Returns number created."""
    now = _now()
    created = 0
    cursor = db.subscriptions.find(
        {"status": {"$in": ["active", "past_due"]}},
        {"_id": 0},
    )
    async for sub in cursor:
        company_id = sub.get("company_id")
        plan_id = sub.get("plan_id")
        if not company_id or not plan_id or plan_id in ("trial", "free"):
            continue
        period_end_dt = _parse_iso(sub.get("current_period_end"))
        if not period_end_dt or period_end_dt >= now:
            continue
        # Only paid plans should auto-invoice
        if plan_id not in SUBSCRIPTION_PLANS:
            continue
        # Check if a pending invoice already exists for this period
        next_period_start = period_end_dt
        next_period_end = next_period_start + timedelta(days=30)
        existing = await db.invoices.find_one({
            "company_id": company_id,
            "status": "pending",
            "period_start_iso": next_period_start.isoformat(),
        }, {"_id": 0, "invoice_id": 1})
        if existing:
            continue
        company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1})
        base, per_emp, total, emp_count = await _compute_invoice_amount(company_id, plan_id)
        invoice_id = f"inv_{uuid.uuid4().hex[:12]}"
        invoice_number = f"FRH-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        invoice_data = {
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "company_id": company_id,
            "company_name": (company or {}).get("name", ""),
            "plan_id": plan_id,
            "plan_name": SUBSCRIPTION_PLANS[plan_id].get("name", plan_id),
            "employee_count": emp_count,
            "base_price": base,
            "price_per_employee": per_emp,
            "subtotal": total,
            "tax": 0,
            "total": total,
            "currency": "USD",
            "status": "pending",
            "period_start": next_period_start.strftime("%d/%m/%Y"),
            "period_end": next_period_end.strftime("%d/%m/%Y"),
            "period_start_iso": next_period_start.isoformat(),
            "period_end_iso": next_period_end.isoformat(),
            "due_at": next_period_start.isoformat(),
            "created_at": now.isoformat(),
        }
        await db.invoices.insert_one(invoice_data)
        await db.subscriptions.update_one(
            {"company_id": company_id},
            {"$set": {"status": "past_due", "past_due_since": now.isoformat()}},
        )
        created += 1
        logger.info(f"billing: pending invoice {invoice_number} created for {company_id}")
    return created


async def suspend_overdue_subscriptions() -> int:
    """Suspend any subscription that has been past_due longer than GRACE_DAYS."""
    cutoff = (_now() - timedelta(days=GRACE_DAYS)).isoformat()
    res = await db.subscriptions.update_many(
        {"status": "past_due", "past_due_since": {"$lt": cutoff}},
        {"$set": {"status": "suspended", "suspended_at": _now().isoformat()}},
    )
    if res.modified_count:
        logger.info(f"billing: suspended {res.modified_count} subscription(s) past grace")
    return res.modified_count


async def run_billing_cycle() -> dict:
    """Run both daily tasks. Safe to call any time."""
    created = await generate_pending_invoices_for_overdue_subs()
    suspended = await suspend_overdue_subscriptions()
    return {"invoices_created": created, "subscriptions_suspended": suspended}


# -------------------- ENDPOINTS --------------------

@router.get("/status")
async def get_billing_status(current_user: dict = Depends(get_current_user)):
    """Return the company's billing status: pending invoice (if any) and whether
    the company is blocked (suspended) and should be redirected to /billing-required."""
    company_id = current_user.get("company_id")
    if not company_id:
        return {"has_pending": False, "is_blocked": False}

    sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0}) or {}
    pending = await db.invoices.find_one(
        {"company_id": company_id, "status": "pending"},
        {"_id": 0},
        sort=[("created_at", -1)],
    )

    grace_days_left = 0
    if sub.get("status") == "past_due":
        past_due_since = _parse_iso(sub.get("past_due_since"))
        if past_due_since:
            elapsed = (_now() - past_due_since).days
            grace_days_left = max(0, GRACE_DAYS - elapsed)

    return {
        "has_pending": bool(pending),
        "pending_invoice": pending,
        "is_blocked": sub.get("status") == "suspended",
        "subscription_status": sub.get("status"),
        "grace_days_left": grace_days_left,
        "current_period_end": sub.get("current_period_end"),
    }


class PayPendingRequest(BaseModel):
    invoice_id: str
    origin_url: str


@router.post("/pay-pending")
async def pay_pending_invoice(data: PayPendingRequest, current_user: dict = Depends(get_current_user)):
    """Create a Stripe Checkout Session to pay a pending invoice. The user can
    enter any card; we do not require a saved payment method."""
    company_id = current_user.get("company_id")
    invoice = await db.invoices.find_one(
        {"invoice_id": data.invoice_id, "company_id": company_id, "status": "pending"},
        {"_id": 0},
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura pendiente no encontrada")

    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe no configurado")
    stripe.api_key = api_key

    amount = float(invoice.get("total", 0))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Monto inválido")

    host_url = data.origin_url.rstrip("/")
    success_url = f"{host_url}/subscriptions?session_id={{CHECKOUT_SESSION_ID}}&status=success"
    cancel_url = f"{host_url}/billing-required?status=cancelled"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": (invoice.get("currency") or "usd").lower(),
                    "unit_amount": int(round(amount * 100)),
                    "product_data": {
                        "name": f"{invoice.get('plan_name', invoice.get('plan_id'))} — factura {invoice.get('invoice_number')}",
                        "description": f"Período {invoice.get('period_start')} - {invoice.get('period_end')} ({invoice.get('employee_count', 0)} empleado(s))",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "company_id": company_id,
                "user_id": current_user.get("user_id"),
                "plan_id": invoice.get("plan_id"),
                "plan_name": invoice.get("plan_name", invoice.get("plan_id")),
                "employee_count": str(invoice.get("employee_count", 0)),
                "base_price": str(invoice.get("base_price", 0)),
                "price_per_employee": str(invoice.get("price_per_employee", 0)),
                "total_amount": str(amount),
                "invoice_id": invoice.get("invoice_id"),
                "settle_pending_invoice": "1",
            },
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Stripe pay-pending error: {e}")
        raise HTTPException(status_code=500, detail="No se pudo crear la sesión de pago") from e

    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "session_id": session.id,
        "company_id": company_id,
        "user_id": current_user.get("user_id"),
        "plan_id": invoice.get("plan_id"),
        "plan_name": invoice.get("plan_name"),
        "employee_count": invoice.get("employee_count"),
        "amount": amount,
        "currency": invoice.get("currency", "USD"),
        "payment_status": "initiated",
        "invoice_id": invoice.get("invoice_id"),
        "created_at": _now().isoformat(),
    })
    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/internal/run")
async def manual_run_billing(request: Request):
    """Manual trigger of the daily billing cycle. Requires the
    `X-Internal-Token` header to match INTERNAL_CRON_TOKEN (super_admin only)."""
    expected = os.environ.get("INTERNAL_CRON_TOKEN", "")
    if not expected or request.headers.get("x-internal-token") != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await run_billing_cycle()
    return {"ok": True, **result}
