"""
Dashboard Routes - FortexaRH
Handles dashboard statistics and metrics
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from datetime import datetime, timezone, timedelta
from typing import Optional

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials = Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)



@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Empleados Activos
    total_employees = await db.employees.count_documents({"company_id": company_id, "status": "active"})
    
    # Nóminas Pendientes (payroll entries not approved/paid this month)
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    pending_payrolls = await db.payroll_v2.count_documents({
        "company_id": company_id,
        "period": current_month,
        "status": {"$in": ["draft", "pending", "processing"]}
    })
    # If no payroll_v2 entries, count employees without payroll this month
    if pending_payrolls == 0:
        processed_employees = await db.payroll_v2.distinct("employee_id", {
            "company_id": company_id,
            "period": current_month,
            "status": {"$in": ["approved", "paid"]}
        })
        pending_payrolls = total_employees - len(processed_employees)
        if pending_payrolls < 0:
            pending_payrolls = 0
    
    # Presentes Hoy
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_attendance = await db.attendances.count_documents({
        "company_id": company_id,
        "date": today,
        "status": "present"
    })
    
    # Vacaciones Pendientes
    pending_vacations = await db.vacations.count_documents({
        "company_id": company_id,
        "status": "pending"
    })
    
    # Vacantes Abiertas
    open_jobs = await db.jobs.count_documents({
        "company_id": company_id,
        "status": "open"
    })
    
    # Nuevos Candidatos (últimos 7 días)
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_candidates = await db.candidates.count_documents({
        "company_id": company_id,
        "created_at": {"$gte": seven_days_ago}
    })
    # If no date filter works, just count pending candidates
    if new_candidates == 0:
        new_candidates = await db.candidates.count_documents({
            "company_id": company_id,
            "stage": {"$in": ["applied", "screening", "new"]}
        })
    
    # Get total payroll amount this month
    payrolls = await db.payroll_v2.find({
        "company_id": company_id,
        "period": current_month
    }, {"_id": 0, "gross_salary": 1, "net_salary": 1}).to_list(1000)
    
    monthly_payroll = sum(p.get("gross_salary", 0) for p in payrolls)
    
    # Attendance rate
    attendance_rate = round((today_attendance / total_employees * 100) if total_employees > 0 else 0, 1)
    
    return {
        "total_employees": total_employees,
        "pending_payrolls": pending_payrolls,
        "today_attendance": today_attendance,
        "attendance_rate": attendance_rate,
        "pending_vacations": pending_vacations,
        "open_jobs": open_jobs,
        "new_candidates": new_candidates,
        "monthly_payroll": monthly_payroll
    }


@router.get("/payroll-stats")
async def get_payroll_stats(current_user: dict = Depends(get_current_user)):
    """Get payroll statistics for dashboard widgets"""
    company_id = current_user.get("company_id")
    
    # Get current month
    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")
    
    # Get monthly totals for the last 6 months
    months_data = []
    for i in range(6):
        month_date = now - timedelta(days=30 * i)
        month_str = month_date.strftime("%Y-%m")
        
        # Get payroll entries for this month
        payroll_entries = await db.payroll_entries.find({
            "company_id": company_id,
            "period_id": {"$regex": f".*_{month_str.replace('-', '')}"}
        }, {"_id": 0, "net_pay": 1}).to_list(10000)
        
        total = sum(e.get("net_pay", 0) for e in payroll_entries)
        months_data.append({
            "month": month_str,
            "total": total
        })
    
    # Get by department
    employees = await db.employees.find({
        "company_id": company_id,
        "status": "active"
    }, {"_id": 0, "department": 1, "salary": 1}).to_list(1000)
    
    dept_totals = {}
    for emp in employees:
        dept = emp.get("department", "Sin Departamento")
        if dept not in dept_totals:
            dept_totals[dept] = 0
        dept_totals[dept] += emp.get("salary", 0)
    
    by_department = [{"department": k, "total": v} for k, v in dept_totals.items()]
    by_department.sort(key=lambda x: x["total"], reverse=True)
    
    return {
        "monthly_trend": months_data[::-1],
        "by_department": by_department[:5]
    }


@router.get("/currency-summary")
async def get_currency_summary(current_user: dict = Depends(get_current_user)):
    """Get currency distribution summary for dashboard"""
    company_id = current_user.get("company_id")
    
    # Get all employees
    employees = await db.employees.find({
        "company_id": company_id,
        "status": "active"
    }, {"_id": 0, "salary": 1, "currency": 1}).to_list(1000)
    
    currency_totals = {}
    for emp in employees:
        currency = emp.get("currency", "DOP")
        salary = emp.get("salary", 0)
        if currency not in currency_totals:
            currency_totals[currency] = {"count": 0, "total": 0}
        currency_totals[currency]["count"] += 1
        currency_totals[currency]["total"] += salary
    
    return {
        "by_currency": [
            {"currency": k, "count": v["count"], "total": v["total"]}
            for k, v in currency_totals.items()
        ]
    }
