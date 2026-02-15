"""
Employee Loans Routes for FortexaRH
Module for managing employee loans, payments, and deductions
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import logging

router = APIRouter(prefix="/loans", tags=["Employee Loans"])

# These will be injected from server.py
db = None
_get_current_user_func = None

logger = logging.getLogger(__name__)


# ===================== PYDANTIC MODELS =====================
from models.finance import LoanCreate, LoanPaymentCreate


# ===================== ROUTER INITIALIZATION =====================

def init_router(database, auth_dependency):
    """Initialize router with database and auth dependency"""
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request):
    """Wrapper to call the auth dependency"""
    from fastapi.security import HTTPBearer
    security = HTTPBearer(auto_error=False)
    credentials = await security(request)
    return await _get_current_user_func(request, credentials)


# ===================== LOAN ENDPOINTS =====================

@router.get("")
async def get_loans(
    request: Request,
    status: Optional[str] = None,
    employee_id: Optional[str] = None
):
    """Get all loans for the company"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    if status:
        query["status"] = status
    if employee_id:
        query["employee_id"] = employee_id
    
    loans = await db.loans.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Enrich with employee info
    for loan in loans:
        employee = await db.employees.find_one(
            {"employee_id": loan.get("employee_id"), "company_id": company_id},
            {"_id": 0, "first_name": 1, "last_name": 1, "document_number": 1, "position": 1}
        )
        if employee:
            loan["employee_name"] = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
            loan["employee_document"] = employee.get("document_number", "")
            loan["employee_position"] = employee.get("position", "")
    
    return loans


@router.get("/summary")
async def get_loans_summary(request: Request):
    """Get loans summary for dashboard"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    # Get all active loans
    active_loans = await db.loans.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    total_loaned = sum(loan.get("amount", 0) for loan in active_loans)
    total_paid = sum(loan.get("total_paid", 0) for loan in active_loans)
    total_pending = total_loaned - total_paid
    
    # Count by status
    all_loans = await db.loans.find(
        {"company_id": company_id},
        {"_id": 0, "status": 1}
    ).to_list(1000)
    
    status_counts = {}
    for loan in all_loans:
        status = loan.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total_active_loans": len(active_loans),
        "total_loaned": round(total_loaned, 2),
        "total_paid": round(total_paid, 2),
        "total_pending": round(total_pending, 2),
        "status_counts": status_counts,
        "employees_with_loans": len(set(loan.get("employee_id") for loan in active_loans))
    }


@router.post("")
async def create_loan(data: LoanCreate, request: Request):
    """Create a new loan for an employee"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    # Verify employee exists
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Check if employee has existing active loan
    existing_loan = await db.loans.find_one({
        "employee_id": data.employee_id,
        "company_id": company_id,
        "status": "active"
    })
    if existing_loan:
        raise HTTPException(status_code=400, detail="El empleado ya tiene un préstamo activo")
    
    # Calculate monthly payment
    if data.interest_rate > 0:
        # With interest (amortization formula)
        monthly_rate = data.interest_rate / 100 / 12
        monthly_payment = data.amount * (monthly_rate * (1 + monthly_rate) ** data.term_months) / ((1 + monthly_rate) ** data.term_months - 1)
        total_to_pay = monthly_payment * data.term_months
    else:
        # No interest (simple division)
        monthly_payment = data.amount / data.term_months
        total_to_pay = data.amount
    
    loan_id = f"loan_{uuid.uuid4().hex[:12]}"
    
    # Generate payment schedule
    schedule = []
    start = datetime.strptime(data.start_date, "%Y-%m-%d")
    remaining = data.amount
    
    for i in range(data.term_months):
        payment_date = start + timedelta(days=30 * (i + 1))
        
        if data.interest_rate > 0:
            interest_payment = remaining * (data.interest_rate / 100 / 12)
            principal_payment = monthly_payment - interest_payment
        else:
            interest_payment = 0
            principal_payment = monthly_payment
        
        remaining = max(0, remaining - principal_payment)
        
        schedule.append({
            "installment_number": i + 1,
            "due_date": payment_date.strftime("%Y-%m-%d"),
            "amount": round(monthly_payment, 2),
            "principal": round(principal_payment, 2),
            "interest": round(interest_payment, 2),
            "remaining_balance": round(remaining, 2),
            "status": "pending",
            "paid_date": None,
            "paid_amount": 0
        })
    
    loan = {
        "loan_id": loan_id,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "amount": data.amount,
        "currency": data.currency,
        "interest_rate": data.interest_rate,
        "term_months": data.term_months,
        "monthly_payment": round(monthly_payment, 2),
        "total_to_pay": round(total_to_pay, 2),
        "total_paid": 0,
        "remaining_balance": data.amount,
        "start_date": data.start_date,
        "description": data.description,
        "deduct_from_payroll": data.deduct_from_payroll,
        "status": "active",
        "payment_schedule": schedule,
        "payments": [],
        "created_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.loans.insert_one(loan)
    
    return {
        "loan_id": loan_id,
        "monthly_payment": round(monthly_payment, 2),
        "total_to_pay": round(total_to_pay, 2),
        "message": "Préstamo creado exitosamente"
    }


@router.get("/{loan_id}")
async def get_loan(loan_id: str, request: Request):
    """Get loan details"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    loan = await db.loans.find_one(
        {"loan_id": loan_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    # Get employee info
    employee = await db.employees.find_one(
        {"employee_id": loan.get("employee_id"), "company_id": company_id},
        {"_id": 0, "first_name": 1, "last_name": 1, "document_number": 1, "position": 1, "department": 1}
    )
    
    if employee:
        loan["employee"] = {
            "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
            "document": employee.get("document_number", ""),
            "position": employee.get("position", ""),
            "department": employee.get("department", "")
        }
    
    return loan


@router.post("/{loan_id}/payment")
async def register_loan_payment(loan_id: str, data: LoanPaymentCreate, request: Request):
    """Register a payment for a loan"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    loan = await db.loans.find_one(
        {"loan_id": loan_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    if loan.get("status") != "active":
        raise HTTPException(status_code=400, detail="El préstamo no está activo")
    
    payment_id = f"pay_{uuid.uuid4().hex[:8]}"
    new_total_paid = loan.get("total_paid", 0) + data.amount
    new_remaining = loan.get("amount", 0) - new_total_paid
    
    payment = {
        "payment_id": payment_id,
        "amount": data.amount,
        "payment_date": data.payment_date,
        "payment_type": data.payment_type,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update next pending installment
    schedule = loan.get("payment_schedule", [])
    for installment in schedule:
        if installment.get("status") == "pending":
            installment["status"] = "paid"
            installment["paid_date"] = data.payment_date
            installment["paid_amount"] = data.amount
            break
    
    # Check if loan is fully paid
    new_status = "paid" if new_remaining <= 0 else "active"
    
    await db.loans.update_one(
        {"loan_id": loan_id, "company_id": company_id},
        {
            "$set": {
                "total_paid": round(new_total_paid, 2),
                "remaining_balance": round(max(0, new_remaining), 2),
                "status": new_status,
                "payment_schedule": schedule,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$push": {"payments": payment}
        }
    )
    
    return {
        "payment_id": payment_id,
        "total_paid": round(new_total_paid, 2),
        "remaining_balance": round(max(0, new_remaining), 2),
        "status": new_status,
        "message": "Pago registrado exitosamente"
    }


@router.delete("/{loan_id}")
async def delete_loan(loan_id: str, request: Request):
    """Delete a loan (only if no payments made)"""
    current_user = await get_current_user(request)
    company_id = current_user.get("company_id")
    
    loan = await db.loans.find_one(
        {"loan_id": loan_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    if loan.get("total_paid", 0) > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar un préstamo con pagos registrados")
    
    await db.loans.delete_one({"loan_id": loan_id, "company_id": company_id})
    
    return {"message": "Préstamo eliminado"}


# ===================== EMPLOYEE-SPECIFIC LOAN ENDPOINT =====================

async def get_employee_loans_internal(employee_id: str, company_id: str):
    """Get all loans for a specific employee (internal function)"""
    loans = await db.loans.find(
        {"employee_id": employee_id, "company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Calculate pending deduction for current period
    active_loans = [l for l in loans if l.get("status") == "active" and l.get("deduct_from_payroll")]
    pending_deduction = sum(l.get("monthly_payment", 0) for l in active_loans)
    
    return {
        "loans": loans,
        "pending_deduction": round(pending_deduction, 2),
        "total_balance": sum(l.get("remaining_balance", 0) for l in active_loans)
    }
