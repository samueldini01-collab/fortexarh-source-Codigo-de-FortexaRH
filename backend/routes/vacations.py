"""
Vacations and Leave Management - FortexaRH
Complete leave management with Dominican Republic labor law compliance
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta, date
import uuid
from io import BytesIO, StringIO
from fastapi.responses import StreamingResponse
from services.employee_notifications import create_employee_notification

router = APIRouter(prefix="/vacations", tags=["Vacations"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


# ==================== Leave Types ====================

LEAVE_TYPES = [
    {"code": "vacation", "name": "Vacaciones", "paid": True, "requires_approval": True, "max_days": None},
    {"code": "sick", "name": "Licencia por Enfermedad", "paid": True, "requires_approval": True, "max_days": None},
    {"code": "maternity", "name": "Licencia por Maternidad", "paid": True, "requires_approval": True, "max_days": 84},
    {"code": "paternity", "name": "Licencia por Paternidad", "paid": True, "requires_approval": True, "max_days": 2},
    {"code": "bereavement", "name": "Licencia por Duelo", "paid": True, "requires_approval": True, "max_days": 3},
    {"code": "marriage", "name": "Licencia por Matrimonio", "paid": True, "requires_approval": True, "max_days": 5},
    {"code": "personal", "name": "Permiso Personal", "paid": False, "requires_approval": True, "max_days": None},
    {"code": "unpaid", "name": "Licencia Sin Sueldo", "paid": False, "requires_approval": True, "max_days": None},
    {"code": "medical_appointment", "name": "Cita Médica", "paid": True, "requires_approval": True, "max_days": 1},
    {"code": "study", "name": "Permiso de Estudio", "paid": False, "requires_approval": True, "max_days": None},
]


# ==================== Models ====================
from models.hr import (
    LeaveTypeCreate, LeaveRequestCreate, LeaveApproval, LeavePolicyCreate
)


# ==================== Helper Functions ====================

def calculate_vacation_entitlement(hire_date: str, policy: dict = None) -> dict:
    """
    Calculate vacation days based on Dominican Republic labor law:
    - After 1 year of service: 14 working days
    - After 5 years: 18 working days (14 + 1 day per additional year, max 18)
    """
    if policy is None:
        policy = {
            "base_vacation_days": 14,
            "additional_days_per_year": 1,
            "max_vacation_days": 18,
            "years_for_additional": 5,
            "requires_min_service_months": 12
        }
    
    try:
        hire = datetime.strptime(hire_date, "%Y-%m-%d").date()
    except:
        hire = datetime.strptime(hire_date[:10], "%Y-%m-%d").date()
    
    today = date.today()
    service_days = (today - hire).days
    service_years = service_days // 365
    service_months = service_days // 30
    
    # Must have minimum service
    if service_months < policy.get("requires_min_service_months", 12):
        return {
            "entitled_days": 0,
            "service_years": service_years,
            "service_months": service_months,
            "eligible": False,
            "message": f"Requiere mínimo {policy['requires_min_service_months']} meses de servicio"
        }
    
    # Calculate days based on years of service
    base_days = policy.get("base_vacation_days", 14)
    additional_per_year = policy.get("additional_days_per_year", 1)
    max_days = policy.get("max_vacation_days", 18)
    
    if service_years >= 1:
        additional_years = max(0, service_years - 1)
        additional_days = additional_years * additional_per_year
        entitled_days = min(base_days + additional_days, max_days)
    else:
        entitled_days = 0
    
    return {
        "entitled_days": entitled_days,
        "service_years": service_years,
        "service_months": service_months,
        "eligible": entitled_days > 0,
        "message": f"{entitled_days} días de vacaciones (Ley 16-92)"
    }


def calculate_working_days(start_date: str, end_date: str) -> int:
    """Calculate working days (excluding weekends) between two dates"""
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    working_days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Monday to Friday
            working_days += 1
        current += timedelta(days=1)
    
    return working_days


# ==================== Leave Policies ====================

@router.get("/policies")
async def get_leave_policies(current_user: dict = Depends(get_current_user)):
    """Get company leave policies"""
    policies = await db.leave_policies.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(50)
    
    if not policies:
        # Return default Dominican Republic policy
        return [{
            "policy_id": "default",
            "name": "Política Estándar (Ley 16-92)",
            "base_vacation_days": 14,
            "additional_days_per_year": 1,
            "max_vacation_days": 18,
            "years_for_additional": 1,
            "carry_over_allowed": True,
            "max_carry_over_days": 5,
            "requires_min_service_months": 12,
            "is_default": True
        }]
    
    return policies


@router.post("/policies")
async def create_leave_policy(data: LeavePolicyCreate, current_user: dict = Depends(get_current_user)):
    """Create a custom leave policy"""
    policy_id = f"policy_{uuid.uuid4().hex[:12]}"
    policy = {
        "policy_id": policy_id,
        "company_id": current_user.get("company_id"),
        **data.dict(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.leave_policies.insert_one(policy)
    return {"policy_id": policy_id, "message": "Política creada exitosamente"}


# ==================== Leave Types ====================

@router.get("/types")
async def get_leave_types(current_user: dict = Depends(get_current_user)):
    """Get available leave types"""
    # First check for custom company types
    custom_types = await db.leave_types.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(50)
    
    if custom_types:
        return custom_types
    
    return LEAVE_TYPES


@router.post("/types")
async def create_leave_type(data: LeaveTypeCreate, current_user: dict = Depends(get_current_user)):
    """Create a custom leave type"""
    type_id = f"ltype_{uuid.uuid4().hex[:12]}"
    leave_type = {
        "type_id": type_id,
        "company_id": current_user.get("company_id"),
        **data.dict(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.leave_types.insert_one(leave_type)
    return {"type_id": type_id, "message": "Tipo de permiso creado"}


# ==================== Employee Balance ====================

@router.get("/balance/{employee_id}")
async def get_employee_leave_balance(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get leave balance for an employee"""
    company_id = current_user.get("company_id")
    
    employee = await db.employees.find_one(
        {"employee_id": employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Get company policy
    policy = await db.leave_policies.find_one(
        {"company_id": company_id, "is_default": True},
        {"_id": 0}
    )
    
    # Calculate entitlement
    hire_date = employee.get("hire_date", employee.get("created_at", "2024-01-01"))
    entitlement = calculate_vacation_entitlement(hire_date, policy)
    
    # Get current year's used vacation days
    current_year = datetime.now().year
    year_start = f"{current_year}-01-01"
    year_end = f"{current_year}-12-31"
    
    used_leaves = await db.vacations.find({
        "company_id": company_id,
        "employee_id": employee_id,
        "status": "approved",
        "start_date": {"$gte": year_start, "$lte": year_end}
    }, {"_id": 0}).to_list(100)
    
    # Calculate used days by type
    used_by_type = {}
    for leave in used_leaves:
        leave_type = leave.get("leave_type", "vacation")
        days = leave.get("days_requested", 0)
        used_by_type[leave_type] = used_by_type.get(leave_type, 0) + days
    
    vacation_used = used_by_type.get("vacation", 0)
    vacation_available = max(0, entitlement["entitled_days"] - vacation_used)
    
    # Get carry over from previous year
    carry_over = await db.leave_carryover.find_one({
        "company_id": company_id,
        "employee_id": employee_id,
        "year": current_year
    })
    carry_over_days = carry_over.get("days", 0) if carry_over else 0
    
    return {
        "employee_id": employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "hire_date": hire_date,
        "service_years": entitlement["service_years"],
        "service_months": entitlement["service_months"],
        "year": current_year,
        "vacation": {
            "entitled": entitlement["entitled_days"],
            "carry_over": carry_over_days,
            "total_available": entitlement["entitled_days"] + carry_over_days,
            "used": vacation_used,
            "remaining": vacation_available + carry_over_days,
            "eligible": entitlement["eligible"],
            "message": entitlement["message"]
        },
        "used_by_type": used_by_type,
        "pending_requests": await db.vacations.count_documents({
            "company_id": company_id,
            "employee_id": employee_id,
            "status": "pending"
        })
    }


@router.get("/balance")
async def get_all_employees_balance(
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get leave balance for all employees"""
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id, "status": "active"}
    if department:
        query["department"] = department
    
    employees = await db.employees.find(query, {"_id": 0}).to_list(1000)
    
    balances = []
    for emp in employees:
        balance = await get_employee_leave_balance(emp["employee_id"], current_user)
        balances.append(balance)
    
    return balances


# ==================== Leave Requests ====================

@router.get("")
async def get_leave_requests(
    status: Optional[str] = None,
    leave_type: Optional[str] = None,
    employee_id: Optional[str] = None,
    department: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get leave requests with filters"""
    query = {"company_id": current_user.get("company_id")}
    
    if status:
        query["status"] = status
    if leave_type:
        query["leave_type"] = leave_type
    if employee_id:
        query["employee_id"] = employee_id
    if department:
        query["department"] = department
    if start_date and end_date:
        query["$or"] = [
            {"start_date": {"$gte": start_date, "$lte": end_date}},
            {"end_date": {"$gte": start_date, "$lte": end_date}}
        ]
    
    requests = await db.vacations.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return requests


@router.get("/pending")
async def get_pending_requests(current_user: dict = Depends(get_current_user)):
    """Get all pending leave requests for approval"""
    requests = await db.vacations.find(
        {"company_id": current_user.get("company_id"), "status": "pending"},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    return requests


# ==================== Calendar View ====================
# NOTE: This route MUST be defined before /{vacation_id} to avoid route conflicts

@router.get("/calendar")
async def get_leave_calendar(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...),
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get calendar view of approved leaves for a month"""
    company_id = current_user.get("company_id")
    
    # Calculate date range
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    query = {
        "company_id": company_id,
        "status": "approved",
        "$or": [
            {"start_date": {"$gte": start_date, "$lt": end_date}},
            {"end_date": {"$gte": start_date, "$lt": end_date}},
            {"start_date": {"$lt": start_date}, "end_date": {"$gte": end_date}}
        ]
    }
    
    if department:
        query["department"] = department
    
    leaves = await db.vacations.find(query, {"_id": 0}).to_list(500)
    
    # Organize by date
    calendar_data = {}
    for leave in leaves:
        start = datetime.strptime(leave["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(leave["end_date"], "%Y-%m-%d").date()
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            
            calendar_data[date_str].append({
                "vacation_id": leave["vacation_id"],
                "employee_id": leave["employee_id"],
                "employee_name": leave["employee_name"],
                "department": leave.get("department"),
                "leave_type": leave["leave_type"]
            })
            current += timedelta(days=1)
    
    return {
        "month": month,
        "year": year,
        "leaves": leaves,
        "calendar": calendar_data
    }


@router.post("")
async def create_leave_request(data: LeaveRequestCreate, current_user: dict = Depends(get_current_user)):
    """Create a new leave request"""
    company_id = current_user.get("company_id")
    
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Calculate days requested
    days_requested = calculate_working_days(data.start_date, data.end_date)
    
    # Check for vacation type - validate balance
    if data.leave_type == "vacation":
        balance = await get_employee_leave_balance(data.employee_id, current_user)
        if not balance["vacation"]["eligible"]:
            raise HTTPException(status_code=400, detail=balance["vacation"]["message"])
        if days_requested > balance["vacation"]["remaining"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Días solicitados ({days_requested}) exceden el balance disponible ({balance['vacation']['remaining']})"
            )
    
    # Check for overlapping requests
    overlap = await db.vacations.find_one({
        "company_id": company_id,
        "employee_id": data.employee_id,
        "status": {"$in": ["pending", "approved"]},
        "$or": [
            {"start_date": {"$lte": data.end_date}, "end_date": {"$gte": data.start_date}}
        ]
    })
    if overlap:
        raise HTTPException(status_code=400, detail="Ya existe una solicitud para estas fechas")
    
    vacation_id = f"vac_{uuid.uuid4().hex[:12]}"
    vacation = {
        "vacation_id": vacation_id,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "department": employee.get("department"),
        "position": employee.get("position"),
        "leave_type": data.leave_type,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days_requested": days_requested,
        "reason": data.reason,
        "attachment_url": data.attachment_url,
        "status": "pending",
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.vacations.insert_one(vacation)
    
    # Create notification for approvers
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "type": "leave_request",
        "title": "Nueva Solicitud de Permiso",
        "message": f"{employee['first_name']} {employee['last_name']} ha solicitado {days_requested} días de {data.leave_type}",
        "reference_id": vacation_id,
        "reference_type": "vacation",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"vacation_id": vacation_id, "days_requested": days_requested, "message": "Solicitud creada exitosamente"}


@router.get("/{vacation_id}")
async def get_leave_request(vacation_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific leave request"""
    request = await db.vacations.find_one(
        {"vacation_id": vacation_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return request


@router.put("/{vacation_id}/approve")
async def approve_leave_request(
    vacation_id: str,
    data: Optional[LeaveApproval] = None,
    current_user: dict = Depends(get_current_user)
):
    """Approve a leave request"""
    company_id = current_user.get("company_id")
    
    request = await db.vacations.find_one(
        {"vacation_id": vacation_id, "company_id": company_id}
    )
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Solo se pueden aprobar solicitudes pendientes")
    
    update_data = {
        "status": "approved",
        "approved_by": current_user["user_id"],
        "approved_by_name": current_user.get("name"),
        "approved_at": datetime.now(timezone.utc).isoformat()
    }
    
    if data and data.approver_comments:
        update_data["approver_comments"] = data.approver_comments
    
    await db.vacations.update_one(
        {"vacation_id": vacation_id},
        {"$set": update_data}
    )
    
    # Notify employee
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "user_id": request["employee_id"],
        "type": "leave_approved",
        "title": "Solicitud Aprobada",
        "message": f"Tu solicitud de {request['leave_type']} del {request['start_date']} al {request['end_date']} ha sido aprobada",
        "reference_id": vacation_id,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Push notification to employee portal
    await create_employee_notification(
        db,
        employee_id=request["employee_id"],
        company_id=company_id,
        title="Vacaciones Aprobadas",
        message=f"Tu solicitud de {request['leave_type']} del {request['start_date']} al {request['end_date']} ha sido aprobada.",
        notification_type="success",
        category="vacation",
        action_url="/vacations",
    )
    
    return {"message": "Solicitud aprobada exitosamente"}


@router.put("/{vacation_id}/reject")
async def reject_leave_request(
    vacation_id: str,
    data: Optional[LeaveApproval] = None,
    current_user: dict = Depends(get_current_user)
):
    """Reject a leave request"""
    company_id = current_user.get("company_id")
    
    request = await db.vacations.find_one(
        {"vacation_id": vacation_id, "company_id": company_id}
    )
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Solo se pueden rechazar solicitudes pendientes")
    
    update_data = {
        "status": "rejected",
        "rejected_by": current_user["user_id"],
        "rejected_by_name": current_user.get("name"),
        "rejected_at": datetime.now(timezone.utc).isoformat()
    }
    
    if data and data.approver_comments:
        update_data["rejection_reason"] = data.approver_comments
    
    await db.vacations.update_one(
        {"vacation_id": vacation_id},
        {"$set": update_data}
    )
    
    # Notify employee
    reason_text = f" Motivo: {data.approver_comments}" if data and data.approver_comments else ""
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "user_id": request["employee_id"],
        "type": "leave_rejected",
        "title": "Solicitud Rechazada",
        "message": f"Tu solicitud de {request['leave_type']} del {request['start_date']} al {request['end_date']} ha sido rechazada.{reason_text}",
        "reference_id": vacation_id,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Push notification to employee portal
    await create_employee_notification(
        db,
        employee_id=request["employee_id"],
        company_id=company_id,
        title="Solicitud de Vacaciones Rechazada",
        message=f"Tu solicitud de {request['leave_type']} del {request['start_date']} al {request['end_date']} ha sido rechazada.{reason_text}",
        notification_type="alert",
        category="vacation",
        action_url="/vacations",
    )
    
    return {"message": "Solicitud rechazada"}


@router.put("/{vacation_id}/cancel")
async def cancel_leave_request(vacation_id: str, current_user: dict = Depends(get_current_user)):
    """Cancel a leave request (by employee)"""
    company_id = current_user.get("company_id")
    
    request = await db.vacations.find_one(
        {"vacation_id": vacation_id, "company_id": company_id}
    )
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if request["status"] not in ["pending", "approved"]:
        raise HTTPException(status_code=400, detail="No se puede cancelar esta solicitud")
    
    # Check if leave hasn't started yet
    if request["status"] == "approved":
        start = datetime.strptime(request["start_date"], "%Y-%m-%d").date()
        if start <= date.today():
            raise HTTPException(status_code=400, detail="No se puede cancelar un permiso que ya inició")
    
    await db.vacations.update_one(
        {"vacation_id": vacation_id},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": current_user["user_id"]
        }}
    )
    
    return {"message": "Solicitud cancelada"}

# ==================== Reports & Export ====================

@router.get("/report/summary")
async def get_leave_summary_report(
    year: int = Query(...),
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get annual leave summary report"""
    company_id = current_user.get("company_id")
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"
    
    pipeline = [
        {
            "$match": {
                "company_id": company_id,
                "status": "approved",
                "start_date": {"$gte": year_start, "$lte": year_end}
            }
        },
        {
            "$group": {
                "_id": {
                    "employee_id": "$employee_id",
                    "leave_type": "$leave_type"
                },
                "employee_name": {"$first": "$employee_name"},
                "department": {"$first": "$department"},
                "total_days": {"$sum": "$days_requested"},
                "requests_count": {"$sum": 1}
            }
        },
        {
            "$group": {
                "_id": "$_id.employee_id",
                "employee_name": {"$first": "$employee_name"},
                "department": {"$first": "$department"},
                "leaves_by_type": {
                    "$push": {
                        "type": "$_id.leave_type",
                        "days": "$total_days",
                        "count": "$requests_count"
                    }
                },
                "total_days_taken": {"$sum": "$total_days"}
            }
        },
        {"$sort": {"total_days_taken": -1}}
    ]
    
    if department:
        pipeline[0]["$match"]["department"] = department
    
    report = await db.vacations.aggregate(pipeline).to_list(1000)
    
    # Get type summary
    type_pipeline = [
        {
            "$match": {
                "company_id": company_id,
                "status": "approved",
                "start_date": {"$gte": year_start, "$lte": year_end}
            }
        },
        {
            "$group": {
                "_id": "$leave_type",
                "total_days": {"$sum": "$days_requested"},
                "total_requests": {"$sum": 1}
            }
        }
    ]
    
    type_summary = await db.vacations.aggregate(type_pipeline).to_list(20)
    
    return {
        "year": year,
        "department": department,
        "by_employee": report,
        "by_type": {t["_id"]: t for t in type_summary},
        "total_days_taken": sum(e["total_days_taken"] for e in report)
    }


@router.get("/export")
async def export_leave_requests(
    start_date: str = Query(...),
    end_date: str = Query(...),
    format: str = Query("csv"),
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export leave requests to CSV or Excel"""
    company_id = current_user.get("company_id")
    
    query = {
        "company_id": company_id,
        "$or": [
            {"start_date": {"$gte": start_date, "$lte": end_date}},
            {"end_date": {"$gte": start_date, "$lte": end_date}}
        ]
    }
    if status:
        query["status"] = status
    
    requests = await db.vacations.find(query, {"_id": 0}).sort("start_date", 1).to_list(10000)
    
    type_labels = {t["code"]: t["name"] for t in LEAVE_TYPES}
    status_labels = {"pending": "Pendiente", "approved": "Aprobado", "rejected": "Rechazado", "cancelled": "Cancelado"}
    
    if format == "csv":
        import csv
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Empleado", "Departamento", "Tipo", "Fecha Inicio", "Fecha Fin",
            "Días", "Estado", "Motivo", "Fecha Solicitud"
        ])
        
        for req in requests:
            writer.writerow([
                req.get("employee_name", ""),
                req.get("department", ""),
                type_labels.get(req.get("leave_type", ""), req.get("leave_type", "")),
                req.get("start_date", ""),
                req.get("end_date", ""),
                req.get("days_requested", 0),
                status_labels.get(req.get("status", ""), req.get("status", "")),
                req.get("reason", ""),
                req.get("requested_at", "")[:10] if req.get("requested_at") else ""
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=permisos_{start_date}_{end_date}.csv"}
        )
    
    elif format == "excel":
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Permisos"
        
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        headers = ["Empleado", "Departamento", "Tipo", "Fecha Inicio", "Fecha Fin",
                   "Días", "Estado", "Motivo", "Fecha Solicitud"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        for row, req in enumerate(requests, 2):
            ws.cell(row=row, column=1, value=req.get("employee_name", ""))
            ws.cell(row=row, column=2, value=req.get("department", ""))
            ws.cell(row=row, column=3, value=type_labels.get(req.get("leave_type", ""), req.get("leave_type", "")))
            ws.cell(row=row, column=4, value=req.get("start_date", ""))
            ws.cell(row=row, column=5, value=req.get("end_date", ""))
            ws.cell(row=row, column=6, value=req.get("days_requested", 0))
            ws.cell(row=row, column=7, value=status_labels.get(req.get("status", ""), req.get("status", "")))
            ws.cell(row=row, column=8, value=req.get("reason", ""))
            ws.cell(row=row, column=9, value=req.get("requested_at", "")[:10] if req.get("requested_at") else "")
        
        for col in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 30)
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=permisos_{start_date}_{end_date}.xlsx"}
        )
    
    raise HTTPException(status_code=400, detail="Formato no soportado")
