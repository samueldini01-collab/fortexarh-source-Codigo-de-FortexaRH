"""
Subscription Routes for FortexaRH
Module for managing subscriptions, cancellation, retention, and billing
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging
import os
import stripe
import resend

router = APIRouter(prefix="/subscription", tags=["Subscriptions"])

from config import db
from utils.auth import get_current_user
from config import SUBSCRIPTION_PLANS, FEATURE_ACCESS, ADDITIONAL_USER_PRICE
logger = logging.getLogger(__name__)


# ===================== PYDANTIC MODELS =====================
from models.finance import (
    CancellationSurveyData, RetentionOfferResponse,
    SubscriptionCreate, SubscriptionUpdate
)


# ===================== ROUTER INITIALIZATION =====================


def _get_stripe_key():
    """Get Stripe API key from environment"""
    key = os.environ.get('STRIPE_API_KEY')
    if not key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    return key


# ===================== SUBSCRIPTION ENDPOINTS =====================

@router.get("")
async def get_company_subscription(request: Request):
    """Get the current company subscription"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not subscription:
        # Create default trial subscription (5 days, 1 employee max)
        trial_ends_at = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        subscription = {
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "company_id": company_id,
            "plan_id": "trial",
            "plan_name": "Prueba Gratuita",
            "status": "trial",
            "employee_count": 1,
            "additional_users": 0,
            "billing_cycle": "monthly",
            "base_price": 0.0,
            "employee_price": 0.0,
            "total_monthly": 0.0,
            "trial_ends_at": trial_ends_at,
            "current_period_start": datetime.now(timezone.utc).isoformat(),
            "current_period_end": trial_ends_at,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscriptions.insert_one(subscription)
    
    # Get plan details
    plan = SUBSCRIPTION_PLANS.get(subscription.get("plan_id", "trial"), SUBSCRIPTION_PLANS.get("trial", {}))
    subscription["plan_details"] = plan
    
    # Count current employees and users
    employee_count = await db.employees.count_documents({"company_id": company_id, "status": "active"})
    user_count = await db.users.count_documents({"company_id": company_id})
    
    subscription["current_employees"] = employee_count
    subscription["current_users"] = user_count
    subscription["max_employees"] = plan.get("max_employees", 1)
    subscription["included_users"] = plan.get("included_users", 1)
    
    # Check if trial has expired
    if subscription.get("status") == "trial" and subscription.get("trial_ends_at"):
        trial_ends = datetime.fromisoformat(subscription["trial_ends_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > trial_ends:
            subscription["status"] = "expired"
            await db.subscriptions.update_one(
                {"company_id": company_id},
                {"$set": {"status": "expired"}}
            )
    
    # Calculate days remaining for trial
    if subscription.get("trial_ends_at"):
        trial_ends = datetime.fromisoformat(subscription["trial_ends_at"].replace("Z", "+00:00"))
        days_remaining = (trial_ends - datetime.now(timezone.utc)).days
        subscription["trial_days_remaining"] = max(0, days_remaining)
    
    # Get feature access for this plan
    if FEATURE_ACCESS:
        subscription["feature_access"] = FEATURE_ACCESS.get(subscription.get("plan_id", "trial"), FEATURE_ACCESS.get("trial", {}))
    
    return subscription


@router.post("")
async def create_subscription(data: SubscriptionCreate, request: Request):
    """Create or update subscription"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    plan = SUBSCRIPTION_PLANS.get(data.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Plan no válido")
    
    # Check employee limit
    if plan["max_employees"] > 0 and data.employee_count > plan["max_employees"]:
        raise HTTPException(status_code=400, detail=f"El plan {plan['name']} permite máximo {plan['max_employees']} empleados")
    
    # Calculate total
    base = plan["base_price"]
    employee_cost = data.employee_count * plan["price_per_employee"]
    additional_users_cost = data.additional_users * ADDITIONAL_USER_PRICE
    total_monthly = base + employee_cost + additional_users_cost
    
    subscription = {
        "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "plan_id": data.plan_id,
        "plan_name": plan["name"],
        "status": "active",
        "employee_count": data.employee_count,
        "additional_users": data.additional_users,
        "billing_cycle": data.billing_cycle,
        "base_price": base,
        "employee_price": plan["price_per_employee"],
        "additional_users_cost": additional_users_cost,
        "total_monthly": total_monthly,
        "current_period_start": datetime.now(timezone.utc).isoformat(),
        "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert subscription
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": subscription},
        upsert=True
    )
    
    return {"message": "Suscripción actualizada", "subscription": subscription}


@router.put("")
async def update_subscription(data: SubscriptionUpdate, request: Request):
    """Update subscription (change plan, employees, cancel, renew)"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    subscription = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    
    updates = {}
    
    # Handle actions
    if data.action == "cancel":
        updates["status"] = "cancelled"
        updates["cancelled_at"] = datetime.now(timezone.utc).isoformat()
    elif data.action == "renew":
        updates["status"] = "active"
        updates["current_period_start"] = datetime.now(timezone.utc).isoformat()
        updates["current_period_end"] = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    # Update plan
    if data.plan_id:
        plan = SUBSCRIPTION_PLANS.get(data.plan_id)
        if not plan:
            raise HTTPException(status_code=400, detail="Plan no válido")
        updates["plan_id"] = data.plan_id
        updates["plan_name"] = plan["name"]
        updates["base_price"] = plan["base_price"]
        updates["employee_price"] = plan["price_per_employee"]
    
    # Update employee count
    if data.employee_count is not None:
        current_plan = SUBSCRIPTION_PLANS.get(data.plan_id or subscription["plan_id"])
        if current_plan["max_employees"] > 0 and data.employee_count > current_plan["max_employees"]:
            raise HTTPException(status_code=400, detail=f"El plan permite máximo {current_plan['max_employees']} empleados")
        updates["employee_count"] = data.employee_count
    
    # Update additional users
    if data.additional_users is not None:
        updates["additional_users"] = data.additional_users
        updates["additional_users_cost"] = data.additional_users * ADDITIONAL_USER_PRICE
    
    # Recalculate total
    plan_id = updates.get("plan_id", subscription["plan_id"])
    plan = SUBSCRIPTION_PLANS[plan_id]
    emp_count = updates.get("employee_count", subscription.get("employee_count", 1))
    add_users = updates.get("additional_users", subscription.get("additional_users", 0))
    
    updates["total_monthly"] = plan["base_price"] + (emp_count * plan["price_per_employee"]) + (add_users * ADDITIONAL_USER_PRICE)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": updates}
    )
    
    return {"message": "Suscripción actualizada correctamente"}


@router.get("/check-access")
async def check_subscription_access(request: Request):
    """Check if user has system access based on subscription"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    subscription = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    
    if not subscription:
        return {"has_access": True, "status": "trial", "message": "Período de prueba"}
    
    status = subscription.get("status", "active")
    
    if status == "cancelled" or status == "expired":
        return {
            "has_access": False,
            "status": status,
            "message": "Su suscripción está cancelada o vencida. Por favor renueve para continuar.",
            "redirect_to": "/subscriptions"
        }
    
    # Check if trial expired
    if status == "trial":
        trial_ends = subscription.get("trial_ends_at")
        if trial_ends:
            trial_end_date = datetime.fromisoformat(trial_ends.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > trial_end_date:
                await db.subscriptions.update_one(
                    {"company_id": company_id},
                    {"$set": {"status": "expired"}}
                )
                return {
                    "has_access": False,
                    "status": "expired",
                    "message": "Su período de prueba ha terminado. Por favor seleccione un plan.",
                    "redirect_to": "/subscriptions"
                }
    
    return {"has_access": True, "status": status, "plan": subscription.get("plan_id")}


# ===================== CANCELLATION FLOW =====================

@router.get("/cancellation-info")
async def get_cancellation_info(request: Request):
    """Get information needed for cancellation flow"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No hay suscripción activa")
    
    # Get company info
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1, "employee_count": 1}
    )
    
    plan_id = subscription.get("plan_id", "trial")
    plan = SUBSCRIPTION_PLANS.get(plan_id, {})
    
    # Calculate retention offer (20% discount for 3 months)
    current_monthly = subscription.get("total_monthly", 0)
    discount_percent = 20
    discounted_monthly = current_monthly * (1 - discount_percent / 100)
    savings_3_months = (current_monthly - discounted_monthly) * 3
    
    return {
        "current_plan": {
            "id": plan_id,
            "name": plan.get("name", plan_id),
            "monthly_cost": current_monthly,
            "employee_count": subscription.get("employee_count", 0)
        },
        "subscription_status": subscription.get("status"),
        "subscription_start": subscription.get("created_at"),
        "retention_offer": {
            "discount_percent": discount_percent,
            "duration_months": 3,
            "discounted_monthly": round(discounted_monthly, 2),
            "savings_total": round(savings_3_months, 2),
            "offer_code": f"STAY{discount_percent}"
        },
        "cancellation_reasons": [
            {"id": "too_expensive", "label": "El precio es muy alto"},
            {"id": "not_using", "label": "No estoy usando el sistema"},
            {"id": "missing_features", "label": "Faltan funciones que necesito"},
            {"id": "switching", "label": "Cambio a otro sistema"},
            {"id": "business_closed", "label": "Cierre de negocio"},
            {"id": "temporary", "label": "Pausa temporal"},
            {"id": "other", "label": "Otro motivo"}
        ]
    }


@router.post("/accept-retention-offer")
async def accept_retention_offer(request: Request):
    """Accept the retention offer (20% discount for 3 months)"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_email = current_user.get("email")
    
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No hay suscripción activa")
    
    # Apply 20% discount for 3 months
    current_monthly = subscription.get("total_monthly", 0)
    discount_percent = 20
    discounted_monthly = round(current_monthly * (1 - discount_percent / 100), 2)
    discount_ends_at = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {
            "$set": {
                "retention_discount": {
                    "percent": discount_percent,
                    "original_monthly": current_monthly,
                    "discounted_monthly": discounted_monthly,
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                    "ends_at": discount_ends_at
                },
                "total_monthly": discounted_monthly,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Log retention offer acceptance
    await db.retention_events.insert_one({
        "event_id": f"ret_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "event_type": "offer_accepted",
        "discount_percent": discount_percent,
        "duration_months": 3,
        "original_monthly": current_monthly,
        "new_monthly": discounted_monthly,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send confirmation email
    if user_email:
        try:
            resend.api_key = os.environ.get('RESEND_API_KEY')
            resend.Emails.send({
                "from": os.environ.get('SENDER_EMAIL', 'FortexaRH <onboarding@resend.dev>'),
                "to": [user_email],
                "subject": "¡Gracias por quedarte! Tu descuento está activo",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #1e3a5f;">¡Gracias por quedarte con FortexaRH!</h2>
                    <p>Hemos aplicado un <strong>{discount_percent}% de descuento</strong> a tu suscripción por los próximos 3 meses.</p>
                    <div style="background: #f0f7ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Precio anterior:</strong> ${current_monthly:.2f}/mes</p>
                        <p style="margin: 10px 0 0 0;"><strong>Nuevo precio:</strong> ${discounted_monthly:.2f}/mes</p>
                        <p style="margin: 10px 0 0 0; color: #22c55e;"><strong>Ahorras:</strong> ${(current_monthly - discounted_monthly) * 3:.2f} en 3 meses</p>
                    </div>
                    <p>El descuento se aplicará automáticamente a tus próximas facturas.</p>
                    <p>¡Gracias por confiar en nosotros!</p>
                </div>
                """
            })
        except Exception as e:
            logger.error(f"Error sending retention email: {e}")
    
    return {
        "success": True,
        "message": "Descuento aplicado exitosamente",
        "new_monthly": discounted_monthly,
        "discount_ends_at": discount_ends_at,
        "savings_3_months": round((current_monthly - discounted_monthly) * 3, 2)
    }


@router.post("/cancel")
async def cancel_subscription(survey: CancellationSurveyData, request: Request):
    """Cancel subscription with survey feedback"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    user_email = current_user.get("email")
    user_name = current_user.get("name", "")
    
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No hay suscripción activa")
    
    # Get company info
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1}
    )
    company_name = company.get("name", "") if company else ""
    
    # Try to cancel in Stripe if there's a Stripe subscription
    stripe_sub_id = subscription.get("stripe_subscription_id")
    if stripe_sub_id:
        try:
            stripe.api_key = _get_stripe_key()
            # Cancel at period end (don't cancel immediately)
            stripe.Subscription.modify(
                stripe_sub_id,
                cancel_at_period_end=True
            )
        except Exception as e:
            logger.error(f"Error canceling Stripe subscription: {e}")
    
    # Calculate when access ends (end of current billing period or trial)
    now = datetime.now(timezone.utc)
    if subscription.get("status") == "trial":
        access_ends_at = subscription.get("trial_ends_at", now.isoformat())
    else:
        # End of current month
        next_month = now.replace(day=28) + timedelta(days=4)
        access_ends_at = next_month.replace(day=1).isoformat()
    
    # Update subscription status
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {
            "$set": {
                "status": "canceling",
                "cancel_requested_at": now.isoformat(),
                "cancel_reason": survey.reason,
                "cancel_feedback": survey.feedback,
                "cancel_would_return": survey.would_return,
                "access_ends_at": access_ends_at,
                "updated_at": now.isoformat()
            }
        }
    )
    
    # Save cancellation survey for analytics
    await db.cancellation_surveys.insert_one({
        "survey_id": f"srv_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "company_name": company_name,
        "plan_id": subscription.get("plan_id"),
        "plan_name": SUBSCRIPTION_PLANS.get(subscription.get("plan_id", ""), {}).get("name", ""),
        "monthly_value": subscription.get("total_monthly", 0),
        "reason": survey.reason,
        "feedback": survey.feedback,
        "would_return": survey.would_return,
        "subscription_duration_days": (now - datetime.fromisoformat(subscription.get("created_at", now.isoformat()).replace("Z", "+00:00"))).days if subscription.get("created_at") else 0,
        "created_at": now.isoformat()
    })
    
    # Send cancellation confirmation email
    if user_email:
        try:
            resend.api_key = os.environ.get('RESEND_API_KEY')
            resend.Emails.send({
                "from": os.environ.get('SENDER_EMAIL', 'FortexaRH <onboarding@resend.dev>'),
                "to": [user_email],
                "subject": "Confirmación de cancelación - FortexaRH",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #1e3a5f;">Tu cancelación ha sido procesada</h2>
                    <p>Hola {user_name or 'Usuario'},</p>
                    <p>Lamentamos verte partir. Tu suscripción a FortexaRH ha sido cancelada.</p>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Empresa:</strong> {company_name}</p>
                        <p style="margin: 10px 0 0 0;"><strong>Acceso hasta:</strong> {access_ends_at[:10]}</p>
                    </div>
                    <p>Podrás seguir usando el sistema hasta esa fecha. Después, tus datos se mantendrán guardados por 30 días por si decides volver.</p>
                    <p style="margin-top: 30px;">Si cambias de opinión, puedes reactivar tu suscripción en cualquier momento desde el panel de control.</p>
                    <p>¡Gracias por haber sido parte de FortexaRH!</p>
                </div>
                """
            })
        except Exception as e:
            logger.error(f"Error sending cancellation email: {e}")
    
    return {
        "success": True,
        "message": "Suscripción cancelada",
        "access_ends_at": access_ends_at,
        "can_reactivate": True
    }


@router.post("/reactivate")
async def reactivate_subscription(request: Request):
    """Reactivate a canceled subscription"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No hay suscripción")
    
    if subscription.get("status") not in ["canceling", "canceled"]:
        raise HTTPException(status_code=400, detail="La suscripción no está cancelada")
    
    # Try to reactivate in Stripe
    stripe_sub_id = subscription.get("stripe_subscription_id")
    if stripe_sub_id:
        try:
            stripe.api_key = _get_stripe_key()
            stripe.Subscription.modify(
                stripe_sub_id,
                cancel_at_period_end=False
            )
        except Exception as e:
            logger.error(f"Error reactivating Stripe subscription: {e}")
    
    # Update subscription status
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {
            "$set": {
                "status": "active",
                "cancel_requested_at": None,
                "access_ends_at": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$unset": {
                "cancel_reason": "",
                "cancel_feedback": "",
                "cancel_would_return": ""
            }
        }
    )
    
    return {
        "success": True,
        "message": "Suscripción reactivada exitosamente"
    }
