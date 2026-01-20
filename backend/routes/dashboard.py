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
    
    total_employees = await db.employees.count_documents({"company_id": company_id, "status": "active"})
    
    # Get pending vacations
    pending_vacations = await db.vacations.count_documents({
        "company_id": company_id,
        "status": "pending"
    })
    
    # Get today's attendance
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_attendance = await db.attendances.count_documents({
        "company_id": company_id,
        "date": today,
        "status": "present"
    })
    
    # Get total payroll amount this month
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    payrolls = await db.payrolls.find({
        "company_id": company_id,
        "period": {"$regex": f"^{current_month}"}
    }, {"_id": 0, "total_amount": 1}).to_list(1000)
    
    monthly_payroll = sum(p.get("total_amount", 0) for p in payrolls)
    
    return {
        "total_employees": total_employees,
        "pending_vacations": pending_vacations,
        "today_attendance": today_attendance,
        "attendance_rate": round((today_attendance / total_employees * 100) if total_employees > 0 else 0, 1),
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
