"""
Notifications Router - FortexaRH
In-app notification system for payroll approvals, vacations, evaluations, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Callable, Optional, List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/notifications", tags=["Notifications"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func: Callable = None


def init_router(database, auth_dependency: Callable):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    type: str  # payroll_approval, vacation_approved, vacation_rejected, evaluation, attendance, system
    priority: str = "normal"  # low, normal, high, urgent
    link: Optional[str] = None
    target_user_id: Optional[str] = None  # If None, sent to all with permission
    target_role: Optional[str] = None  # admin, hr_manager, employee, etc.
    metadata: Optional[dict] = None


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


# ============== NOTIFICATION CRUD ==============

@router.get("")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for the current user"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "employee")
    
    # Build query - notifications for this user or for their role
    query = {
        "company_id": company_id,
        "$or": [
            {"target_user_id": user_id},
            {"target_user_id": None, "target_role": {"$in": [user_role, "all"]}},
            {"target_user_id": None, "target_role": None}  # Broadcast to all
        ]
    }
    
    if unread_only:
        query["read_by"] = {"$nin": [user_id]}
    
    notifications = await db.notifications.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Mark which ones are read by this user
    for n in notifications:
        n["is_read"] = user_id in n.get("read_by", [])
    
    return notifications


@router.get("/count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "employee")
    
    query = {
        "company_id": company_id,
        "read_by": {"$nin": [user_id]},
        "$or": [
            {"target_user_id": user_id},
            {"target_user_id": None, "target_role": {"$in": [user_role, "all"]}},
            {"target_user_id": None, "target_role": None}
        ]
    }
    
    count = await db.notifications.count_documents(query)
    return {"unread_count": count}


@router.post("/mark-read")
async def mark_as_read(data: MarkReadRequest, current_user: dict = Depends(get_current_user)):
    """Mark notifications as read"""
    user_id = current_user.get("user_id")
    
    result = await db.notifications.update_many(
        {"notification_id": {"$in": data.notification_ids}},
        {"$addToSet": {"read_by": user_id}}
    )
    
    return {"marked_count": result.modified_count}


@router.post("/mark-all-read")
async def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for current user"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "employee")
    
    query = {
        "company_id": company_id,
        "read_by": {"$nin": [user_id]},
        "$or": [
            {"target_user_id": user_id},
            {"target_user_id": None, "target_role": {"$in": [user_role, "all"]}},
            {"target_user_id": None, "target_role": None}
        ]
    }
    
    result = await db.notifications.update_many(
        query,
        {"$addToSet": {"read_by": user_id}}
    )
    
    return {"marked_count": result.modified_count}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a notification (admin only)"""
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar notificaciones")
    
    result = await db.notifications.delete_one({
        "notification_id": notification_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    
    return {"message": "Notificación eliminada"}


# ============== INTERNAL: CREATE NOTIFICATIONS ==============

async def create_notification(
    company_id: str,
    title: str,
    message: str,
    notification_type: str,
    priority: str = "normal",
    link: str = None,
    target_user_id: str = None,
    target_role: str = None,
    metadata: dict = None,
    created_by: str = None
):
    """Internal function to create a notification"""
    if db is None:
        return None
    
    notification = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "title": title,
        "message": message,
        "type": notification_type,
        "priority": priority,
        "link": link,
        "target_user_id": target_user_id,
        "target_role": target_role,
        "metadata": metadata or {},
        "read_by": [],
        "created_by": created_by,
        "created_at": now_iso()
    }
    
    await db.notifications.insert_one(notification)
    return notification["notification_id"]


# ============== NOTIFICATION TRIGGERS ==============

@router.post("/trigger/payroll-approval")
async def trigger_payroll_approval_notification(
    period_id: str,
    period_description: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger notification when payroll needs approval"""
    company_id = current_user.get("company_id")
    user_name = current_user.get("name", current_user.get("email", "Usuario"))
    
    notif_id = await create_notification(
        company_id=company_id,
        title="Nómina Pendiente de Aprobación",
        message=f"{user_name} ha enviado la nómina '{period_description}' para aprobación.",
        notification_type="payroll_approval",
        priority="high",
        link=f"/payroll-v2?period={period_id}",
        target_role="admin",  # Also hr_manager and finance_manager should see
        metadata={"period_id": period_id, "period_description": period_description},
        created_by=current_user.get("user_id")
    )
    
    # Also notify hr_manager and finance_manager
    await create_notification(
        company_id=company_id,
        title="Nómina Pendiente de Aprobación",
        message=f"{user_name} ha enviado la nómina '{period_description}' para aprobación.",
        notification_type="payroll_approval",
        priority="high",
        link=f"/payroll-v2?period={period_id}",
        target_role="hr_manager",
        metadata={"period_id": period_id},
        created_by=current_user.get("user_id")
    )
    
    return {"message": "Notificación enviada", "notification_id": notif_id}


@router.post("/trigger/payroll-approved")
async def trigger_payroll_approved_notification(
    period_id: str,
    period_description: str,
    submitted_by_user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger notification when payroll is approved"""
    company_id = current_user.get("company_id")
    approver_name = current_user.get("name", current_user.get("email", "Usuario"))
    
    notif_id = await create_notification(
        company_id=company_id,
        title="Nómina Aprobada",
        message=f"La nómina '{period_description}' ha sido aprobada por {approver_name}.",
        notification_type="payroll_approved",
        priority="normal",
        link=f"/payroll-v2?period={period_id}",
        target_user_id=submitted_by_user_id,
        metadata={"period_id": period_id, "approved_by": current_user.get("user_id")},
        created_by=current_user.get("user_id")
    )
    
    return {"message": "Notificación enviada", "notification_id": notif_id}


@router.post("/trigger/payroll-rejected")
async def trigger_payroll_rejected_notification(
    period_id: str,
    period_description: str,
    submitted_by_user_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger notification when payroll is rejected"""
    company_id = current_user.get("company_id")
    rejector_name = current_user.get("name", current_user.get("email", "Usuario"))
    
    notif_id = await create_notification(
        company_id=company_id,
        title="Nómina Rechazada",
        message=f"La nómina '{period_description}' fue rechazada por {rejector_name}. Motivo: {reason}",
        notification_type="payroll_rejected",
        priority="high",
        link=f"/payroll-v2?period={period_id}",
        target_user_id=submitted_by_user_id,
        metadata={"period_id": period_id, "reason": reason},
        created_by=current_user.get("user_id")
    )
    
    return {"message": "Notificación enviada", "notification_id": notif_id}


# ============== EMPLOYEE PORTAL NOTIFICATIONS ==============

@router.post("/trigger/vacation-status")
async def trigger_vacation_status_notification(
    employee_id: str,
    employee_name: str,
    status: str,  # approved, rejected
    vacation_dates: str,
    reason: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Trigger notification when vacation is approved/rejected"""
    company_id = current_user.get("company_id")
    approver_name = current_user.get("name", current_user.get("email", "Usuario"))
    
    if status == "approved":
        title = "Vacaciones Aprobadas"
        message = f"Tu solicitud de vacaciones ({vacation_dates}) ha sido aprobada por {approver_name}."
        priority = "normal"
    else:
        title = "Vacaciones Rechazadas"
        message = f"Tu solicitud de vacaciones ({vacation_dates}) fue rechazada. {f'Motivo: {reason}' if reason else ''}"
        priority = "high"
    
    # Get portal user for this employee
    portal_user = await db.portal_users.find_one(
        {"company_id": company_id, "employee_id": employee_id},
        {"_id": 0, "user_id": 1}
    )
    
    target_user = portal_user.get("user_id") if portal_user else None
    
    notif_id = await create_notification(
        company_id=company_id,
        title=title,
        message=message,
        notification_type=f"vacation_{status}",
        priority=priority,
        link="/employee-portal/vacations",
        target_user_id=target_user,
        metadata={"employee_id": employee_id, "status": status, "dates": vacation_dates},
        created_by=current_user.get("user_id")
    )
    
    return {"message": "Notificación enviada", "notification_id": notif_id}


@router.post("/trigger/payroll-available")
async def trigger_payroll_available_notification(
    period_id: str,
    period_description: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger notification when payroll is paid and available to employees"""
    company_id = current_user.get("company_id")
    
    notif_id = await create_notification(
        company_id=company_id,
        title="Nómina Disponible",
        message=f"Tu recibo de nómina de '{period_description}' está disponible para consulta.",
        notification_type="payroll_available",
        priority="normal",
        link="/employee-portal/payroll",
        target_role="all",  # All employees
        metadata={"period_id": period_id},
        created_by=current_user.get("user_id")
    )
    
    return {"message": "Notificación enviada a todos los empleados", "notification_id": notif_id}


@router.post("/trigger/evaluation-scheduled")
async def trigger_evaluation_scheduled_notification(
    employee_id: str,
    employee_name: str,
    evaluation_type: str,
    scheduled_date: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger notification when evaluation is scheduled"""
    company_id = current_user.get("company_id")
    
    portal_user = await db.portal_users.find_one(
        {"company_id": company_id, "employee_id": employee_id},
        {"_id": 0, "user_id": 1}
    )
    
    target_user = portal_user.get("user_id") if portal_user else None
    
    notif_id = await create_notification(
        company_id=company_id,
        title="Evaluación Programada",
        message=f"Tienes una evaluación de desempeño ({evaluation_type}) programada para el {scheduled_date}.",
        notification_type="evaluation_scheduled",
        priority="normal",
        link="/employee-portal/evaluations",
        target_user_id=target_user,
        metadata={"employee_id": employee_id, "evaluation_type": evaluation_type, "date": scheduled_date},
        created_by=current_user.get("user_id")
    )
    
    return {"message": "Notificación enviada", "notification_id": notif_id}


@router.post("/trigger/attendance-reminder")
async def trigger_attendance_reminder(
    employee_ids: List[str],
    reminder_type: str,  # check_in, check_out
    current_user: dict = Depends(get_current_user)
):
    """Trigger attendance reminder notifications"""
    company_id = current_user.get("company_id")
    
    if reminder_type == "check_in":
        title = "Recordatorio de Entrada"
        message = "No olvides registrar tu entrada de hoy."
    else:
        title = "Recordatorio de Salida"
        message = "No olvides registrar tu salida antes de irte."
    
    count = 0
    for emp_id in employee_ids:
        portal_user = await db.portal_users.find_one(
            {"company_id": company_id, "employee_id": emp_id},
            {"_id": 0, "user_id": 1}
        )
        
        if portal_user:
            await create_notification(
                company_id=company_id,
                title=title,
                message=message,
                notification_type=f"attendance_{reminder_type}",
                priority="low",
                link="/employee-portal/attendance",
                target_user_id=portal_user.get("user_id"),
                metadata={"employee_id": emp_id, "reminder_type": reminder_type},
                created_by=current_user.get("user_id")
            )
            count += 1
    
    return {"message": f"Recordatorios enviados a {count} empleados"}


# Export the create_notification function for use in other modules
__all__ = ["router", "init_router", "create_notification"]
