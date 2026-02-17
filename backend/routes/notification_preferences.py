"""
User Notification Preferences - FortexaRH
Per-user, per-event, per-channel notification configuration with quiet hours and digest.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import os
import uuid

router = APIRouter(prefix="/notification-preferences", tags=["Notification Preferences"])
from config import db
from utils.auth import get_current_user
from services.push_service import send_push_to_user

# All notification event types with metadata
NOTIFICATION_EVENTS = {
    "payroll_approval": {
        "category": "payroll",
        "label": "Nómina pendiente de aprobación",
        "label_en": "Payroll pending approval",
        "default": {"in_app": True, "email": True, "push": True},
        "roles": ["admin", "hr_manager", "finance_manager"]
    },
    "payroll_approved": {
        "category": "payroll",
        "label": "Nómina aprobada",
        "label_en": "Payroll approved",
        "default": {"in_app": True, "email": False, "push": False},
        "roles": ["admin", "hr_manager"]
    },
    "payroll_rejected": {
        "category": "payroll",
        "label": "Nómina rechazada",
        "label_en": "Payroll rejected",
        "default": {"in_app": True, "email": True, "push": True},
        "roles": ["admin", "hr_manager"]
    },
    "payroll_available": {
        "category": "payroll",
        "label": "Recibo de nómina disponible",
        "label_en": "Payslip available",
        "default": {"in_app": True, "email": False, "push": True},
        "roles": ["all"]
    },
    "vacation_request": {
        "category": "vacations",
        "label": "Nueva solicitud de vacaciones",
        "label_en": "New vacation request",
        "default": {"in_app": True, "email": True, "push": True},
        "roles": ["admin", "hr_manager"]
    },
    "vacation_approved": {
        "category": "vacations",
        "label": "Vacaciones aprobadas",
        "label_en": "Vacation approved",
        "default": {"in_app": True, "email": True, "push": True},
        "roles": ["employee", "all"]
    },
    "vacation_rejected": {
        "category": "vacations",
        "label": "Vacaciones rechazadas",
        "label_en": "Vacation rejected",
        "default": {"in_app": True, "email": True, "push": True},
        "roles": ["employee", "all"]
    },
    "evaluation_scheduled": {
        "category": "evaluations",
        "label": "Evaluación programada",
        "label_en": "Evaluation scheduled",
        "default": {"in_app": True, "email": True, "push": False},
        "roles": ["employee", "all"]
    },
    "evaluation_completed": {
        "category": "evaluations",
        "label": "Evaluación completada",
        "label_en": "Evaluation completed",
        "default": {"in_app": True, "email": False, "push": False},
        "roles": ["admin", "hr_manager"]
    },
    "contract_expiry": {
        "category": "contracts",
        "label": "Contrato próximo a vencer",
        "label_en": "Contract expiring soon",
        "default": {"in_app": True, "email": True, "push": True},
        "roles": ["admin", "hr_manager"]
    },
    "document_expiry": {
        "category": "contracts",
        "label": "Documento por vencer",
        "label_en": "Document expiring soon",
        "default": {"in_app": True, "email": False, "push": False},
        "roles": ["admin", "hr_manager"]
    },
    "new_employee": {
        "category": "employees",
        "label": "Nuevo empleado agregado",
        "label_en": "New employee added",
        "default": {"in_app": True, "email": False, "push": False},
        "roles": ["admin", "hr_manager"]
    },
    "employee_birthday": {
        "category": "employees",
        "label": "Cumpleaños de empleado",
        "label_en": "Employee birthday",
        "default": {"in_app": True, "email": True, "push": False},
        "roles": ["admin", "hr_manager"]
    },
    "attendance_check_in": {
        "category": "attendance",
        "label": "Recordatorio de entrada",
        "label_en": "Check-in reminder",
        "default": {"in_app": True, "email": False, "push": True},
        "roles": ["employee", "all"]
    },
    "attendance_check_out": {
        "category": "attendance",
        "label": "Recordatorio de salida",
        "label_en": "Check-out reminder",
        "default": {"in_app": True, "email": False, "push": True},
        "roles": ["employee", "all"]
    },
    "partner_new_client": {
        "category": "partner",
        "label": "Nuevo cliente referido",
        "label_en": "New referred client",
        "default": {"in_app": True, "email": True, "push": True},
        "roles": ["partner_admin"]
    },
    "partner_commission": {
        "category": "partner",
        "label": "Comisión recibida",
        "label_en": "Commission received",
        "default": {"in_app": True, "email": True, "push": False},
        "roles": ["partner_admin"]
    },
    "partner_payout": {
        "category": "partner",
        "label": "Retiro procesado",
        "label_en": "Payout processed",
        "default": {"in_app": True, "email": True, "push": True},
        "roles": ["partner_admin"]
    },
    "system_alert": {
        "category": "system",
        "label": "Alerta del sistema",
        "label_en": "System alert",
        "default": {"in_app": True, "email": False, "push": False},
        "roles": ["admin"]
    },
    "subscription_change": {
        "category": "system",
        "label": "Cambio en suscripción",
        "label_en": "Subscription change",
        "default": {"in_app": True, "email": True, "push": False},
        "roles": ["admin"]
    }
}

NOTIFICATION_CATEGORIES = {
    "payroll": {"label": "Nómina", "label_en": "Payroll", "icon": "DollarSign"},
    "vacations": {"label": "Vacaciones", "label_en": "Vacations", "icon": "Calendar"},
    "evaluations": {"label": "Evaluaciones", "label_en": "Evaluations", "icon": "Target"},
    "contracts": {"label": "Contratos", "label_en": "Contracts", "icon": "FileText"},
    "employees": {"label": "Empleados", "label_en": "Employees", "icon": "Users"},
    "attendance": {"label": "Asistencia", "label_en": "Attendance", "icon": "Clock"},
    "partner": {"label": "Partner", "label_en": "Partner", "icon": "Briefcase"},
    "system": {"label": "Sistema", "label_en": "System", "icon": "Settings"}
}


def _build_default_prefs(user_role: str) -> dict:
    """Build default preferences based on user role."""
    events = {}
    for event_key, event_meta in NOTIFICATION_EVENTS.items():
        applicable_roles = event_meta["roles"]
        if "all" in applicable_roles or user_role in applicable_roles:
            events[event_key] = event_meta["default"].copy()
    return events


@router.get("/events")
async def get_notification_event_types(current_user: dict = Depends(get_current_user)):
    """Get all available notification event types with categories."""
    user_role = current_user.get("role", "employee")
    relevant = {}
    for event_key, event_meta in NOTIFICATION_EVENTS.items():
        applicable = event_meta["roles"]
        if "all" in applicable or user_role in applicable:
            relevant[event_key] = {
                "category": event_meta["category"],
                "label": event_meta["label"],
                "label_en": event_meta["label_en"],
                "default": event_meta["default"]
            }
    return {
        "events": relevant,
        "categories": NOTIFICATION_CATEGORIES
    }


@router.get("")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get notification preferences for the current user."""
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "employee")

    prefs = await db.user_notification_preferences.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )

    if not prefs:
        default_events = _build_default_prefs(user_role)
        return {
            "user_id": user_id,
            "events": default_events,
            "quiet_hours": {
                "enabled": False,
                "start_time": "20:00",
                "end_time": "08:00",
                "timezone": "America/Santo_Domingo",
                "skip_weekends": True
            },
            "digest": {
                "enabled": False,
                "frequency": "daily",
                "day_of_week": 1,
                "send_time": "08:00"
            }
        }

    return prefs


@router.put("")
async def update_user_preferences(
    prefs: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update notification preferences for the current user."""
    user_id = current_user.get("user_id")

    update_data = {
        "user_id": user_id,
        "company_id": current_user.get("company_id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    if "events" in prefs:
        update_data["events"] = prefs["events"]
    if "quiet_hours" in prefs:
        update_data["quiet_hours"] = prefs["quiet_hours"]
    if "digest" in prefs:
        update_data["digest"] = prefs["digest"]

    await db.user_notification_preferences.update_one(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True
    )

    return {"message": "Preferencias actualizadas correctamente"}


# ============== PUSH SUBSCRIPTION ==============

@router.post("/push/subscribe")
async def subscribe_push(
    subscription: dict,
    current_user: dict = Depends(get_current_user)
):
    """Register a push notification subscription for the current user."""
    user_id = current_user.get("user_id")

    sub_data = {
        "user_id": user_id,
        "company_id": current_user.get("company_id"),
        "endpoint": subscription.get("endpoint"),
        "keys": subscription.get("keys", {}),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.push_subscriptions.update_one(
        {"user_id": user_id, "endpoint": subscription.get("endpoint")},
        {"$set": sub_data},
        upsert=True
    )

    return {"message": "Suscripción push registrada"}


@router.post("/push/unsubscribe")
async def unsubscribe_push(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Remove a push subscription."""
    user_id = current_user.get("user_id")
    endpoint = data.get("endpoint")

    await db.push_subscriptions.delete_one(
        {"user_id": user_id, "endpoint": endpoint}
    )

    return {"message": "Suscripción push eliminada"}


@router.get("/push/status")
async def get_push_status(current_user: dict = Depends(get_current_user)):
    """Check if user has active push subscriptions."""
    user_id = current_user.get("user_id")

    count = await db.push_subscriptions.count_documents({"user_id": user_id})
    return {"subscribed": count > 0, "subscription_count": count}


# ============== NOTIFICATION HELPER ==============

async def should_notify_user(user_id: str, event_type: str, channel: str = "in_app") -> bool:
    """Check if a user should receive a notification for a given event and channel."""
    prefs = await db.user_notification_preferences.find_one(
        {"user_id": user_id},
        {"_id": 0, "events": 1, "quiet_hours": 1}
    )

    if not prefs:
        event_meta = NOTIFICATION_EVENTS.get(event_type)
        if event_meta:
            return event_meta["default"].get(channel, False)
        return channel == "in_app"

    event_prefs = prefs.get("events", {}).get(event_type)
    if event_prefs is None:
        event_meta = NOTIFICATION_EVENTS.get(event_type)
        if event_meta:
            return event_meta["default"].get(channel, False)
        return channel == "in_app"

    if not event_prefs.get(channel, False):
        return False

    # Check quiet hours for push/email (in_app always goes through)
    if channel in ("push", "email"):
        quiet = prefs.get("quiet_hours", {})
        if quiet.get("enabled"):
            from datetime import datetime as dt
            try:
                import pytz
                tz = pytz.timezone(quiet.get("timezone", "America/Santo_Domingo"))
                now_local = datetime.now(timezone.utc).astimezone(tz)
                start = dt.strptime(quiet["start_time"], "%H:%M").time()
                end = dt.strptime(quiet["end_time"], "%H:%M").time()

                if quiet.get("skip_weekends") and now_local.weekday() >= 5:
                    return False

                current_time = now_local.time()
                if start > end:
                    if current_time >= start or current_time < end:
                        return False
                else:
                    if start <= current_time < end:
                        return False
            except Exception:
                pass

    return True
