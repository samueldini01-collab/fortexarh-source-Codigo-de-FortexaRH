"""
Abandoned Cart Recovery
-----------------------
Tracks visitors who start the /checkout flow but never complete payment.
An APScheduler cron (started from server.py) scans hourly and sends a
Resend-powered recovery email with a link back to the checkout.

Public endpoints (no auth):
  - POST /api/public/abandoned-carts            → capture/update a cart
  - GET  /api/public/abandoned-carts/{cart_id}  → retrieve for "Return to checkout"

Super-admin endpoints (auth):
  - GET  /api/super-admin/abandoned-carts/stats → aggregated metrics
  - GET  /api/super-admin/abandoned-carts       → list with filters
  - POST /api/super-admin/abandoned-carts/{cart_id}/resend → force resend
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from config import db, SUBSCRIPTION_PLANS
from routes.super_admin import get_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Abandoned Carts"])

RECOVERY_DELAY_HOURS = 1
RECOVERY_WINDOW_HOURS = 72  # Don't send recovery beyond this age


# ===================== MODELS =====================

class AbandonedCartIn(BaseModel):
    email: EmailStr
    plan_id: str
    employee_count: int = Field(default=1, ge=1, le=10000)
    origin_url: str
    country: Optional[str] = None
    language: Optional[str] = "es"


# ===================== HELPERS =====================

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _compute_amount(plan_id: str, employee_count: int) -> float:
    plan = SUBSCRIPTION_PLANS.get(plan_id) or {}
    base = float(plan.get("base_price", 0))
    per_emp = float(plan.get("price_per_employee", 0))
    return round(base + per_emp * max(1, int(employee_count)), 2)


def _sanitize(doc: dict) -> dict:
    """Strip BSON _id before returning to client."""
    if not doc:
        return doc
    doc.pop("_id", None)
    # Convert datetime fields to ISO strings for JSON serialization
    for k in ("created_at", "updated_at", "recovery_email_sent_at", "recovered_at"):
        v = doc.get(k)
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


# ===================== PUBLIC ENDPOINTS =====================

@router.post("/public/abandoned-carts")
async def capture_abandoned_cart(payload: AbandonedCartIn):
    """Create or refresh an abandoned-cart record.

    The email + plan_id combination is used as a natural key so visitors who
    come back and update their cart don't create duplicates.
    """
    plan = SUBSCRIPTION_PLANS.get(payload.plan_id)
    if not plan or payload.plan_id == "trial":
        raise HTTPException(status_code=400, detail="Plan inválido")

    amount = _compute_amount(payload.plan_id, payload.employee_count)
    now = _now()

    existing = await db.abandoned_carts.find_one(
        {"email": payload.email.lower(), "plan_id": payload.plan_id, "recovered_at": None}
    )

    if existing:
        await db.abandoned_carts.update_one(
            {"cart_id": existing["cart_id"]},
            {"$set": {
                "employee_count": payload.employee_count,
                "amount": amount,
                "origin_url": payload.origin_url,
                "country": payload.country,
                "language": payload.language,
                "updated_at": now,
            }},
        )
        return {"cart_id": existing["cart_id"], "reused": True}

    cart_id = f"cart_{uuid.uuid4().hex[:16]}"
    await db.abandoned_carts.insert_one({
        "cart_id": cart_id,
        "email": payload.email.lower(),
        "plan_id": payload.plan_id,
        "plan_name": plan.get("name", payload.plan_id),
        "employee_count": payload.employee_count,
        "amount": amount,
        "currency": "usd",
        "origin_url": payload.origin_url,
        "country": payload.country,
        "language": payload.language or "es",
        "created_at": now,
        "updated_at": now,
        "recovery_email_sent_at": None,
        "recovered_at": None,
        "stripe_session_id": None,
    })
    return {"cart_id": cart_id, "reused": False}


@router.get("/public/abandoned-carts/{cart_id}")
async def get_abandoned_cart(cart_id: str):
    doc = await db.abandoned_carts.find_one({"cart_id": cart_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    return _sanitize(doc)


# ===================== INTERNAL: mark recovered =====================

async def mark_cart_recovered(email: Optional[str], plan_id: str, session_id: str) -> bool:
    """Called by the Stripe success flow. Updates the matching cart (latest
    one for that email+plan) as recovered."""
    if not email:
        return False
    result = await db.abandoned_carts.update_one(
        {
            "email": email.lower(),
            "plan_id": plan_id,
            "recovered_at": None,
        },
        {"$set": {
            "recovered_at": _now(),
            "stripe_session_id": session_id,
        }},
        upsert=False,
    )
    return result.modified_count > 0


# ===================== SUPER-ADMIN ENDPOINTS =====================


@router.get("/super-admin/abandoned-carts/stats")
async def abandoned_carts_stats(admin=Depends(get_super_admin)):
    now = _now()
    since_30d = now - timedelta(days=30)

    total = await db.abandoned_carts.count_documents({"created_at": {"$gte": since_30d}})
    recovered = await db.abandoned_carts.count_documents({
        "created_at": {"$gte": since_30d},
        "recovered_at": {"$ne": None},
    })
    emailed = await db.abandoned_carts.count_documents({
        "created_at": {"$gte": since_30d},
        "recovery_email_sent_at": {"$ne": None},
    })

    pipeline = [
        {"$match": {
            "created_at": {"$gte": since_30d},
            "recovered_at": {"$ne": None},
        }},
        {"$group": {"_id": None, "sum": {"$sum": "$amount"}}},
    ]
    rev_cursor = db.abandoned_carts.aggregate(pipeline)
    rev_docs = await rev_cursor.to_list(length=1)
    recovered_revenue = float(rev_docs[0]["sum"]) if rev_docs else 0.0

    pipeline_abandoned = [
        {"$match": {
            "created_at": {"$gte": since_30d},
            "recovered_at": None,
        }},
        {"$group": {"_id": None, "sum": {"$sum": "$amount"}}},
    ]
    ab_cursor = db.abandoned_carts.aggregate(pipeline_abandoned)
    ab_docs = await ab_cursor.to_list(length=1)
    abandoned_revenue = float(ab_docs[0]["sum"]) if ab_docs else 0.0

    recovery_rate = round((recovered / total) * 100, 1) if total else 0.0

    return {
        "window_days": 30,
        "total_carts": total,
        "emails_sent": emailed,
        "recovered": recovered,
        "recovery_rate_pct": recovery_rate,
        "recovered_revenue_usd": round(recovered_revenue, 2),
        "abandoned_revenue_usd": round(abandoned_revenue, 2),
    }


@router.get("/super-admin/abandoned-carts")
async def list_abandoned_carts(
    status: str = Query("all", pattern="^(all|open|recovered|emailed)$"),
    limit: int = Query(100, ge=1, le=500),
    admin=Depends(get_super_admin),
):
    query = {}
    if status == "open":
        query["recovered_at"] = None
    elif status == "recovered":
        query["recovered_at"] = {"$ne": None}
    elif status == "emailed":
        query["recovery_email_sent_at"] = {"$ne": None}
        query["recovered_at"] = None
    cursor = db.abandoned_carts.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_sanitize(d) for d in docs]


@router.post("/super-admin/abandoned-carts/{cart_id}/resend")
async def resend_recovery_email(cart_id: str, admin=Depends(get_super_admin)):
    doc = await db.abandoned_carts.find_one({"cart_id": cart_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    if doc.get("recovered_at"):
        raise HTTPException(status_code=400, detail="Ya fue recuperado")
    sent = await _send_recovery_email(doc)
    if sent:
        await db.abandoned_carts.update_one(
            {"cart_id": cart_id},
            {"$set": {"recovery_email_sent_at": _now()}},
        )
        return {"sent": True}
    raise HTTPException(status_code=500, detail="No se pudo enviar el email")


# ===================== EMAIL SENDER =====================

EMAIL_SUBJECTS = {
    "es": "Olvidaste algo en FortexaRH — tu suscripción espera",
    "en": "You left something behind at FortexaRH — your subscription is waiting",
    "fr": "Vous avez oublié quelque chose chez FortexaRH — votre abonnement vous attend",
    "pt": "Você deixou algo para trás no FortexaRH — sua assinatura aguarda",
}

EMAIL_BODY = {
    "es": {
        "hello": "Hola",
        "intro": "Te detuviste al configurar tu suscripción {plan_name}. ¡Todavía puedes completarla!",
        "summary": "Resumen del plan",
        "employees": "{n} empleados",
        "total": "Total mensual",
        "cta": "Completar suscripción",
        "closing": "Si ya no te interesa, puedes ignorar este mensaje.",
    },
    "en": {
        "hello": "Hello",
        "intro": "You paused while setting up your {plan_name} subscription. You can still finish it!",
        "summary": "Plan summary",
        "employees": "{n} employees",
        "total": "Monthly total",
        "cta": "Complete subscription",
        "closing": "If you changed your mind, feel free to ignore this message.",
    },
    "fr": {
        "hello": "Bonjour",
        "intro": "Vous vous êtes arrêté lors de la configuration de votre abonnement {plan_name}. Vous pouvez toujours la terminer !",
        "summary": "Résumé du plan",
        "employees": "{n} employés",
        "total": "Total mensuel",
        "cta": "Finaliser l'abonnement",
        "closing": "Si vous avez changé d'avis, ignorez simplement ce message.",
    },
    "pt": {
        "hello": "Olá",
        "intro": "Você pausou ao configurar sua assinatura {plan_name}. Ainda pode finalizar!",
        "summary": "Resumo do plano",
        "employees": "{n} empregados",
        "total": "Total mensal",
        "cta": "Concluir assinatura",
        "closing": "Se mudou de ideia, pode ignorar esta mensagem.",
    },
}


async def _send_recovery_email(cart: dict) -> bool:
    """Best-effort send via Resend. Returns True on success."""
    try:
        import resend  # local import so missing package doesn't block server boot
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Resend not installed: {exc}")
        return False

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY not configured — skipping recovery email")
        return False
    resend.api_key = api_key

    lang = (cart.get("language") or "es").lower()[:2]
    if lang not in EMAIL_BODY:
        lang = "es"
    words = EMAIL_BODY[lang]
    subject = EMAIL_SUBJECTS.get(lang, EMAIL_SUBJECTS["es"])

    origin = cart.get("origin_url") or "https://fortexarh.com"
    recovery_url = f"{origin.rstrip('/')}/checkout?plan={cart['plan_id']}&cart={cart['cart_id']}"

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#0f172a;">
      <h2 style="color:#059669;margin-bottom:8px;">FortexaRH</h2>
      <h3 style="margin-top:0;">{words['hello']} 👋</h3>
      <p style="font-size:15px;line-height:1.6;">{words['intro'].format(plan_name=cart.get('plan_name', cart['plan_id']))}</p>
      <div style="background:#f1f5f9;border-radius:10px;padding:16px;margin:16px 0;">
        <p style="margin:0;font-weight:bold;color:#334155;">{words['summary']}</p>
        <p style="margin:4px 0 0;">{cart.get('plan_name', cart['plan_id'])} — {words['employees'].format(n=cart.get('employee_count', 1))}</p>
        <p style="margin:4px 0 0;color:#059669;font-size:18px;font-weight:bold;">{words['total']}: ${cart.get('amount', 0):.2f} USD</p>
      </div>
      <div style="text-align:center;margin:24px 0;">
        <a href="{recovery_url}" style="background:#059669;color:#ffffff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">{words['cta']}</a>
      </div>
      <p style="font-size:12px;color:#64748b;">{words['closing']}</p>
    </div>
    """

    sender = os.environ.get("SENDER_EMAIL", "FortexaRH <onboarding@resend.dev>")

    try:
        params = {
            "from": sender,
            "to": [cart["email"]],
            "subject": subject,
            "html": html,
        }
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Recovery email send failed: {exc}")
        return False


# ===================== CRON WORKER =====================

async def run_abandoned_cart_recovery_job() -> dict:
    """Find carts older than RECOVERY_DELAY_HOURS that haven't been emailed
    or recovered yet, and send a single recovery email each."""
    now = _now()
    cutoff_old = now - timedelta(hours=RECOVERY_DELAY_HOURS)
    cutoff_window = now - timedelta(hours=RECOVERY_WINDOW_HOURS)

    query = {
        "created_at": {"$lte": cutoff_old, "$gte": cutoff_window},
        "recovery_email_sent_at": None,
        "recovered_at": None,
    }

    cursor = db.abandoned_carts.find(query).limit(200)
    docs = await cursor.to_list(length=200)
    sent = 0
    failed = 0
    for cart in docs:
        ok = await _send_recovery_email(cart)
        if ok:
            await db.abandoned_carts.update_one(
                {"cart_id": cart["cart_id"]},
                {"$set": {"recovery_email_sent_at": _now()}},
            )
            sent += 1
        else:
            failed += 1

    logger.info(f"Abandoned-cart recovery cron: scanned={len(docs)} sent={sent} failed={failed}")
    return {"scanned": len(docs), "sent": sent, "failed": failed}


async def create_abandoned_cart_indexes():
    try:
        await db.abandoned_carts.create_index([("cart_id", 1)], unique=True)
        await db.abandoned_carts.create_index([("email", 1), ("plan_id", 1)])
        await db.abandoned_carts.create_index([("created_at", -1)])
        await db.abandoned_carts.create_index([("recovery_email_sent_at", 1), ("recovered_at", 1)])
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"abandoned_carts index warning: {exc}")
