"""
Reports Routes - FortexaRH
Handles cost reports by department and other analytics
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from io import BytesIO
import csv

router = APIRouter(prefix="/reports", tags=["Reports"])
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


# ==================== DEPARTMENT COST REPORT ====================

@router.get("/costs-by-department")
async def get_costs_by_department(
    period: Optional[str] = None,  # Format: YYYY-MM
    current_user: dict = Depends(get_current_user)
):
    """
    Get payroll costs breakdown by department
    Returns salary, deductions, and net pay per department
    """
    company_id = current_user.get("company_id")
    
    # Default to current month if no period specified
    if not period:
        today = datetime.now(timezone.utc)
        period = today.strftime("%Y-%m")
    
    # Get all active employees with their departments
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, 
         "department": 1, "salary": 1, "position": 1,
         "sfs_discount": 1, "afp_discount": 1, "isr_discount": 1}
    ).to_list(1000)
    
    # Get payroll entries for the period (if any)
    payroll_entries = await db.payroll_v2.find(
        {"company_id": company_id, "period": period},
        {"_id": 0}
    ).to_list(1000)
    
    # Create lookup for payroll data by employee
    payroll_by_employee = {p.get("employee_id"): p for p in payroll_entries}
    
    # Calculate costs by department
    departments = {}
    company_totals = {
        "total_gross": 0,
        "total_sfs": 0,
        "total_afp": 0,
        "total_isr": 0,
        "total_other_deductions": 0,
        "total_net": 0,
        "employee_count": 0
    }
    
    for emp in employees:
        dept = emp.get("department") or "Sin Departamento"
        salary = emp.get("salary", 0)
        
        # Get payroll data if available, otherwise estimate
        payroll = payroll_by_employee.get(emp["employee_id"])
        
        if payroll:
            gross = payroll.get("gross_salary", salary)
            sfs = payroll.get("sfs_employee", 0)
            afp = payroll.get("afp_employee", 0)
            isr = payroll.get("isr", 0)
            other = payroll.get("other_deductions", 0)
            net = payroll.get("net_salary", gross - sfs - afp - isr - other)
        else:
            # Estimate based on salary and Dominican Republic rates
            gross = salary
            sfs = salary * 0.0304 if emp.get("sfs_discount", True) else 0  # 3.04% SFS employee
            afp = salary * 0.0287 if emp.get("afp_discount", True) else 0  # 2.87% AFP employee
            isr = calculate_isr(salary) if emp.get("isr_discount", True) else 0
            other = 0
            net = gross - sfs - afp - isr
        
        # Initialize department if needed
        if dept not in departments:
            departments[dept] = {
                "department": dept,
                "employee_count": 0,
                "gross_salary": 0,
                "sfs_deduction": 0,
                "afp_deduction": 0,
                "isr_deduction": 0,
                "other_deductions": 0,
                "net_salary": 0,
                "employer_sfs": 0,  # Employer contributions
                "employer_afp": 0,
                "employer_risk": 0,
                "employer_infotep": 0,
                "total_employer_cost": 0,
                "employees": []
            }
        
        # Employer contributions (Dominican Republic rates)
        employer_sfs = salary * 0.0709 if emp.get("sfs_discount", True) else 0  # 7.09%
        employer_afp = salary * 0.0710 if emp.get("afp_discount", True) else 0  # 7.10%
        employer_risk = salary * 0.011  # 1.1% Risk insurance
        employer_infotep = salary * 0.01  # 1% INFOTEP
        
        total_employer = employer_sfs + employer_afp + employer_risk + employer_infotep
        
        # Add to department totals
        departments[dept]["employee_count"] += 1
        departments[dept]["gross_salary"] += gross
        departments[dept]["sfs_deduction"] += sfs
        departments[dept]["afp_deduction"] += afp
        departments[dept]["isr_deduction"] += isr
        departments[dept]["other_deductions"] += other
        departments[dept]["net_salary"] += net
        departments[dept]["employer_sfs"] += employer_sfs
        departments[dept]["employer_afp"] += employer_afp
        departments[dept]["employer_risk"] += employer_risk
        departments[dept]["employer_infotep"] += employer_infotep
        departments[dept]["total_employer_cost"] += total_employer
        
        departments[dept]["employees"].append({
            "employee_id": emp["employee_id"],
            "name": f"{emp['first_name']} {emp['last_name']}",
            "position": emp.get("position", ""),
            "gross_salary": gross,
            "net_salary": net,
            "total_deductions": sfs + afp + isr + other
        })
        
        # Add to company totals
        company_totals["total_gross"] += gross
        company_totals["total_sfs"] += sfs
        company_totals["total_afp"] += afp
        company_totals["total_isr"] += isr
        company_totals["total_other_deductions"] += other
        company_totals["total_net"] += net
        company_totals["employee_count"] += 1
    
    # Calculate total cost including employer contributions
    total_employer_contributions = sum(d["total_employer_cost"] for d in departments.values())
    company_totals["total_employer_contributions"] = total_employer_contributions
    company_totals["grand_total_cost"] = company_totals["total_gross"] + total_employer_contributions
    
    # Sort departments by cost (descending)
    dept_list = sorted(departments.values(), key=lambda x: x["gross_salary"], reverse=True)
    
    # Calculate percentages
    total_gross = company_totals["total_gross"]
    for dept in dept_list:
        dept["percentage_of_total"] = round((dept["gross_salary"] / total_gross * 100), 1) if total_gross > 0 else 0
        dept["total_cost"] = dept["gross_salary"] + dept["total_employer_cost"]
    
    return {
        "period": period,
        "company_id": company_id,
        "departments": dept_list,
        "summary": company_totals,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/costs-by-department/export")
async def export_costs_by_department(
    period: Optional[str] = None,
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    """Export department costs report as CSV"""
    company_id = current_user.get("company_id")
    
    # Get the report data
    if not period:
        today = datetime.now(timezone.utc)
        period = today.strftime("%Y-%m")
    
    # Reuse the main endpoint logic
    report = await get_costs_by_department(period, current_user)
    
    # Create CSV
    output = BytesIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    # Write header
    writer.writerow([
        "Departamento",
        "Empleados",
        "Salario Bruto",
        "SFS Empleado",
        "AFP Empleado",
        "ISR",
        "Otras Deducciones",
        "Salario Neto",
        "SFS Empleador",
        "AFP Empleador",
        "Riesgo Laboral",
        "INFOTEP",
        "Total Costo Empleador",
        "Costo Total",
        "% del Total"
    ])
    
    # Write department rows
    for dept in report["departments"]:
        writer.writerow([
            dept["department"],
            dept["employee_count"],
            f"{dept['gross_salary']:.2f}",
            f"{dept['sfs_deduction']:.2f}",
            f"{dept['afp_deduction']:.2f}",
            f"{dept['isr_deduction']:.2f}",
            f"{dept['other_deductions']:.2f}",
            f"{dept['net_salary']:.2f}",
            f"{dept['employer_sfs']:.2f}",
            f"{dept['employer_afp']:.2f}",
            f"{dept['employer_risk']:.2f}",
            f"{dept['employer_infotep']:.2f}",
            f"{dept['total_employer_cost']:.2f}",
            f"{dept['total_cost']:.2f}",
            f"{dept['percentage_of_total']:.1f}%"
        ])
    
    # Write summary row
    summary = report["summary"]
    writer.writerow([])
    writer.writerow(["TOTALES"])
    writer.writerow([
        "TOTAL EMPRESA",
        summary["employee_count"],
        f"{summary['total_gross']:.2f}",
        f"{summary['total_sfs']:.2f}",
        f"{summary['total_afp']:.2f}",
        f"{summary['total_isr']:.2f}",
        f"{summary['total_other_deductions']:.2f}",
        f"{summary['total_net']:.2f}",
        "", "", "", "",
        f"{summary['total_employer_contributions']:.2f}",
        f"{summary['grand_total_cost']:.2f}",
        "100%"
    ])
    
    output.seek(0)
    content = output.getvalue().decode('utf-8')
    
    # Return as downloadable file
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=costos_departamento_{period}.csv"
        }
    )


@router.get("/cost-trends")
async def get_cost_trends(
    months: int = 6,
    current_user: dict = Depends(get_current_user)
):
    """Get cost trends over time"""
    company_id = current_user.get("company_id")
    today = datetime.now(timezone.utc)
    
    trends = []
    
    for i in range(months - 1, -1, -1):
        # Calculate the month
        month_date = today - timedelta(days=30 * i)
        period = month_date.strftime("%Y-%m")
        
        # Get payroll data for this period
        payroll_entries = await db.payroll_v2.find(
            {"company_id": company_id, "period": period},
            {"_id": 0, "gross_salary": 1, "net_salary": 1}
        ).to_list(1000)
        
        if payroll_entries:
            total_gross = sum(p.get("gross_salary", 0) for p in payroll_entries)
            total_net = sum(p.get("net_salary", 0) for p in payroll_entries)
            employee_count = len(payroll_entries)
        else:
            # Use current employee data as estimate
            employees = await db.employees.find(
                {"company_id": company_id, "status": "active"},
                {"_id": 0, "salary": 1}
            ).to_list(1000)
            total_gross = sum(e.get("salary", 0) for e in employees)
            total_net = total_gross * 0.85  # Approximate
            employee_count = len(employees)
        
        trends.append({
            "period": period,
            "month_name": month_date.strftime("%B %Y"),
            "total_gross": total_gross,
            "total_net": total_net,
            "employee_count": employee_count,
            "average_salary": total_gross / employee_count if employee_count > 0 else 0
        })
    
    return {
        "trends": trends,
        "period_count": months
    }


@router.get("/department-comparison")
async def get_department_comparison(
    current_user: dict = Depends(get_current_user)
):
    """Get comparison metrics between departments"""
    company_id = current_user.get("company_id")
    
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0, "department": 1, "salary": 1, "hire_date": 1}
    ).to_list(1000)
    
    departments = {}
    
    for emp in employees:
        dept = emp.get("department") or "Sin Departamento"
        salary = emp.get("salary", 0)
        
        if dept not in departments:
            departments[dept] = {
                "department": dept,
                "salaries": [],
                "count": 0
            }
        
        departments[dept]["salaries"].append(salary)
        departments[dept]["count"] += 1
    
    # Calculate statistics for each department
    result = []
    for dept_name, dept_data in departments.items():
        salaries = dept_data["salaries"]
        if salaries:
            result.append({
                "department": dept_name,
                "employee_count": dept_data["count"],
                "total_salary": sum(salaries),
                "average_salary": sum(salaries) / len(salaries),
                "min_salary": min(salaries),
                "max_salary": max(salaries),
                "salary_range": max(salaries) - min(salaries)
            })
    
    # Sort by total salary descending
    result.sort(key=lambda x: x["total_salary"], reverse=True)
    
    return result


def calculate_isr(monthly_salary: float) -> float:
    """Calculate ISR (Dominican Republic Income Tax)"""
    annual = monthly_salary * 12
    
    # 2024 ISR brackets (annual)
    if annual <= 416220:
        isr_annual = 0
    elif annual <= 624329:
        isr_annual = (annual - 416220) * 0.15
    elif annual <= 867123:
        isr_annual = 31216 + (annual - 624329) * 0.20
    else:
        isr_annual = 79775 + (annual - 867123) * 0.25
    
    return isr_annual / 12  # Return monthly ISR
