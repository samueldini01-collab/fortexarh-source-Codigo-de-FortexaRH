"""
Dashboard Routes - FortexaRH
Handles dashboard statistics and metrics
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from datetime import datetime, timezone, timedelta
from typing import Optional

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


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
    """Get comprehensive payroll statistics for dashboard"""
    company_id = current_user.get("company_id")
    
    # Get all periods
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get all active employees
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    # Monthly trend (last 12 months)
    paid_periods = [p for p in periods if p.get("status") == "paid"]
    monthly_data = {}
    for p in paid_periods:
        key = f"{p.get('year')}-{p.get('month'):02d}"
        if key not in monthly_data:
            monthly_data[key] = {"month": key, "total_gross": 0, "total_net": 0, "count": 0}
        monthly_data[key]["total_gross"] += p.get("total_gross", 0)
        monthly_data[key]["total_net"] += p.get("total_net", 0)
        monthly_data[key]["count"] += 1
    monthly_trend = sorted(monthly_data.values(), key=lambda x: x["month"])[-12:]
    
    # Department distribution
    dept_distribution = {}
    for emp in employees:
        dept = emp.get("department", "Sin Departamento")
        if dept not in dept_distribution:
            dept_distribution[dept] = {"department": dept, "count": 0, "total_salary": 0}
        dept_distribution[dept]["count"] += 1
        dept_distribution[dept]["total_salary"] += emp.get("salary", emp.get("base_salary", 0))
    
    # Employer cost breakdown (last 6 paid periods)
    total_entries = []
    for p in paid_periods[-6:]:
        entries = await db.payroll_entries.find(
            {"period_id": p["period_id"], "company_id": company_id},
            {"_id": 0}
        ).to_list(500)
        total_entries.extend(entries)
    
    employer_costs = {
        "total_gross_salary": sum(e.get("gross_salary", 0) for e in total_entries),
        "total_net_salary": sum(e.get("net_salary", 0) for e in total_entries),
        "total_sfs_employer": sum(e.get("sfs_employer", 0) for e in total_entries),
        "total_afp_employer": sum(e.get("afp_employer", 0) for e in total_entries),
        "total_srl": sum(e.get("srl_employer", 0) for e in total_entries),
        "total_infotep": sum(e.get("infotep_employer", 0) for e in total_entries),
    }
    employer_costs["total_employer_cost"] = (
        employer_costs["total_gross_salary"] +
        employer_costs["total_sfs_employer"] +
        employer_costs["total_afp_employer"] +
        employer_costs["total_srl"] +
        employer_costs["total_infotep"]
    )
    
    # Top 10 salaries
    top_salaries = sorted(employees, key=lambda x: x.get("salary", x.get("base_salary", 0)), reverse=True)[:10]
    top_salaries_data = [
        {
            "employee_id": e.get("employee_id"),
            "name": f"{e.get('first_name', '')} {e.get('last_name', '')}",
            "department": e.get("department", ""),
            "salary": e.get("salary", e.get("base_salary", 0))
        }
        for e in top_salaries
    ]
    
    # Alerts
    alerts = []
    unpaid_approved = [p for p in periods if p.get("status") == "approved"]
    if unpaid_approved:
        alerts.append({"type": "warning", "key": "unpaidApproved", "count": len(unpaid_approved)})
    incomplete_employees = [e for e in employees if not e.get("document_id") or not e.get("bank_account")]
    if incomplete_employees:
        alerts.append({"type": "info", "key": "incompleteEmployees", "count": len(incomplete_employees)})
    
    # Summary
    summary = {
        "total_employees": len(employees),
        "total_periods": len(periods),
        "paid_periods": len(paid_periods),
        "total_paid_ytd": sum(p.get("total_net", 0) for p in paid_periods if p.get("year") == datetime.now().year),
        "avg_salary": sum(e.get("salary", e.get("base_salary", 0)) for e in employees) / len(employees) if employees else 0
    }
    
    return {
        "summary": summary,
        "monthly_trend": monthly_trend,
        "department_distribution": list(dept_distribution.values()),
        "employer_costs": employer_costs,
        "top_salaries": top_salaries_data,
        "alerts": alerts
    }


@router.get("/currency-summary")
async def get_currency_summary(current_user: dict = Depends(get_current_user)):
    """Get currency distribution summary for dashboard"""
    company_id = current_user.get("company_id")
    
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "status": "paid"},
        {"_id": 0}
    ).to_list(100)
    
    currency_summary = {"DOP": 0, "USD": 0}
    for p in periods:
        currency = p.get("currency", "DOP")
        currency_summary[currency] = currency_summary.get(currency, 0) + p.get("total_net", 0)
    
    return currency_summary
