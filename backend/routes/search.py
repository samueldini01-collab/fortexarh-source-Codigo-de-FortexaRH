"""
Global Search Router - FortexaRH
Provides search functionality across all modules
"""

from fastapi import APIRouter, Depends
from typing import Callable

router = APIRouter(tags=["Search"])

# These will be set by init_router
db = None
get_current_user: Callable = None


def init_router(database, auth_dependency: Callable):
    """Initialize the router with database and auth dependency"""
    global db, get_current_user
    db = database
    get_current_user = auth_dependency


@router.get("/search")
async def global_search(q: str, current_user: dict = Depends(lambda: get_current_user)):
    """Global search across employees, payroll, vacations, journal entries, etc."""
    if not db or not get_current_user:
        return {"results": [], "error": "Router not initialized"}
    
    # Re-call with actual dependency
    company_id = current_user.get("company_id")
    results = []
    query_lower = q.lower()
    
    # Search employees
    employees = await db.employees.find(
        {
            "company_id": company_id,
            "$or": [
                {"first_name": {"$regex": q, "$options": "i"}},
                {"last_name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}},
                {"document_number": {"$regex": q, "$options": "i"}},
                {"position": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "position": 1, "department": 1}
    ).limit(5).to_list(5)
    
    for emp in employees:
        results.append({
            "type": "employee",
            "title": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "description": f"{emp.get('position', '')} - {emp.get('department', '')}",
            "href": f"/employees?id={emp.get('employee_id')}"
        })
    
    # Search payroll periods
    payroll_periods = await db.payroll_periods.find(
        {
            "company_id": company_id,
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"period_type": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "period_id": 1, "name": 1, "period_type": 1, "status": 1}
    ).limit(5).to_list(5)
    
    for period in payroll_periods:
        results.append({
            "type": "payroll",
            "title": period.get("name", "Período de nómina"),
            "description": f"{period.get('period_type', '')} - {period.get('status', '')}",
            "href": f"/payroll-v2?period={period.get('period_id')}"
        })
    
    # Search vacations
    vacations = await db.vacations.find(
        {"company_id": company_id},
        {"_id": 0, "vacation_id": 1, "employee_id": 1, "start_date": 1, "end_date": 1, "status": 1}
    ).limit(10).to_list(10)
    
    # Filter by employee name
    for vac in vacations:
        emp = await db.employees.find_one(
            {"employee_id": vac.get("employee_id")},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if emp:
            emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".lower()
            if query_lower in emp_name or query_lower in "vacacion" or query_lower in "vacaciones":
                results.append({
                    "type": "vacation",
                    "title": f"Vacaciones - {emp.get('first_name', '')} {emp.get('last_name', '')}",
                    "description": f"{vac.get('start_date', '')} - {vac.get('end_date', '')} ({vac.get('status', '')})",
                    "href": f"/vacations?id={vac.get('vacation_id')}"
                })
                if len([r for r in results if r['type'] == 'vacation']) >= 3:
                    break
    
    # Search journal entries
    if "asiento" in query_lower or "diario" in query_lower or "contabilidad" in query_lower:
        journals = await db.journal_entries.find(
            {"company_id": company_id},
            {"_id": 0, "entry_id": 1, "description": 1, "entry_date": 1, "total_debit": 1}
        ).sort("entry_date", -1).limit(5).to_list(5)
        
        for entry in journals:
            results.append({
                "type": "journal",
                "title": entry.get("description", "Asiento de diario"),
                "description": f"Fecha: {entry.get('entry_date', '')} - Total: RD$ {entry.get('total_debit', 0):,.2f}",
                "href": f"/accounting?entry={entry.get('entry_id')}"
            })
    
    # Search attendance if query matches
    if "asistencia" in query_lower or "entrada" in query_lower or "salida" in query_lower:
        results.append({
            "type": "navigation",
            "title": "Asistencias",
            "description": "Gestión de asistencias y horarios",
            "href": "/attendance"
        })
    
    # Search loans
    if "prestamo" in query_lower or "préstamo" in query_lower:
        loans = await db.loans.find(
            {"company_id": company_id, "status": "active"},
            {"_id": 0, "loan_id": 1, "employee_id": 1, "amount": 1, "remaining_balance": 1}
        ).limit(5).to_list(5)
        
        for loan in loans:
            emp = await db.employees.find_one({"employee_id": loan.get("employee_id")}, {"_id": 0, "first_name": 1, "last_name": 1})
            emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}" if emp else "Empleado"
            results.append({
                "type": "loan",
                "title": f"Préstamo - {emp_name}",
                "description": f"Monto: RD$ {loan.get('amount', 0):,.2f} - Balance: RD$ {loan.get('remaining_balance', 0):,.2f}",
                "href": f"/loans?id={loan.get('loan_id')}"
            })
    
    return {"results": results[:15]}  # Limit to 15 results
