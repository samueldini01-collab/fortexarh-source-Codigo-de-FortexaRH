"""
Liquidación / Severance Calculation - Dominican Republic Labor Code
Art. 80 (Desahucio), Art. 86 (Despido), Voluntary Resignation
Calculates: Preaviso, Cesantía, Vacaciones, Salario Navidad, Proporción Regalía
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from config import db
from utils.auth import get_current_user
import math

router = APIRouter(prefix="/liquidation", tags=["Liquidation"])


class LiquidationRequest(BaseModel):
    employee_id: str
    termination_type: str  # "desahucio", "despido", "renuncia"
    termination_date: Optional[str] = None
    last_salary: Optional[float] = None


def calculate_years_months(hire_date, end_date):
    """Calculate years and months of service"""
    years = end_date.year - hire_date.year
    months = end_date.month - hire_date.month
    if end_date.day < hire_date.day:
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    total_months = years * 12 + months
    return years, months, total_months


def calculate_preaviso(total_months):
    """Art. 76 - Advance notice based on time of service"""
    if total_months < 3:
        return 0  # No preaviso during probation
    elif total_months < 6:
        return 7  # 7 days
    elif total_months < 12:
        return 14  # 14 days
    else:
        return 28  # 28 days


def calculate_cesantia(total_months, daily_salary):
    """Art. 80 - Severance pay (Cesantía/Desahucio)"""
    if total_months < 3:
        return 0
    elif total_months < 6:
        return 6 * daily_salary
    elif total_months < 12:
        return 13 * daily_salary
    elif total_months < 60:  # 1-5 years
        return 21 * daily_salary * math.ceil(total_months / 12)
    else:  # 5+ years
        return 23 * daily_salary * math.ceil(total_months / 12)


def calculate_cesantia_despido(total_months, daily_salary):
    """Art. 86, 95 - Indemnización por despido injustificado"""
    if total_months < 3:
        return 0
    
    # Base: 5 days per year of service
    years = total_months / 12
    days = 5 * math.ceil(years)
    
    # Plus cesantía
    cesantia = calculate_cesantia(total_months, daily_salary)
    indemnizacion = days * daily_salary
    
    return cesantia + indemnizacion


@router.post("/calculate")
async def calculate_liquidation(data: LiquidationRequest, current_user: dict = Depends(get_current_user)):
    """Calculate employee liquidation/severance"""
    company_id = current_user.get("company_id")

    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    # Parse dates
    hire_date_str = employee.get("hire_date")
    if not hire_date_str:
        raise HTTPException(status_code=400, detail="El empleado no tiene fecha de ingreso")

    try:
        hire_date = datetime.strptime(str(hire_date_str)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Fecha de ingreso inválida")

    if data.termination_date:
        try:
            term_date = datetime.strptime(data.termination_date[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            term_date = datetime.now(timezone.utc).date()
    else:
        term_date = datetime.now(timezone.utc).date()

    # Salary
    monthly_salary = data.last_salary or employee.get("salary", 0)
    daily_salary = monthly_salary / 23.83  # DR standard working days per month

    years, months, total_months = calculate_years_months(hire_date, term_date)

    # Calculate components
    preaviso_days = calculate_preaviso(total_months)
    preaviso_amount = preaviso_days * daily_salary

    if data.termination_type == "desahucio":
        # Art. 80 - Employer termination without cause
        cesantia_amount = calculate_cesantia(total_months, daily_salary)
        indemnizacion = 0
    elif data.termination_type == "despido":
        # Art. 86/95 - Unjustified dismissal
        cesantia_amount = calculate_cesantia(total_months, daily_salary)
        indemnizacion = 5 * math.ceil(total_months / 12) * daily_salary
    else:
        # Voluntary resignation - no cesantía/indemnización
        cesantia_amount = 0
        indemnizacion = 0
        preaviso_amount = 0

    # Vacation days owed (proportional)
    vacation_days_per_year = 14  # DR standard
    months_in_year = term_date.month
    proportional_vacation_days = round((vacation_days_per_year / 12) * months_in_year, 1)
    used_vacation = employee.get("vacation_days_used", 0)
    pending_vacation_days = max(0, proportional_vacation_days - used_vacation)
    vacation_amount = pending_vacation_days * daily_salary

    # Christmas salary (Regalía Pascual) - proportional
    months_worked_this_year = term_date.month
    regalia_amount = (monthly_salary / 12) * months_worked_this_year

    # Total
    total = preaviso_amount + cesantia_amount + indemnizacion + vacation_amount + regalia_amount

    result = {
        "employee_id": data.employee_id,
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
        "position": employee.get("position", ""),
        "department": employee.get("department", ""),
        "hire_date": hire_date.isoformat(),
        "termination_date": term_date.isoformat(),
        "termination_type": data.termination_type,
        "monthly_salary": round(monthly_salary, 2),
        "daily_salary": round(daily_salary, 2),
        "years_of_service": years,
        "months_of_service": months,
        "total_months": total_months,
        "breakdown": {
            "preaviso": {
                "days": preaviso_days,
                "amount": round(preaviso_amount, 2),
                "label": "Preaviso (Art. 76)"
            },
            "cesantia": {
                "amount": round(cesantia_amount, 2),
                "label": "Cesantía (Art. 80)" if data.termination_type == "desahucio" else "Cesantía"
            },
            "indemnizacion": {
                "amount": round(indemnizacion, 2),
                "label": "Indemnización (Art. 86/95)"
            },
            "vacaciones": {
                "days": round(pending_vacation_days, 1),
                "amount": round(vacation_amount, 2),
                "label": "Vacaciones Pendientes"
            },
            "regalia": {
                "months": months_worked_this_year,
                "amount": round(regalia_amount, 2),
                "label": "Regalía Pascual (Proporcional)"
            }
        },
        "total": round(total, 2)
    }

    return result


@router.get("/employees")
async def get_employees_for_liquidation(current_user: dict = Depends(get_current_user)):
    """Get active employees for liquidation calculation"""
    company_id = current_user.get("company_id")
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "position": 1, "department": 1, "hire_date": 1, "salary": 1}
    ).to_list(500)
    return employees
