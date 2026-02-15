"""
Stats Routes - FortexaRH
Handles payroll trend and employee statistics endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/stats", tags=["Stats"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


@router.get("/payroll-trend")
async def get_payroll_trend(year: int = None, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    current_year = year or datetime.now().year

    periods = await db.payroll_periods.find(
        {
            "company_id": company_id,
            "status": "processed",
            "year": current_year
        },
        {"_id": 0}
    ).sort("month", 1).to_list(12)

    months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    trend = []

    for i, month_name in enumerate(months, 1):
        period = next((p for p in periods if p.get("month") == i), None)
        if period:
            trend.append({
                "month": month_name,
                "gross": period.get("totals", {}).get("gross_salary", 0),
                "net": period.get("totals", {}).get("net_salary", 0),
                "deductions": period.get("totals", {}).get("total_deductions", 0),
                "employees": period.get("employee_count", 0)
            })
        else:
            trend.append({"month": month_name, "gross": 0, "net": 0, "deductions": 0, "employees": 0})

    return trend


@router.get("/employees")
async def get_employee_stats(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")

    active = await db.employees.count_documents({"company_id": company_id, "status": "active"})
    inactive = await db.employees.count_documents({"company_id": company_id, "status": "inactive"})

    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = await db.employees.count_documents({
        "company_id": company_id,
        "hire_date": {"$gte": month_start.isoformat()}
    })

    pipeline = [
        {"$match": {"company_id": company_id, "status": "active"}},
        {"$group": {"_id": "$department", "count": {"$sum": 1}}}
    ]
    dept_stats = await db.employees.aggregate(pipeline).to_list(100)

    return {
        "total_active": active,
        "total_inactive": inactive,
        "new_this_month": new_this_month,
        "turnover_rate": round((inactive / (active + inactive) * 100) if (active + inactive) > 0 else 0, 1),
        "by_department": [{"name": d["_id"] or "Sin Departamento", "count": d["count"]} for d in dept_stats]
    }
