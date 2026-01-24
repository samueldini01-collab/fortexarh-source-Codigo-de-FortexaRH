"""
Metrics Dashboard Routes - FortexaRH
Provides real-time aggregated metrics from payroll, employees, and other modules
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from typing import Callable, Optional
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/metrics", tags=["Metrics"])
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


@router.get("/dashboard")
async def get_dashboard_metrics(year: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """Get comprehensive dashboard metrics with real data"""
    company_id = current_user.get("company_id")
    
    if not year:
        year = datetime.now().year
    
    # Get employee counts
    total_employees = await db.employees.count_documents({"company_id": company_id, "status": "active"})
    
    # Employees hired this month
    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = await db.employees.count_documents({
        "company_id": company_id,
        "hire_date": {"$gte": first_of_month.strftime("%Y-%m-%d")}
    })
    
    # Employees by department
    dept_pipeline = [
        {"$match": {"company_id": company_id, "status": "active"}},
        {"$group": {"_id": "$department", "count": {"$sum": 1}, "total_salary": {"$sum": "$salary"}}},
        {"$project": {"department": "$_id", "employee_count": "$count", "total_salary": 1, "_id": 0}}
    ]
    departments = await db.employees.aggregate(dept_pipeline).to_list(100)
    
    # Payroll data for the year
    payroll_periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": year},
        {"_id": 0}
    ).to_list(100)
    
    # Calculate monthly payroll trend
    months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    payroll_trend = []
    
    for month_idx in range(1, 13):
        month_periods = [p for p in payroll_periods if p.get("month") == month_idx]
        gross = sum(p.get("total_gross", 0) for p in month_periods)
        net = sum(p.get("total_net", 0) for p in month_periods)
        deductions = gross - net if gross > 0 else 0
        employees = max((p.get("employee_count", 0) for p in month_periods), default=0) if month_periods else 0
        
        payroll_trend.append({
            "month": months[month_idx - 1],
            "month_number": month_idx,
            "gross": round(gross, 2),
            "net": round(net, 2),
            "deductions": round(deductions, 2),
            "employees": employees
        })
    
    # Department costs from payroll entries
    dept_costs_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$lookup": {
            "from": "payroll_periods",
            "localField": "period_id",
            "foreignField": "period_id",
            "as": "period"
        }},
        {"$unwind": {"path": "$period", "preserveNullAndEmptyArrays": True}},
        {"$match": {"period.year": year}},
        {"$group": {
            "_id": "$department",
            "total_cost": {"$sum": "$gross_salary"},
            "employee_count": {"$addToSet": "$employee_id"}
        }},
        {"$project": {
            "name": "$_id",
            "cost": "$total_cost",
            "employees": {"$size": "$employee_count"},
            "_id": 0
        }}
    ]
    department_costs = await db.payroll_entries.aggregate(dept_costs_pipeline).to_list(100)
    
    # If no payroll data, use employee salary data
    if not department_costs or all(d.get("cost", 0) == 0 for d in department_costs):
        department_costs = [
            {"name": d["department"] or "Sin Departamento", "cost": d.get("total_salary", 0), "employees": d["employee_count"]}
            for d in departments if d.get("department")
        ]
    
    # Loan metrics
    active_loans = await db.loans.count_documents({"company_id": company_id, "status": "active"})
    loan_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": "$status",
            "total_amount": {"$sum": "$original_amount"},
            "remaining": {"$sum": "$remaining_balance"},
            "count": {"$sum": 1}
        }}
    ]
    loan_stats = await db.loans.aggregate(loan_pipeline).to_list(10)
    
    total_loaned = sum(l.get("total_amount", 0) for l in loan_stats)
    total_remaining = sum(l.get("remaining", 0) for l in loan_stats if l.get("_id") == "active")
    total_paid = total_loaned - total_remaining
    
    employees_with_loans = await db.loans.distinct("employee_id", {"company_id": company_id, "status": "active"})
    
    # Vacation metrics
    pending_vacations = await db.vacations.count_documents({"company_id": company_id, "status": "pending"})
    
    # Evaluation metrics
    evaluations_this_month = await db.evaluations.count_documents({
        "company_id": company_id,
        "created_at": {"$gte": first_of_month.isoformat()}
    })
    
    # Attendance metrics
    today = now.strftime("%Y-%m-%d")
    attendance_today = await db.attendances.count_documents({
        "company_id": company_id,
        "date": today,
        "check_in": {"$exists": True}
    })
    attendance_rate = round((attendance_today / total_employees * 100), 1) if total_employees > 0 else 0
    
    # Calculate turnover rate (last 12 months)
    year_ago = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    terminated = await db.employees.count_documents({
        "company_id": company_id,
        "status": "terminated",
        "termination_date": {"$gte": year_ago}
    })
    turnover_rate = round((terminated / total_employees * 100), 1) if total_employees > 0 else 0
    
    # Payroll pending approval
    pending_payrolls = await db.payroll_periods.count_documents({
        "company_id": company_id,
        "status": {"$in": ["pending_approval", "calculated"]}
    })
    
    return {
        "year": year,
        "employee_metrics": {
            "total_employees": total_employees,
            "new_this_month": new_this_month,
            "turnover_rate": turnover_rate,
            "departments": departments
        },
        "payroll_trend": payroll_trend,
        "department_costs": department_costs,
        "loan_metrics": {
            "total_active_loans": active_loans,
            "total_loaned": round(total_loaned, 2),
            "total_paid": round(total_paid, 2),
            "total_pending": round(total_remaining, 2),
            "employees_with_loans": len(employees_with_loans)
        },
        "quick_stats": {
            "pending_vacations": pending_vacations,
            "evaluations_this_month": evaluations_this_month,
            "attendance_rate": attendance_rate,
            "pending_payrolls": pending_payrolls
        },
        "last_updated": now.isoformat()
    }


@router.get("/payroll-summary")
async def get_payroll_summary(year: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """Get detailed payroll summary for a year"""
    company_id = current_user.get("company_id")
    
    if not year:
        year = datetime.now().year
    
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": year},
        {"_id": 0}
    ).sort("month", 1).to_list(100)
    
    total_gross = sum(p.get("total_gross", 0) for p in periods)
    total_net = sum(p.get("total_net", 0) for p in periods)
    total_deductions = total_gross - total_net
    
    paid_periods = [p for p in periods if p.get("status") == "paid"]
    pending_periods = [p for p in periods if p.get("status") in ["pending_approval", "approved"]]
    
    return {
        "year": year,
        "total_periods": len(periods),
        "paid_periods": len(paid_periods),
        "pending_periods": len(pending_periods),
        "total_gross": round(total_gross, 2),
        "total_net": round(total_net, 2),
        "total_deductions": round(total_deductions, 2),
        "total_paid": sum(p.get("total_net", 0) for p in paid_periods),
        "periods": periods
    }


@router.get("/employee-stats")
async def get_employee_stats(current_user: dict = Depends(get_current_user)):
    """Get detailed employee statistics"""
    company_id = current_user.get("company_id")
    now = datetime.now(timezone.utc)
    
    # Total counts by status
    status_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_counts = await db.employees.aggregate(status_pipeline).to_list(10)
    
    # Department distribution
    dept_pipeline = [
        {"$match": {"company_id": company_id, "status": "active"}},
        {"$group": {
            "_id": "$department",
            "count": {"$sum": 1},
            "avg_salary": {"$avg": "$salary"},
            "total_salary": {"$sum": "$salary"}
        }},
        {"$sort": {"count": -1}}
    ]
    departments = await db.employees.aggregate(dept_pipeline).to_list(100)
    
    # New hires last 12 months
    months_ago = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    new_hires_pipeline = [
        {"$match": {
            "company_id": company_id,
            "hire_date": {"$gte": months_ago}
        }},
        {"$project": {
            "month": {"$substr": ["$hire_date", 0, 7]}
        }},
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    new_hires = await db.employees.aggregate(new_hires_pipeline).to_list(12)
    
    # Average tenure
    active_employees = await db.employees.find(
        {"company_id": company_id, "status": "active", "hire_date": {"$exists": True}},
        {"_id": 0, "hire_date": 1}
    ).to_list(1000)
    
    total_tenure = 0
    for emp in active_employees:
        try:
            hire = datetime.strptime(emp["hire_date"], "%Y-%m-%d")
            tenure = (now.replace(tzinfo=None) - hire).days / 365
            total_tenure += tenure
        except:
            pass
    
    avg_tenure = round(total_tenure / len(active_employees), 1) if active_employees else 0
    
    return {
        "status_distribution": {s["_id"]: s["count"] for s in status_counts},
        "departments": [
            {
                "department": d["_id"] or "Sin Departamento",
                "employee_count": d["count"],
                "avg_salary": round(d.get("avg_salary", 0), 2),
                "total_salary": round(d.get("total_salary", 0), 2)
            }
            for d in departments
        ],
        "new_hires_trend": new_hires,
        "avg_tenure_years": avg_tenure,
        "total_active": sum(s["count"] for s in status_counts if s["_id"] == "active")
    }
