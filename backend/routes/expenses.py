"""
Expenses & Travel Allowances (Viáticos) Routes - FortexaRH
Manages expense requests, advances, approvals, and reimbursements
"""
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import base64
import os

router = APIRouter(prefix="/expenses", tags=["Expenses & Viáticos"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials=Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


# ==================== ENUMS ====================

class ExpenseType(str, Enum):
    TRAVEL = "travel"  # Viaje de negocios
    ADMINISTRATIVE = "administrative"  # Gastos administrativos
    ACCOMMODATION = "accommodation"  # Alojamiento
    MEALS = "meals"  # Comidas
    TRANSPORTATION = "transportation"  # Transporte
    OTHER = "other"  # Otros


class RequestStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED_MANAGER = "approved_manager"
    APPROVED_ADMIN = "approved_admin"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AdvanceStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DISBURSED = "disbursed"
    REJECTED = "rejected"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    VERIFIED = "verified"
    REQUIRES_RETURN = "requires_return"


# ==================== MODELS ====================

class ExpenseRequestCreate(BaseModel):
    title: str
    expense_type: ExpenseType
    description: str
    destination: Optional[str] = None
    start_date: str
    end_date: str
    estimated_budget: float
    budget_breakdown: Optional[List[dict]] = None  # [{category: str, amount: float, description: str}]
    requires_advance: bool = False
    advance_amount: Optional[float] = None
    advance_date: Optional[str] = None
    notes: Optional[str] = None


class ExpenseRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    estimated_budget: Optional[float] = None
    budget_breakdown: Optional[List[dict]] = None
    requires_advance: Optional[bool] = None
    advance_amount: Optional[float] = None
    notes: Optional[str] = None


class ApprovalAction(BaseModel):
    action: str  # approve, reject
    comments: Optional[str] = None


class ExpenseItem(BaseModel):
    category: str
    description: str
    amount: float
    date: str
    has_receipt: bool = False
    receipt_number: Optional[str] = None
    vendor: Optional[str] = None
    is_deductible: bool = True


class ExpenseVerification(BaseModel):
    items: List[ExpenseItem]
    total_spent: float
    notes: Optional[str] = None


# ==================== EXPENSE CATEGORIES ====================

EXPENSE_CATEGORIES = [
    {"id": "transporte", "name": "Transporte", "icon": "car"},
    {"id": "alojamiento", "name": "Alojamiento", "icon": "hotel"},
    {"id": "alimentacion", "name": "Alimentación", "icon": "utensils"},
    {"id": "materiales", "name": "Materiales", "icon": "package"},
    {"id": "viajes", "name": "Viajes", "icon": "plane"},
    {"id": "administrativos", "name": "Gastos Administrativos", "icon": "file-text"},
    {"id": "educacion", "name": "Educación", "icon": "graduation-cap"},
    {"id": "uniformes", "name": "Uniformes", "icon": "shirt"},
    {"id": "otros", "name": "Otros", "icon": "more-horizontal"}
]


# ==================== ENDPOINTS ====================

@router.get("/categories")
async def get_expense_categories():
    """Get available expense categories"""
    return EXPENSE_CATEGORIES


@router.get("/requests")
async def get_expense_requests(
    status: Optional[str] = None,
    employee_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get expense requests - filtered by role"""
    company_id = current_user.get("company_id")
    user_role = current_user.get("role")
    
    query = {"company_id": company_id}
    
    # Filter by status
    if status:
        query["status"] = status
    
    # Regular employees only see their own requests
    if user_role not in ["admin", "hr_manager", "manager"]:
        query["employee_id"] = current_user.get("employee_id") or current_user.get("user_id")
    elif employee_id:
        query["employee_id"] = employee_id
    
    requests = await db.expense_requests.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return requests


@router.get("/requests/pending-approval")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    """Get requests pending approval for managers/admins"""
    company_id = current_user.get("company_id")
    user_role = current_user.get("role")
    
    if user_role not in ["admin", "hr_manager", "manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver aprobaciones pendientes")
    
    # Managers see requests pending manager approval
    # Admins see all pending requests
    if user_role == "manager":
        query = {
            "company_id": company_id,
            "status": "pending"
        }
    else:
        query = {
            "company_id": company_id,
            "status": {"$in": ["pending", "approved_manager"]}
        }
    
    requests = await db.expense_requests.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return requests


@router.get("/requests/{request_id}")
async def get_expense_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific expense request with all details"""
    company_id = current_user.get("company_id")
    
    expense_req = await db.expense_requests.find_one(
        {"request_id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not expense_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Get related advances
    advances = await db.expense_advances.find(
        {"request_id": request_id},
        {"_id": 0}
    ).to_list(10)
    
    # Get expense items/verification
    expense_items = await db.expense_items.find(
        {"request_id": request_id},
        {"_id": 0}
    ).to_list(100)
    
    # Get attachments
    attachments = await db.expense_attachments.find(
        {"request_id": request_id},
        {"_id": 0, "file_data": 0}  # Exclude binary data
    ).to_list(50)
    
    # Get approval history
    approvals = await db.expense_approvals.find(
        {"request_id": request_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(20)
    
    return {
        "request": expense_req,
        "advances": advances,
        "expense_items": expense_items,
        "attachments": attachments,
        "approval_history": approvals
    }


@router.post("/requests")
async def create_expense_request(
    data: ExpenseRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new expense/travel request"""
    company_id = current_user.get("company_id")
    
    # Get employee info
    employee = await db.employees.find_one(
        {"employee_id": current_user.get("employee_id")},
        {"_id": 0, "first_name": 1, "last_name": 1, "department": 1, "position": 1}
    )
    
    if not employee:
        # Use user info as fallback
        employee = {
            "first_name": current_user.get("name", "").split()[0] if current_user.get("name") else "",
            "last_name": " ".join(current_user.get("name", "").split()[1:]) if current_user.get("name") else "",
            "department": "",
            "position": ""
        }
    
    request_id = f"exp_{uuid.uuid4().hex[:8]}"
    
    expense_request = {
        "request_id": request_id,
        "company_id": company_id,
        "employee_id": current_user.get("employee_id") or current_user.get("user_id"),
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
        "department": employee.get("department", ""),
        "position": employee.get("position", ""),
        "title": data.title,
        "expense_type": data.expense_type,
        "description": data.description,
        "destination": data.destination,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "estimated_budget": data.estimated_budget,
        "budget_breakdown": data.budget_breakdown or [],
        "requires_advance": data.requires_advance,
        "advance_amount": data.advance_amount if data.requires_advance else None,
        "advance_date": data.advance_date if data.requires_advance else None,
        "actual_spent": 0,
        "status": RequestStatus.PENDING,
        "verification_status": None,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.expense_requests.insert_one(expense_request)
    
    # Create advance request if needed
    if data.requires_advance and data.advance_amount:
        advance = {
            "advance_id": f"adv_{uuid.uuid4().hex[:8]}",
            "request_id": request_id,
            "company_id": company_id,
            "employee_id": current_user.get("employee_id") or current_user.get("user_id"),
            "amount": data.advance_amount,
            "requested_date": data.advance_date,
            "status": AdvanceStatus.PENDING,
            "disbursed_amount": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.expense_advances.insert_one(advance)
    
    # Log activity
    await db.expense_approvals.insert_one({
        "approval_id": f"apr_{uuid.uuid4().hex[:8]}",
        "request_id": request_id,
        "action": "created",
        "performed_by": current_user.get("user_id"),
        "performed_by_name": current_user.get("name"),
        "comments": "Solicitud creada",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": "Solicitud creada exitosamente",
        "request_id": request_id
    }


@router.put("/requests/{request_id}")
async def update_expense_request(
    request_id: str,
    data: ExpenseRequestUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an expense request (only if draft or pending)"""
    company_id = current_user.get("company_id")
    
    expense_req = await db.expense_requests.find_one(
        {"request_id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not expense_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Only allow updates if pending or draft
    if expense_req["status"] not in ["draft", "pending"]:
        raise HTTPException(status_code=400, detail="No se puede modificar una solicitud ya procesada")
    
    # Check ownership
    if expense_req["employee_id"] != current_user.get("employee_id") and current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para modificar esta solicitud")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.expense_requests.update_one(
        {"request_id": request_id},
        {"$set": update_data}
    )
    
    return {"message": "Solicitud actualizada exitosamente"}


@router.post("/requests/{request_id}/approve")
async def approve_expense_request(
    request_id: str,
    data: ApprovalAction,
    current_user: dict = Depends(get_current_user)
):
    """Approve or reject an expense request"""
    company_id = current_user.get("company_id")
    user_role = current_user.get("role")
    
    if user_role not in ["admin", "hr_manager", "manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para aprobar solicitudes")
    
    expense_req = await db.expense_requests.find_one(
        {"request_id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not expense_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    current_status = expense_req["status"]
    new_status = current_status
    
    if data.action == "approve":
        if user_role == "manager" and current_status == "pending":
            new_status = RequestStatus.APPROVED_MANAGER
        elif user_role in ["admin", "hr_manager"]:
            if current_status in ["pending", "approved_manager"]:
                new_status = RequestStatus.APPROVED_ADMIN
                # If requires advance, mark it as approved
                if expense_req.get("requires_advance"):
                    await db.expense_advances.update_many(
                        {"request_id": request_id, "status": "pending"},
                        {"$set": {"status": AdvanceStatus.APPROVED}}
                    )
    elif data.action == "reject":
        new_status = RequestStatus.REJECTED
    
    await db.expense_requests.update_one(
        {"request_id": request_id},
        {"$set": {
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log approval
    await db.expense_approvals.insert_one({
        "approval_id": f"apr_{uuid.uuid4().hex[:8]}",
        "request_id": request_id,
        "action": data.action,
        "from_status": current_status,
        "to_status": new_status,
        "performed_by": current_user.get("user_id"),
        "performed_by_name": current_user.get("name"),
        "role": user_role,
        "comments": data.comments,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    action_text = "aprobada" if data.action == "approve" else "rechazada"
    return {"message": f"Solicitud {action_text} exitosamente", "new_status": new_status}


@router.post("/requests/{request_id}/disburse-advance")
async def disburse_advance(
    request_id: str,
    amount: float,
    method: str = "transfer",  # transfer, cash, check
    reference: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Record advance disbursement"""
    if current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden desembolsar anticipos")
    
    company_id = current_user.get("company_id")
    
    advance = await db.expense_advances.find_one(
        {"request_id": request_id, "company_id": company_id, "status": "approved"},
        {"_id": 0}
    )
    
    if not advance:
        raise HTTPException(status_code=404, detail="No hay anticipo aprobado pendiente de desembolso")
    
    await db.expense_advances.update_one(
        {"advance_id": advance["advance_id"]},
        {"$set": {
            "status": AdvanceStatus.DISBURSED,
            "disbursed_amount": amount,
            "disbursement_method": method,
            "disbursement_reference": reference,
            "disbursed_at": datetime.now(timezone.utc).isoformat(),
            "disbursed_by": current_user.get("user_id")
        }}
    )
    
    # Update request status
    await db.expense_requests.update_one(
        {"request_id": request_id},
        {"$set": {
            "status": RequestStatus.IN_PROGRESS,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Anticipo desembolsado exitosamente"}


@router.post("/requests/{request_id}/verify")
async def verify_expenses(
    request_id: str,
    data: ExpenseVerification,
    current_user: dict = Depends(get_current_user)
):
    """Submit expense verification with actual expenses"""
    company_id = current_user.get("company_id")
    
    expense_req = await db.expense_requests.find_one(
        {"request_id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not expense_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Save expense items
    for item in data.items:
        expense_item = {
            "item_id": f"item_{uuid.uuid4().hex[:8]}",
            "request_id": request_id,
            "company_id": company_id,
            "category": item.category,
            "description": item.description,
            "amount": item.amount,
            "date": item.date,
            "has_receipt": item.has_receipt,
            "receipt_number": item.receipt_number,
            "vendor": item.vendor,
            "is_deductible": item.is_deductible,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.expense_items.insert_one(expense_item)
    
    # Calculate balance
    advance = await db.expense_advances.find_one(
        {"request_id": request_id, "status": "disbursed"},
        {"_id": 0}
    )
    
    advance_amount = advance.get("disbursed_amount", 0) if advance else 0
    balance = advance_amount - data.total_spent
    
    verification_status = VerificationStatus.VERIFIED
    if balance > 0:
        verification_status = VerificationStatus.REQUIRES_RETURN
    
    # Update request
    await db.expense_requests.update_one(
        {"request_id": request_id},
        {"$set": {
            "actual_spent": data.total_spent,
            "balance": balance,
            "status": RequestStatus.PENDING_VERIFICATION,
            "verification_status": verification_status,
            "verification_notes": data.notes,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": "Comprobación registrada exitosamente",
        "total_spent": data.total_spent,
        "advance_received": advance_amount,
        "balance": balance,
        "status": verification_status
    }


@router.post("/requests/{request_id}/complete")
async def complete_expense_request(
    request_id: str,
    payroll_action: str = None,  # "deduct" or "reimburse" or None
    current_user: dict = Depends(get_current_user)
):
    """Complete an expense request and optionally integrate with payroll"""
    if current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden completar solicitudes")
    
    company_id = current_user.get("company_id")
    
    expense_req = await db.expense_requests.find_one(
        {"request_id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not expense_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    balance = expense_req.get("balance", 0)
    employee_id = expense_req.get("employee_id")
    
    # Create payroll integration record if needed
    if payroll_action and balance != 0:
        payroll_record = {
            "record_id": f"pexp_{uuid.uuid4().hex[:8]}",
            "request_id": request_id,
            "company_id": company_id,
            "employee_id": employee_id,
            "type": "deduction" if balance > 0 else "reimbursement",
            "amount": abs(balance),
            "description": f"Viáticos - {expense_req.get('title')}",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payroll_expense_records.insert_one(payroll_record)
    
    await db.expense_requests.update_one(
        {"request_id": request_id},
        {"$set": {
            "status": RequestStatus.COMPLETED,
            "payroll_action": payroll_action,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "completed_by": current_user.get("user_id"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Solicitud completada exitosamente"}


@router.post("/requests/{request_id}/attachments")
async def upload_attachment(
    request_id: str,
    file: UploadFile = File(...),
    category: str = Form("receipt"),
    description: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload an attachment (receipt, invoice) to an expense request"""
    # Validate file type
    ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'application/pdf',
                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     'application/vnd.ms-excel'}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido. Use: JPG, PNG, PDF, Excel")
    
    company_id = current_user.get("company_id")
    
    expense_req = await db.expense_requests.find_one(
        {"request_id": request_id, "company_id": company_id},
        {"_id": 0, "request_id": 1}
    )
    
    if not expense_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Read file content
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="El archivo no puede superar 5MB")
    
    attachment = {
        "attachment_id": f"att_{uuid.uuid4().hex[:8]}",
        "request_id": request_id,
        "company_id": company_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "category": category,
        "description": description,
        "file_data": base64.b64encode(content).decode(),
        "uploaded_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.expense_attachments.insert_one(attachment)
    
    return {
        "message": "Archivo adjuntado exitosamente",
        "attachment_id": attachment["attachment_id"]
    }


@router.get("/requests/{request_id}/attachments/{attachment_id}")
async def get_attachment(
    request_id: str,
    attachment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get attachment file"""
    company_id = current_user.get("company_id")
    
    attachment = await db.expense_attachments.find_one(
        {"attachment_id": attachment_id, "request_id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return attachment


@router.delete("/requests/{request_id}")
async def cancel_expense_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel an expense request"""
    company_id = current_user.get("company_id")
    
    expense_req = await db.expense_requests.find_one(
        {"request_id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not expense_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Only allow cancellation if not completed
    if expense_req["status"] in ["completed"]:
        raise HTTPException(status_code=400, detail="No se puede cancelar una solicitud completada")
    
    # Check ownership or admin
    if expense_req["employee_id"] != current_user.get("employee_id") and current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para cancelar esta solicitud")
    
    await db.expense_requests.update_one(
        {"request_id": request_id},
        {"$set": {
            "status": RequestStatus.CANCELLED,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": current_user.get("user_id"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Solicitud cancelada exitosamente"}


# ==================== REPORTS ====================

@router.get("/reports/summary")
async def get_expenses_summary(
    start_date: str = None,
    end_date: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Get expenses summary report"""
    if current_user.get("role") not in ["admin", "hr_manager", "manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver reportes")
    
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    # Get all requests
    requests = await db.expense_requests.find(query, {"_id": 0}).to_list(1000)
    
    # Calculate totals
    total_requests = len(requests)
    total_estimated = sum(r.get("estimated_budget", 0) for r in requests)
    total_actual = sum(r.get("actual_spent", 0) for r in requests)
    
    # By status
    by_status = {}
    for r in requests:
        status = r.get("status", "unknown")
        if status not in by_status:
            by_status[status] = {"count": 0, "amount": 0}
        by_status[status]["count"] += 1
        by_status[status]["amount"] += r.get("estimated_budget", 0)
    
    # By type
    by_type = {}
    for r in requests:
        exp_type = r.get("expense_type", "other")
        if exp_type not in by_type:
            by_type[exp_type] = {"count": 0, "amount": 0}
        by_type[exp_type]["count"] += 1
        by_type[exp_type]["amount"] += r.get("estimated_budget", 0)
    
    # By department
    by_department = {}
    for r in requests:
        dept = r.get("department", "Sin departamento")
        if dept not in by_department:
            by_department[dept] = {"count": 0, "amount": 0}
        by_department[dept]["count"] += 1
        by_department[dept]["amount"] += r.get("actual_spent", 0) or r.get("estimated_budget", 0)
    
    # Pending advances
    pending_advances = await db.expense_advances.find(
        {"company_id": company_id, "status": {"$in": ["pending", "approved"]}},
        {"_id": 0}
    ).to_list(100)
    
    total_pending_advances = sum(a.get("amount", 0) for a in pending_advances)
    
    return {
        "total_requests": total_requests,
        "total_estimated": round(total_estimated, 2),
        "total_actual": round(total_actual, 2),
        "savings": round(total_estimated - total_actual, 2),
        "by_status": by_status,
        "by_type": by_type,
        "by_department": by_department,
        "pending_advances": {
            "count": len(pending_advances),
            "total_amount": round(total_pending_advances, 2)
        }
    }


@router.get("/reports/payroll-integration")
async def get_payroll_integration_report(
    status: str = "pending",
    current_user: dict = Depends(get_current_user)
):
    """Get pending payroll integrations (deductions/reimbursements)"""
    if current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver este reporte")
    
    company_id = current_user.get("company_id")
    
    records = await db.payroll_expense_records.find(
        {"company_id": company_id, "status": status},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with employee info
    for record in records:
        employee = await db.employees.find_one(
            {"employee_id": record.get("employee_id")},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if employee:
            record["employee_name"] = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
    
    return records
