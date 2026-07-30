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


# -------------------- DUNNING EMAILS --------------------

REMINDER_UPCOMING_DAYS = 3  # warn N days before period_end (no invoice yet)


def _build_reminder_html(kind: str, name: str, sub: dict, invoice: Optional[dict], company_name: str) -> tuple[str, str]:
    """Return (subject, html) for the given dunning email kind."""
    plan_name = (invoice or {}).get("plan_name") or sub.get("plan_id", "")
    period_end = (invoice or {}).get("period_end") or sub.get("current_period_end", "")
    amount = float((invoice or {}).get("total") or 0)
    invoice_number = (invoice or {}).get("invoice_number", "")
    cta_url = "https://fortexarh.com/subscriptions"

    if kind == "upcoming":
        subject = f"Tu suscripción de FortexaRH vence en {REMINDER_UPCOMING_DAYS} días"
        title = f"Tu próxima factura vence en {REMINDER_UPCOMING_DAYS} días"
        body = (
            f"Hola {name},<br/><br/>"
            f"Tu suscripción <b>{plan_name}</b> de <b>{company_name}</b> tiene su próximo cobro programado."
            f" Asegúrate de tener una tarjeta válida o de iniciar el pago manualmente para no interrumpir el servicio."
        )
        color = "#0ea5e9"
        cta = "Ver mi suscripción"
    elif kind == "due":
        subject = f"Factura {invoice_number} vencida — paga ahora para evitar la suspensión"
        title = "Tu factura está vencida"
        body = (
            f"Hola {name},<br/><br/>"
            f"La factura <b>{invoice_number}</b> de <b>{company_name}</b> por <b>${amount:.2f}</b> está vencida."
            f" Para evitar que tu suscripción sea suspendida, paga ahora con cualquier tarjeta."
        )
        color = "#f59e0b"
        cta = "Pagar ahora"
    else:  # "final"
        subject = f"Última oportunidad — la cuenta de {company_name} será suspendida mañana"
        title = "Última oportunidad antes de la suspensión"
        body = (
            f"Hola {name},<br/><br/>"
            f"Tu factura <b>{invoice_number}</b> por <b>${amount:.2f}</b> sigue sin pagarse."
            f" Si no se completa el pago en las próximas 24 horas, la cuenta de <b>{company_name}</b> será"
            f" <b>suspendida automáticamente</b> y perderás acceso al sistema hasta regularizar el pago."
        )
        color = "#dc2626"
        cta = "Pagar ahora y mantener el servicio"

    period_html = (
        f"<tr><td style='padding:6px 0;color:#64748b;'>Período</td>"
        f"<td style='padding:6px 0;color:#0f172a;text-align:right;font-weight:600;'>{period_end}</td></tr>"
        if period_end else ""
    )
    invoice_html = (
        f"<tr><td style='padding:6px 0;color:#64748b;'>Factura</td>"
        f"<td style='padding:6px 0;color:#0f172a;text-align:right;font-family:monospace;'>{invoice_number}</td></tr>"
        if invoice_number else ""
    )
    amount_html = (
        f"<tr><td style='padding:6px 0;color:#64748b;'>Monto</td>"
        f"<td style='padding:6px 0;color:#0f172a;text-align:right;font-weight:700;font-size:18px;'>${amount:.2f}</td></tr>"
        if amount > 0 else ""
    )

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:0 auto;background:#fff;">
      <div style="background:{color};padding:24px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:#fff;margin:0;font-size:20px;">FortexaRH</h1>
        <p style="color:rgba(255,255,255,0.9);margin:4px 0 0;font-size:13px;">Recordatorio de facturación</p>
      </div>
      <div style="padding:28px;border:1px solid #e2e8f0;border-top:none;">
        <h2 style="color:#0f172a;margin:0 0 14px;font-size:18px;">{title}</h2>
        <p style="color:#475569;font-size:14px;line-height:1.6;">{body}</p>
        <table style="width:100%;margin:18px 0;border-collapse:collapse;font-size:14px;">
          <tr><td style="padding:6px 0;color:#64748b;">Plan</td><td style="padding:6px 0;color:#0f172a;text-align:right;font-weight:600;">{plan_name}</td></tr>
          {period_html}{invoice_html}{amount_html}
        </table>
        <div style="text-align:center;margin:22px 0;">
          <a href="{cta_url}" style="display:inline-block;background:{color};color:#fff;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:600;">{cta}</a>
        </div>
        <p style="color:#94a3b8;font-size:12px;line-height:1.5;">
          Puedes pagar con cualquier tarjeta de crédito o débito desde la página de Suscripción.
          Si ya pagaste, ignora este mensaje.
        </p>
      </div>
      <div style="background:#f8fafc;padding:12px;text-align:center;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">Mensaje automático de FortexaRH · No respondas a este correo.</p>
      </div>
    </div>
    """
    return subject, html


async def _send_dunning_email(kind: str, company_id: str, invoice: Optional[dict], sub: dict) -> bool:
    """Send a dunning email. Honors notification preferences. Idempotent at caller."""
    try:
        import asyncio as _asyncio
        import resend
        if not os.environ.get("RESEND_API_KEY"):
            return False
        # Find the company's admin
        user = await db.users.find_one(
            {"company_id": company_id, "role": {"$in": ["admin", "owner"]}},
            {"_id": 0, "email": 1, "name": 1, "user_id": 1},
        ) or await db.users.find_one(
            {"company_id": company_id},
            {"_id": 0, "email": 1, "name": 1, "user_id": 1},
        )
        if not user:
            return False
        # Respect notification preferences
        try:
            from routes.notification_preferences import should_notify_user
            allow = await should_notify_user(user["user_id"], "billing_reminder", "email")
        except Exception:
            allow = True
        if not allow:
            return False
        company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1}) or {}
        sender = os.environ.get("SENDER_EMAIL", "noreply@fortexaerp.com")
        subject, html = _build_reminder_html(
            kind, user.get("name") or user["email"], sub, invoice, company.get("name", "tu empresa")
        )
        params = {
            "from": f"FortexaRH <{sender}>",
            "to": [user["email"]],
            "subject": subject,
            "html": html,
        }
        await _asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"billing: '{kind}' reminder sent to {user['email']} (company={company_id})")
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning(f"dunning email '{kind}' failed for company {company_id}: {e}")
        return False


async def send_billing_reminders() -> dict:
    """Send dunning emails:
    - 'upcoming': D-3 before current_period_end for active subs (no invoice yet).
    - 'due': pending invoice exists and hasn't been notified of due-date yet.
    - 'final': past_due >= GRACE_DAYS-1 days (last call before suspension).
    """
    now = _now()
    counts = {"upcoming": 0, "due": 0, "final": 0}

    # 1) Upcoming (active subs, period_end in ~3 days)
    target_low = (now + timedelta(days=REMINDER_UPCOMING_DAYS)).isoformat()
    target_high = (now + timedelta(days=REMINDER_UPCOMING_DAYS + 1)).isoformat()
    async for sub in db.subscriptions.find(
        {
            "status": "active",
            "current_period_end": {"$gte": target_low, "$lt": target_high},
            "reminder_upcoming_at": {"$exists": False},
        },
        {"_id": 0},
    ):
        if await _send_dunning_email("upcoming", sub["company_id"], None, sub):
            await db.subscriptions.update_one(
                {"company_id": sub["company_id"]},
                {"$set": {"reminder_upcoming_at": now.isoformat()}},
            )
            counts["upcoming"] += 1

    # 2) Due (pending invoice, no due reminder yet)
    async for inv in db.invoices.find(
        {"status": "pending", "reminder_due_at": {"$exists": False}},
        {"_id": 0},
    ):
        sub = await db.subscriptions.find_one({"company_id": inv["company_id"]}, {"_id": 0}) or {}
        if await _send_dunning_email("due", inv["company_id"], inv, sub):
            await db.invoices.update_one(
                {"invoice_id": inv["invoice_id"]},
                {"$set": {"reminder_due_at": now.isoformat()}},
            )
            counts["due"] += 1

    # 3) Final (past_due_since >= GRACE_DAYS-1, not yet sent)
    final_cutoff = (now - timedelta(days=GRACE_DAYS - 1)).isoformat()
    async for sub in db.subscriptions.find(
        {
            "status": "past_due",
            "past_due_since": {"$lt": final_cutoff},
            "reminder_final_at": {"$exists": False},
        },
        {"_id": 0},
    ):
        inv = await db.invoices.find_one(
            {"company_id": sub["company_id"], "status": "pending"},
            {"_id": 0},
            sort=[("created_at", -1)],
        )
        if await _send_dunning_email("final", sub["company_id"], inv, sub):
            await db.subscriptions.update_one(
                {"company_id": sub["company_id"]},
                {"$set": {"reminder_final_at": now.isoformat()}},
            )
            counts["final"] += 1

    if any(counts.values()):
        logger.info(f"billing reminders sent: {counts}")
    return counts


async def run_billing_cycle() -> dict:
    """Run all daily billing tasks. Safe to call any time.

    Order matters: reminders must run BEFORE suspension so that the final
    warning email can be sent on the day BEFORE suspension kicks in.
    """
    created = await generate_pending_invoices_for_overdue_subs()
    reminders = await send_billing_reminders()
    suspended = await suspend_overdue_subscriptions()
    return {
        "invoices_created": created,
        "subscriptions_suspended": suspended,
        "reminders_sent": reminders,
    }


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
        "is_blocked": sub.get("status") in ("suspended", "past_due"),
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


class SetupAutoRenewalRequest(BaseModel):
    invoice_id: str
    origin_url: str
    authorized_recurring: bool


@router.post("/setup-auto-renewal")
async def setup_auto_renewal(data: SetupAutoRenewalRequest, current_user: dict = Depends(get_current_user)):
    """Create a Stripe Checkout Session in SUBSCRIPTION mode to pay the pending
    invoice AND enroll the company in automatic monthly recurring charges.

    Requires explicit consent via `authorized_recurring: true` (proof stored in
    payment_transactions and in the subscription record for audit).
    """
    if not data.authorized_recurring:
        raise HTTPException(
            status_code=400,
            detail="Debes autorizar los cargos periódicos para activar la renovación automática.",
        )

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

    currency = (invoice.get("currency") or "usd").lower()
    plan_id = invoice.get("plan_id") or "fortexarh_pro"
    plan_name = invoice.get("plan_name") or plan_id

    host_url = data.origin_url.rstrip("/")
    success_url = f"{host_url}/subscriptions?session_id={{CHECKOUT_SESSION_ID}}&status=success&auto_renew=1"
    cancel_url = f"{host_url}/billing-required?status=cancelled"

    # Ensure a Stripe customer exists for this company (create-or-reuse)
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0, "stripe_customer_id": 1},
    )
    stripe_customer_id = subscription.get("stripe_customer_id") if subscription else None
    if not stripe_customer_id:
        try:
            company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "company_name": 1, "name": 1})
            customer = stripe.Customer.create(
                name=(company or {}).get("company_name") or (company or {}).get("name") or "FortexaRH Client",
                email=current_user.get("email"),
                metadata={"company_id": company_id},
            )
            stripe_customer_id = customer.id
            await db.subscriptions.update_one(
                {"company_id": company_id},
                {"$set": {"stripe_customer_id": stripe_customer_id}},
                upsert=True,
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Stripe create customer error: {e}")
            raise HTTPException(status_code=500, detail="No se pudo crear el cliente Stripe") from e

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "unit_amount": int(round(amount * 100)),
                    "recurring": {"interval": "month"},
                    "product_data": {
                        "name": f"{plan_name} — Suscripción mensual",
                    },
                },
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "company_id": company_id,
                "user_id": current_user.get("user_id") or "",
                "plan_id": plan_id,
                "plan_name": plan_name,
                "employee_count": str(invoice.get("employee_count", 0)),
                "invoice_id": invoice.get("invoice_id"),
                "flow": "auto_renewal_setup",
                "settle_pending_invoice": "1",
                "authorized_recurring": "1",
            },
            subscription_data={
                "metadata": {
                    "company_id": company_id,
                    "plan_id": plan_id,
                    "plan_name": plan_name,
                    "authorized_recurring": "1",
                },
            },
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Stripe setup-auto-renewal error: {e}")
        raise HTTPException(status_code=500, detail="No se pudo crear la sesión de pago") from e

    now_iso = _now().isoformat()
    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "session_id": session.id,
        "company_id": company_id,
        "user_id": current_user.get("user_id"),
        "plan_id": plan_id,
        "plan_name": plan_name,
        "employee_count": invoice.get("employee_count"),
        "amount": amount,
        "currency": invoice.get("currency", "USD"),
        "payment_status": "initiated",
        "invoice_id": invoice.get("invoice_id"),
        "flow": "auto_renewal_setup",
        "authorized_recurring": True,
        "authorized_at": now_iso,
        "authorized_by_user_id": current_user.get("user_id"),
        "created_at": now_iso,
    })

    # Persist consent audit record on the subscription document
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": {
            "auto_renewal_consent": True,
            "auto_renewal_consent_at": now_iso,
            "auto_renewal_consent_by_user_id": current_user.get("user_id"),
            "auto_renewal_consent_amount": amount,
            "auto_renewal_consent_currency": invoice.get("currency", "USD"),
        }},
        upsert=True,
    )

    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/cleanup-abandoned-transactions")
async def cleanup_abandoned_transactions(current_user: dict = Depends(get_current_user)):
    """Mark payment_transactions still `initiated` after 24h as `abandoned`.
    Callable by any authenticated user for their own company; super_admin can
    call it globally via /billing/internal/run.
    """
    company_id = current_user.get("company_id")
    cutoff = (_now() - timedelta(hours=24)).isoformat()
    result = await db.payment_transactions.update_many(
        {
            "company_id": company_id,
            "payment_status": "initiated",
            "created_at": {"$lt": cutoff},
        },
        {"$set": {"payment_status": "abandoned", "abandoned_at": _now().isoformat()}},
    )
    return {"abandoned_count": result.modified_count}


class CustomerPortalRequest(BaseModel):
    return_url: str


@router.post("/customer-portal")
async def create_customer_portal_session(
    data: CustomerPortalRequest, current_user: dict = Depends(get_current_user)
):
    """Create a Stripe Customer Portal session so the user can update card,
    view invoices, or cancel their subscription from Stripe's hosted UI."""
    company_id = current_user.get("company_id")
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0, "stripe_customer_id": 1},
    )
    if not subscription or not subscription.get("stripe_customer_id"):
        raise HTTPException(
            status_code=400,
            detail="No hay método de pago guardado todavía. Activa la renovación automática primero.",
        )

    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe no configurado")
    stripe.api_key = api_key

    try:
        session = stripe.billing_portal.Session.create(
            customer=subscription["stripe_customer_id"],
            return_url=data.return_url,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Stripe billing_portal error: {e}")
        raise HTTPException(status_code=500, detail="No se pudo abrir el portal de Stripe") from e

    return {"portal_url": session.url}


@router.get("/renewal-history")
async def get_renewal_history(current_user: dict = Depends(get_current_user)):
    """Return the last 24 paid renewals (auto-renewal + manual) for the company."""
    company_id = current_user.get("company_id")
    invoices = await db.invoices.find(
        {"company_id": company_id, "status": "paid"},
        {
            "_id": 0,
            "invoice_id": 1,
            "invoice_number": 1,
            "plan_name": 1,
            "total": 1,
            "currency": 1,
            "period_start_iso": 1,
            "period_end_iso": 1,
            "paid_at": 1,
            "paid_at_iso": 1,
            "source": 1,
            "stripe_invoice_id": 1,
        },
    ).sort("paid_at_iso", -1).limit(24).to_list(24)

    return {"items": invoices, "count": len(invoices)}


@router.post("/internal/run")
async def manual_run_billing(request: Request):
    """Manual trigger of the daily billing cycle. Requires the
    `X-Internal-Token` header to match INTERNAL_CRON_TOKEN (super_admin only)."""
    expected = os.environ.get("INTERNAL_CRON_TOKEN", "")
    if not expected or request.headers.get("x-internal-token") != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await run_billing_cycle()
    return {"ok": True, **result}
