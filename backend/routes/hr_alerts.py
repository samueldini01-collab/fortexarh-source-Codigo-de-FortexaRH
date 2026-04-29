"""
HR Alerts System - Automatic alerts for:
- Contracts about to expire (30/60/90 days)
- Employees completing probation period
- Work anniversaries (eligible for vacations)
- Employee birthdays coming up
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta
from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/hr-alerts", tags=["HR Alerts"])


@router.get("")
async def get_hr_alerts(current_user: dict = Depends(get_current_user)):
    """Get all active HR alerts for the company"""
    company_id = current_user.get("company_id")
    today = datetime.now(timezone.utc).date()
    alerts = []

    # Get all active employees
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)

    for emp in employees:
        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        emp_id = emp.get("employee_id")

        # 1. PROBATION PERIOD (usually 3 months in DR)
        hire_date_str = emp.get("hire_date")
        if hire_date_str:
            try:
                hire_date = datetime.fromisoformat(str(hire_date_str).replace('Z', '+00:00')).date() if 'T' in str(hire_date_str) else datetime.strptime(str(hire_date_str)[:10], "%Y-%m-%d").date()
                probation_end = hire_date + timedelta(days=90)
                days_to_probation = (probation_end - today).days

                if 0 < days_to_probation <= 15:
                    alerts.append({
                        "type": "probation_ending",
                        "priority": "high",
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "department": emp.get("department", ""),
                        "message": f"Período de prueba termina en {days_to_probation} días",
                        "date": probation_end.isoformat(),
                        "days_remaining": days_to_probation
                    })
                elif days_to_probation == 0:
                    alerts.append({
                        "type": "probation_ending",
                        "priority": "critical",
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "department": emp.get("department", ""),
                        "message": "Período de prueba termina HOY",
                        "date": probation_end.isoformat(),
                        "days_remaining": 0
                    })
            except (ValueError, TypeError):
                pass

        # 2. WORK ANNIVERSARIES (1+ years = eligible for vacations in DR)
        if hire_date_str:
            try:
                hire_date = datetime.fromisoformat(str(hire_date_str).replace('Z', '+00:00')).date() if 'T' in str(hire_date_str) else datetime.strptime(str(hire_date_str)[:10], "%Y-%m-%d").date()
                # Check if anniversary is within next 30 days
                this_year_anniversary = hire_date.replace(year=today.year)
                if this_year_anniversary < today:
                    this_year_anniversary = hire_date.replace(year=today.year + 1)

                days_to_anniversary = (this_year_anniversary - today).days
                years = this_year_anniversary.year - hire_date.year

                if 0 < days_to_anniversary <= 30 and years >= 1:
                    alerts.append({
                        "type": "work_anniversary",
                        "priority": "medium",
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "department": emp.get("department", ""),
                        "message": f"Cumple {years} año(s) en la empresa en {days_to_anniversary} días",
                        "date": this_year_anniversary.isoformat(),
                        "days_remaining": days_to_anniversary,
                        "years": years
                    })
                elif days_to_anniversary == 0 and years >= 1:
                    alerts.append({
                        "type": "work_anniversary",
                        "priority": "medium",
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "department": emp.get("department", ""),
                        "message": f"¡Hoy cumple {years} año(s) en la empresa!",
                        "date": this_year_anniversary.isoformat(),
                        "days_remaining": 0,
                        "years": years
                    })
            except (ValueError, TypeError):
                pass

        # 3. BIRTHDAYS coming up (next 7 days)
        birth_date_str = emp.get("birth_date")
        if birth_date_str:
            try:
                birth_date = datetime.fromisoformat(str(birth_date_str).replace('Z', '+00:00')).date() if 'T' in str(birth_date_str) else datetime.strptime(str(birth_date_str)[:10], "%Y-%m-%d").date()
                this_year_birthday = birth_date.replace(year=today.year)
                if this_year_birthday < today:
                    this_year_birthday = birth_date.replace(year=today.year + 1)

                days_to_birthday = (this_year_birthday - today).days

                if 0 < days_to_birthday <= 7:
                    alerts.append({
                        "type": "birthday",
                        "priority": "low",
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "department": emp.get("department", ""),
                        "message": f"Cumpleaños en {days_to_birthday} día(s)",
                        "date": this_year_birthday.isoformat(),
                        "days_remaining": days_to_birthday
                    })
                elif days_to_birthday == 0:
                    alerts.append({
                        "type": "birthday",
                        "priority": "low",
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "department": emp.get("department", ""),
                        "message": "¡Hoy es su cumpleaños!",
                        "date": this_year_birthday.isoformat(),
                        "days_remaining": 0
                    })
            except (ValueError, TypeError):
                pass

    # 4. CONTRACTS ABOUT TO EXPIRE
    contracts = await db.contracts.find(
        {"company_id": company_id, "status": {"$in": ["active", "signed", "fully_signed"]}},
        {"_id": 0}
    ).to_list(200)

    for contract in contracts:
        end_date_str = contract.get("end_date") or contract.get("expiration_date")
        if not end_date_str:
            continue
        try:
            end_date = datetime.fromisoformat(str(end_date_str).replace('Z', '+00:00')).date() if 'T' in str(end_date_str) else datetime.strptime(str(end_date_str)[:10], "%Y-%m-%d").date()
            days_to_expire = (end_date - today).days

            if days_to_expire <= 0:
                priority = "critical"
                msg = "Contrato VENCIDO"
            elif days_to_expire <= 30:
                priority = "high"
                msg = f"Contrato vence en {days_to_expire} días"
            elif days_to_expire <= 60:
                priority = "medium"
                msg = f"Contrato vence en {days_to_expire} días"
            elif days_to_expire <= 90:
                priority = "low"
                msg = f"Contrato vence en {days_to_expire} días"
            else:
                continue

            # Get employee name
            contract_emp_id = contract.get("employee_id")
            contract_emp = next((e for e in employees if e.get("employee_id") == contract_emp_id), None)
            contract_emp_name = f"{(contract_emp or {}).get('first_name', '')} {(contract_emp or {}).get('last_name', '')}".strip() or "Empleado"

            alerts.append({
                "type": "contract_expiring",
                "priority": priority,
                "employee_id": contract_emp_id,
                "employee_name": contract_emp_name,
                "department": (contract_emp or {}).get("department", ""),
                "message": msg,
                "date": end_date.isoformat(),
                "days_remaining": days_to_expire,
                "contract_id": contract.get("contract_id")
            })
        except (ValueError, TypeError):
            pass

    # Sort by priority then days_remaining
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda x: (priority_order.get(x["priority"], 4), x.get("days_remaining", 999)))

    return {
        "alerts": alerts,
        "summary": {
            "total": len(alerts),
            "critical": len([a for a in alerts if a["priority"] == "critical"]),
            "high": len([a for a in alerts if a["priority"] == "high"]),
            "medium": len([a for a in alerts if a["priority"] == "medium"]),
            "low": len([a for a in alerts if a["priority"] == "low"]),
        }
    }
