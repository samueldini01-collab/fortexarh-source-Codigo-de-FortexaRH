"""
Report Generators - FortexaRH
Data generation functions for each report type.
"""
from datetime import datetime, timezone
from config import db


def format_currency(value):
    """Format value as Dominican Peso"""
    try:
        return f"RD${float(value):,.2f}" if value else "RD$0.00"
    except:
        return "RD$0.00"


def format_date(date_str):
    """Format ISO date string to readable format"""
    if not date_str:
        return "N/A"
    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = date_str
        return dt.strftime("%d/%m/%Y")
    except:
        return str(date_str)[:10] if date_str else "N/A"


def calculate_years_months(start_date):
    """Calculate years and months from a start date"""
    if not start_date:
        return 0, 0
    try:
        if isinstance(start_date, str):
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        else:
            start = start_date
        
        now = datetime.now(timezone.utc)
        diff = now - start.replace(tzinfo=timezone.utc) if start.tzinfo is None else now - start
        years = diff.days // 365
        months = (diff.days % 365) // 30
        return years, months
    except:
        return 0, 0



# ============== DATA GENERATION FUNCTIONS ==============

async def generate_report_data(report_id: str, company_id: str, filters: dict, page: int, page_size: int, sort_by: str = None, sort_order: str = "asc"):
    """Generate data for a specific report"""
    
    # Route to specific generator based on report type
    generators = {
        # Nómina
        "nomina_resumen": generate_nomina_resumen,
        "nomina_detalle_empleado": generate_nomina_detalle,
        "nomina_comparativo": generate_nomina_comparativo,
        "nomina_deducciones": generate_nomina_deducciones,
        "nomina_horas_extras": generate_nomina_horas_extras,
        "nomina_historico": generate_nomina_historico,
        "nomina_costos_departamento": generate_nomina_costos_depto,
        "nomina_proyeccion": generate_nomina_proyeccion,
        # Empleados
        "empleados_listado": generate_empleados_listado,
        "empleados_departamento": generate_empleados_departamento,
        "empleados_antiguedad": generate_empleados_antiguedad,
        "empleados_rotacion": generate_empleados_rotacion,
        "empleados_cumpleanos": generate_empleados_cumpleanos,
        "empleados_contratos": generate_empleados_contratos,
        # Asistencia
        "asistencia_diaria": generate_asistencia_diaria,
        "asistencia_tardanzas": generate_asistencia_tardanzas,
        "asistencia_horas_empleado": generate_asistencia_horas,
        "asistencia_horas_extras": generate_asistencia_extras,
        "asistencia_tendencia": generate_asistencia_tendencia,
        # Vacaciones
        "vacaciones_balance": generate_vacaciones_balance,
        "vacaciones_pendientes": generate_vacaciones_pendientes,
        "vacaciones_historico": generate_vacaciones_historico,
        "vacaciones_calendario": generate_vacaciones_calendario,
        # Evaluaciones
        "evaluaciones_ciclo": generate_evaluaciones_ciclo,
        "evaluaciones_comparativo": generate_evaluaciones_comparativo,
        "evaluaciones_objetivos": generate_evaluaciones_objetivos,
        "evaluaciones_planes": generate_evaluaciones_planes,
        # Financiero
        "financiero_prestamos": generate_financiero_prestamos,
        "financiero_gastos": generate_financiero_gastos,
        "financiero_provisiones": generate_financiero_provisiones,
        "financiero_asientos": generate_financiero_asientos,
        "financiero_dgii": generate_financiero_dgii,
    }
    
    generator = generators.get(report_id)
    if generator:
        return await generator(company_id, filters, page, page_size, sort_by, sort_order)
    
    return {"rows": [], "total_count": 0}


# ============== REPORT GENERATORS ==============

async def generate_nomina_resumen(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate payroll summary report"""
    query = {"company_id": company_id}
    
    if filters.get("period"):
        query["period_id"] = filters["period"]
    if filters.get("department"):
        query["department"] = filters["department"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(1000)
    
    rows = []
    totals = {"base_salary": 0, "bonuses": 0, "deductions": 0, "net_pay": 0}
    
    for entry in entries:
        row = {
            "employee": entry.get("employee_name", ""),
            "department": entry.get("department", ""),
            "base_salary": entry.get("base_salary", 0),
            "bonuses": entry.get("overtime_pay", 0) + entry.get("bonuses", 0),
            "deductions": entry.get("total_deductions", 0),
            "net_pay": entry.get("net_salary", 0)
        }
        rows.append(row)
        totals["base_salary"] += row["base_salary"]
        totals["bonuses"] += row["bonuses"]
        totals["deductions"] += row["deductions"]
        totals["net_pay"] += row["net_pay"]
    
    # Sort
    if sort_by and sort_by in rows[0] if rows else False:
        rows.sort(key=lambda x: x.get(sort_by, 0), reverse=(sort_order == "desc"))
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "rows": rows[start:end],
        "total_count": len(rows),
        "totals": totals
    }


async def generate_nomina_detalle(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate detailed payroll by employee"""
    query = {"company_id": company_id}
    
    if filters.get("employee"):
        query["employee_id"] = filters["employee"]
    if filters.get("period"):
        query["period_id"] = filters["period"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(100)
    
    rows = []
    for entry in entries:
        # Add earnings
        rows.append({"concept": "Salario Base", "type": "Ingreso", "amount": entry.get("base_salary", 0), "percentage": ""})
        if entry.get("overtime_pay", 0) > 0:
            rows.append({"concept": "Horas Extras", "type": "Ingreso", "amount": entry.get("overtime_pay", 0), "percentage": ""})
        if entry.get("bonuses", 0) > 0:
            rows.append({"concept": "Bonificaciones", "type": "Ingreso", "amount": entry.get("bonuses", 0), "percentage": ""})
        
        # Add deductions
        if entry.get("sfs_employee", 0) > 0:
            rows.append({"concept": "SFS (Salud)", "type": "Deducción", "amount": entry.get("sfs_employee", 0), "percentage": "3.04%"})
        if entry.get("afp_employee", 0) > 0:
            rows.append({"concept": "AFP (Pensión)", "type": "Deducción", "amount": entry.get("afp_employee", 0), "percentage": "2.87%"})
        if entry.get("isr", 0) > 0:
            rows.append({"concept": "ISR", "type": "Deducción", "amount": entry.get("isr", 0), "percentage": "Variable"})
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_nomina_comparativo(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate payroll comparison report"""
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("start_date", -1).limit(12).to_list(12)
    
    rows = []
    prev_net = None
    
    for period in reversed(periods):
        entries = await db.payroll_entries.find(
            {"company_id": company_id, "period_id": period["period_id"]},
            {"_id": 0}
        ).to_list(500)
        
        gross = sum(e.get("gross_salary", 0) for e in entries)
        deductions = sum(e.get("total_deductions", 0) for e in entries)
        net = sum(e.get("net_salary", 0) for e in entries)
        
        variation = ((net - prev_net) / prev_net * 100) if prev_net and prev_net > 0 else 0
        
        rows.append({
            "month": period.get("name", period["period_id"]),
            "total_employees": len(entries),
            "gross_pay": gross,
            "deductions": deductions,
            "net_pay": net,
            "variation": f"{variation:+.1f}%" if prev_net else "N/A"
        })
        prev_net = net
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_nomina_deducciones(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate deductions report"""
    query = {"company_id": company_id}
    if filters.get("period"):
        query["period_id"] = filters["period"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    totals = {"sfs": 0, "afp": 0, "isr": 0, "loans": 0, "other": 0, "total": 0}
    
    for e in entries:
        sfs = e.get("sfs_employee", 0)
        afp = e.get("afp_employee", 0)
        isr = e.get("isr", 0)
        loans = e.get("loan_deduction", 0)
        other = e.get("other_deductions", 0)
        total = sfs + afp + isr + loans + other
        
        rows.append({
            "employee": e.get("employee_name", ""),
            "sfs": sfs,
            "afp": afp,
            "isr": isr,
            "loans": loans,
            "other": other,
            "total": total
        })
        
        totals["sfs"] += sfs
        totals["afp"] += afp
        totals["isr"] += isr
        totals["loans"] += loans
        totals["other"] += other
        totals["total"] += total
    
    return {"rows": rows, "total_count": len(rows), "totals": totals}


async def generate_nomina_horas_extras(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate overtime report"""
    query = {"company_id": company_id}
    if filters.get("period"):
        query["period_id"] = filters["period"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for e in entries:
        if e.get("overtime_hours", 0) > 0 or e.get("bonuses", 0) > 0:
            rows.append({
                "employee": e.get("employee_name", ""),
                "regular_hours": e.get("regular_hours", 176),
                "overtime_35": e.get("overtime_hours_35", 0),
                "overtime_100": e.get("overtime_hours_100", 0),
                "bonuses": e.get("bonuses", 0),
                "total_extra": e.get("overtime_pay", 0) + e.get("bonuses", 0)
            })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_nomina_historico(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate payment history for an employee"""
    query = {"company_id": company_id}
    if filters.get("employee"):
        query["employee_id"] = filters["employee"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    rows = []
    for e in entries:
        rows.append({
            "period": e.get("period_name", e.get("period_id", "")),
            "gross_pay": e.get("gross_salary", 0),
            "deductions": e.get("total_deductions", 0),
            "net_pay": e.get("net_salary", 0),
            "payment_date": format_date(e.get("payment_date"))
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_nomina_costos_depto(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate labor costs by department"""
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    dept_data = {}
    total_cost = 0
    
    for emp in employees:
        dept = emp.get("department", "Sin Departamento")
        salary = emp.get("salary", 0)
        
        if dept not in dept_data:
            dept_data[dept] = {"employees": 0, "salaries": 0, "benefits": 0, "taxes": 0}
        
        dept_data[dept]["employees"] += 1
        dept_data[dept]["salaries"] += salary
        dept_data[dept]["benefits"] += salary * 0.08  # Estimate
        dept_data[dept]["taxes"] += salary * 0.18  # Employer contributions
        total_cost += salary * 1.26
    
    rows = []
    for dept, data in dept_data.items():
        dept_total = data["salaries"] + data["benefits"] + data["taxes"]
        rows.append({
            "department": dept,
            "employees": data["employees"],
            "salaries": data["salaries"],
            "benefits": data["benefits"],
            "taxes": data["taxes"],
            "total_cost": dept_total,
            "percentage": f"{(dept_total / total_cost * 100):.1f}%" if total_cost > 0 else "0%"
        })
    
    return {"rows": rows, "total_count": len(rows), "totals": {"total_cost": total_cost}}


async def generate_nomina_proyeccion(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate payroll projection"""
    months_ahead = int(filters.get("months_ahead", 6))
    
    # Get last period total
    last_period = await db.payroll_periods.find_one(
        {"company_id": company_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    base_gross = 0
    base_deductions = 0
    
    if last_period:
        entries = await db.payroll_entries.find(
            {"company_id": company_id, "period_id": last_period["period_id"]},
            {"_id": 0}
        ).to_list(500)
        
        base_gross = sum(e.get("gross_salary", 0) for e in entries)
        base_deductions = sum(e.get("total_deductions", 0) for e in entries)
    
    rows = []
    growth_rate = 0.02  # 2% monthly growth estimate
    
    for i in range(1, months_ahead + 1):
        factor = (1 + growth_rate) ** i
        projected_gross = base_gross * factor
        projected_ded = base_deductions * factor
        
        future_date = datetime.now() + timedelta(days=30*i)
        rows.append({
            "month": future_date.strftime("%B %Y"),
            "projected_gross": projected_gross,
            "projected_deductions": projected_ded,
            "projected_net": projected_gross - projected_ded,
            "confidence": f"{max(95 - i*5, 70)}%"
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_listado(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate employee listing"""
    query = {"company_id": company_id}
    
    if filters.get("status"):
        query["status"] = filters["status"]
    if filters.get("department"):
        query["department"] = filters["department"]
    
    employees = await db.employees.find(query, {"_id": 0}).to_list(1000)
    
    rows = []
    for emp in employees:
        rows.append({
            "cedula": emp.get("cedula", ""),
            "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "department": emp.get("department", ""),
            "position": emp.get("position", ""),
            "hire_date": format_date(emp.get("hire_date")),
            "salary": emp.get("salary", 0),
            "status": emp.get("status", "active")
        })
    
    # Sort
    if sort_by:
        rows.sort(key=lambda x: x.get(sort_by, ""), reverse=(sort_order == "desc"))
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_departamento(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate employees by department report"""
    employees = await db.employees.find({"company_id": company_id}, {"_id": 0}).to_list(500)
    
    dept_data = {}
    for emp in employees:
        dept = emp.get("department", "Sin Departamento")
        status = emp.get("status", "active")
        salary = emp.get("salary", 0)
        
        if dept not in dept_data:
            dept_data[dept] = {"total": 0, "active": 0, "inactive": 0, "salaries": []}
        
        dept_data[dept]["total"] += 1
        if status == "active":
            dept_data[dept]["active"] += 1
        else:
            dept_data[dept]["inactive"] += 1
        dept_data[dept]["salaries"].append(salary)
    
    rows = []
    for dept, data in dept_data.items():
        avg_salary = sum(data["salaries"]) / len(data["salaries"]) if data["salaries"] else 0
        rows.append({
            "department": dept,
            "total": data["total"],
            "active": data["active"],
            "inactive": data["inactive"],
            "avg_salary": avg_salary,
            "total_cost": sum(data["salaries"])
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_antiguedad(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate employee tenure report"""
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for emp in employees:
        years, months = calculate_years_months(emp.get("hire_date"))
        vacation_days = min(14 + years, 18)  # Dominican law
        
        rows.append({
            "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "department": emp.get("department", ""),
            "hire_date": format_date(emp.get("hire_date")),
            "years": years,
            "months": months,
            "vacation_days": vacation_days
        })
    
    # Sort by years desc
    rows.sort(key=lambda x: (x["years"], x["months"]), reverse=True)
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_rotacion(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate employee rotation report"""
    # This would need historical data - using mock data for now
    rows = []
    months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
    
    for month in months:
        rows.append({
            "month": month,
            "hires": 2,
            "terminations": 1,
            "rotation_rate": "5.2%",
            "avg_tenure": "2.3 años"
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_cumpleanos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate birthday report"""
    target_month = int(filters.get("month", datetime.now().month))
    
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for emp in employees:
        birth_date = emp.get("birth_date")
        if birth_date:
            try:
                if isinstance(birth_date, str):
                    bd = datetime.fromisoformat(birth_date.replace("Z", "+00:00"))
                else:
                    bd = birth_date
                
                if bd.month == target_month:
                    years, _ = calculate_years_months(emp.get("hire_date"))
                    age = datetime.now().year - bd.year
                    
                    rows.append({
                        "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                        "department": emp.get("department", ""),
                        "birth_date": format_date(birth_date),
                        "age": age,
                        "years_service": years
                    })
            except:
                pass
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_contratos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate expiring contracts report"""
    days_ahead = int(filters.get("days_ahead", 30))
    cutoff = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for emp in employees:
        contract_end = emp.get("contract_end_date")
        if contract_end:
            try:
                if isinstance(contract_end, str):
                    end_date = datetime.fromisoformat(contract_end.replace("Z", "+00:00"))
                else:
                    end_date = contract_end
                
                if end_date <= cutoff:
                    days_remaining = (end_date - datetime.now(timezone.utc)).days
                    rows.append({
                        "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                        "department": emp.get("department", ""),
                        "contract_type": emp.get("contract_type", "Indefinido"),
                        "start_date": format_date(emp.get("hire_date")),
                        "end_date": format_date(contract_end),
                        "days_remaining": max(0, days_remaining)
                    })
            except:
                pass
    
    rows.sort(key=lambda x: x["days_remaining"])
    return {"rows": rows, "total_count": len(rows)}


# Asistencia generators
async def generate_asistencia_diaria(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate daily attendance report"""
    date = filters.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    attendances = await db.attendances.find(
        {"company_id": company_id, "date": date},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for att in attendances:
        rows.append({
            "name": att.get("employee_name", ""),
            "department": att.get("department", ""),
            "shift": att.get("shift", "Regular"),
            "check_in": att.get("check_in", "-"),
            "check_out": att.get("check_out", "-"),
            "hours": att.get("hours_worked", 0),
            "status": att.get("status", "present")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_asistencia_tardanzas(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate tardiness report"""
    attendances = await db.attendances.find(
        {"company_id": company_id, "status": {"$in": ["late", "absent"]}},
        {"_id": 0}
    ).sort("date", -1).to_list(500)
    
    rows = []
    for att in attendances:
        rows.append({
            "name": att.get("employee_name", ""),
            "date": att.get("date", ""),
            "expected": "08:00",
            "actual": att.get("check_in", "-"),
            "delay_minutes": att.get("delay_minutes", 0),
            "type": "Tardanza" if att.get("status") == "late" else "Ausencia",
            "justified": "Sí" if att.get("justified") else "No"
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_asistencia_horas(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate hours worked report"""
    attendances = await db.attendances.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Aggregate by employee
    emp_data = {}
    for att in attendances:
        emp_name = att.get("employee_name", "")
        if emp_name not in emp_data:
            emp_data[emp_name] = {"regular": 0, "overtime": 0, "absences": 0}
        
        emp_data[emp_name]["regular"] += att.get("hours_worked", 0)
        emp_data[emp_name]["overtime"] += att.get("overtime_hours", 0)
        if att.get("status") == "absent":
            emp_data[emp_name]["absences"] += 1
    
    rows = []
    for name, data in emp_data.items():
        total = data["regular"] + data["overtime"]
        efficiency = (data["regular"] / 176 * 100) if data["regular"] > 0 else 0
        rows.append({
            "name": name,
            "regular_hours": data["regular"],
            "overtime": data["overtime"],
            "absences": data["absences"],
            "total_hours": total,
            "efficiency": f"{efficiency:.1f}%"
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_asistencia_extras(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate overtime hours report"""
    attendances = await db.attendances.find(
        {"company_id": company_id, "overtime_hours": {"$gt": 0}},
        {"_id": 0}
    ).to_list(500)
    
    # Aggregate
    emp_data = {}
    for att in attendances:
        emp_name = att.get("employee_name", "")
        dept = att.get("department", "")
        
        if emp_name not in emp_data:
            emp_data[emp_name] = {"department": dept, "ot_35": 0, "ot_100": 0}
        
        emp_data[emp_name]["ot_35"] += att.get("overtime_35", 0)
        emp_data[emp_name]["ot_100"] += att.get("overtime_100", 0)
    
    rows = []
    for name, data in emp_data.items():
        total_ot = data["ot_35"] + data["ot_100"]
        estimated_cost = data["ot_35"] * 150 + data["ot_100"] * 200  # Rough estimate
        rows.append({
            "name": name,
            "department": data["department"],
            "ot_35": data["ot_35"],
            "ot_100": data["ot_100"],
            "total_ot": total_ot,
            "estimated_cost": estimated_cost
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_asistencia_tendencia(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate attendance trend report"""
    rows = []
    months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
    
    for month in months:
        rows.append({
            "month": month,
            "attendance_rate": "94.5%",
            "punctuality_rate": "89.2%",
            "absence_rate": "5.5%",
            "overtime_avg": "12.3 hrs"
        })
    
    return {"rows": rows, "total_count": len(rows)}


# Vacaciones generators
async def generate_vacaciones_balance(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate vacation balance report"""
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for emp in employees:
        years, _ = calculate_years_months(emp.get("hire_date"))
        accrued = min(14 + years, 18)
        used = emp.get("vacation_days_used", 0)
        pending = emp.get("vacation_days_pending", 0)
        
        rows.append({
            "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "department": emp.get("department", ""),
            "hire_date": format_date(emp.get("hire_date")),
            "accrued": accrued,
            "used": used,
            "pending": pending,
            "available": accrued - used - pending
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_vacaciones_pendientes(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate pending vacation requests report"""
    vacations = await db.vacations.find(
        {"company_id": company_id, "status": "pending"},
        {"_id": 0}
    ).to_list(100)
    
    rows = []
    for vac in vacations:
        rows.append({
            "name": vac.get("employee_name", ""),
            "type": vac.get("leave_type", "vacation"),
            "start_date": format_date(vac.get("start_date")),
            "end_date": format_date(vac.get("end_date")),
            "days": vac.get("days_requested", 0),
            "status": vac.get("status", "pending"),
            "requested_at": format_date(vac.get("created_at"))
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_vacaciones_historico(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate vacation history report"""
    vacations = await db.vacations.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    rows = []
    for vac in vacations:
        rows.append({
            "name": vac.get("employee_name", ""),
            "type": vac.get("leave_type", "vacation"),
            "start_date": format_date(vac.get("start_date")),
            "end_date": format_date(vac.get("end_date")),
            "days": vac.get("days_requested", 0),
            "approved_by": vac.get("approved_by", "-"),
            "status": vac.get("status", "")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_vacaciones_calendario(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate absence calendar report"""
    vacations = await db.vacations.find(
        {"company_id": company_id, "status": "approved"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for vac in vacations:
        rows.append({
            "date": f"{format_date(vac.get('start_date'))} - {format_date(vac.get('end_date'))}",
            "employee": vac.get("employee_name", ""),
            "department": vac.get("department", ""),
            "type": vac.get("leave_type", "vacation"),
            "status": vac.get("status", "")
        })
    
    return {"rows": rows, "total_count": len(rows)}


# Evaluaciones generators
async def generate_evaluaciones_ciclo(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate evaluation cycle report"""
    query = {"company_id": company_id}
    if filters.get("cycle"):
        query["cycle_id"] = filters["cycle"]
    
    evaluations = await db.evaluations.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for ev in evaluations:
        rows.append({
            "name": ev.get("employee_name", ""),
            "department": ev.get("department", ""),
            "evaluator": ev.get("evaluator_name", ""),
            "score": ev.get("overall_score", 0),
            "rating": ev.get("rating", ""),
            "status": ev.get("status", ""),
            "date": format_date(ev.get("created_at"))
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_evaluaciones_comparativo(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate evaluation comparison report"""
    query = {"company_id": company_id}
    if filters.get("employee"):
        query["employee_id"] = filters["employee"]
    
    evaluations = await db.evaluations.find(query, {"_id": 0}).sort("created_at", -1).to_list(10)
    
    rows = []
    prev_score = None
    for ev in reversed(evaluations):
        score = ev.get("overall_score", 0)
        variation = ((score - prev_score) / prev_score * 100) if prev_score else 0
        
        rows.append({
            "period": ev.get("cycle_name", ""),
            "score": score,
            "rating": ev.get("rating", ""),
            "strengths": ", ".join(ev.get("strengths", [])[:2]),
            "areas_improvement": ", ".join(ev.get("areas_improvement", [])[:2]),
            "variation": f"{variation:+.1f}%" if prev_score else "N/A"
        })
        prev_score = score
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_evaluaciones_objetivos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate objectives/KPIs report"""
    objectives = await db.objectives.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for obj in objectives:
        target = obj.get("target_value", 100)
        current = obj.get("current_value", 0)
        progress = (current / target * 100) if target > 0 else 0
        
        rows.append({
            "employee": obj.get("employee_name", ""),
            "objective": obj.get("title", ""),
            "target": target,
            "current": current,
            "progress": f"{progress:.1f}%",
            "due_date": format_date(obj.get("due_date")),
            "status": obj.get("status", "")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_evaluaciones_planes(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate improvement plans report"""
    plans = await db.improvement_plans.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for plan in plans:
        rows.append({
            "employee": plan.get("employee_name", ""),
            "plan": plan.get("title", ""),
            "actions": len(plan.get("actions", [])),
            "progress": f"{plan.get('progress', 0)}%",
            "supervisor": plan.get("supervisor_name", ""),
            "due_date": format_date(plan.get("due_date"))
        })
    
    return {"rows": rows, "total_count": len(rows)}


# Financiero generators
async def generate_financiero_prestamos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate loans report"""
    query = {"company_id": company_id}
    if filters.get("status"):
        query["status"] = filters["status"]
    
    loans = await db.loans.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for loan in loans:
        amount = loan.get("amount", 0)
        paid = loan.get("total_paid", 0)
        remaining = amount - paid
        
        rows.append({
            "employee": loan.get("employee_name", ""),
            "amount": amount,
            "installments": loan.get("installments", 0),
            "paid": paid,
            "remaining": remaining,
            "monthly": loan.get("monthly_payment", 0),
            "status": loan.get("status", "")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_financiero_gastos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate expenses report"""
    query = {"company_id": company_id}
    if filters.get("status"):
        query["status"] = filters["status"]
    
    expenses = await db.expense_requests.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for exp in expenses:
        rows.append({
            "employee": exp.get("employee_name", ""),
            "date": format_date(exp.get("date")),
            "type": exp.get("expense_type", ""),
            "description": exp.get("description", ""),
            "amount": exp.get("amount", 0),
            "status": exp.get("status", ""),
            "approved_by": exp.get("approved_by", "-")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_financiero_provisiones(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate provisions report"""
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    totals = {"vacation_prov": 0, "severance_prov": 0, "notice_prov": 0, "total": 0}
    
    for emp in employees:
        salary = emp.get("salary", 0)
        years, months = calculate_years_months(emp.get("hire_date"))
        
        # Dominican law calculations
        vacation_prov = (salary / 23.83) * min(14 + years, 18) / 12
        severance_prov = salary * min(years, 20) / 12 if years >= 1 else 0
        notice_prov = salary * (7 if years < 3 else (14 if years < 6 else 28)) / 365 / 12
        total = vacation_prov + severance_prov + notice_prov
        
        rows.append({
            "employee": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "salary": salary,
            "vacation_prov": vacation_prov,
            "severance_prov": severance_prov,
            "notice_prov": notice_prov,
            "total": total
        })
        
        totals["vacation_prov"] += vacation_prov
        totals["severance_prov"] += severance_prov
        totals["notice_prov"] += notice_prov
        totals["total"] += total
    
    return {"rows": rows, "total_count": len(rows), "totals": totals}


async def generate_financiero_asientos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate journal entries report"""
    entries = await db.journal_entries.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("date", -1).to_list(500)
    
    rows = []
    for entry in entries:
        for line in entry.get("lines", []):
            rows.append({
                "date": format_date(entry.get("date")),
                "account": line.get("account_code", ""),
                "description": line.get("description", entry.get("description", "")),
                "debit": line.get("debit", 0),
                "credit": line.get("credit", 0),
                "reference": entry.get("reference", "")
            })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_financiero_dgii(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate DGII report (TSS)"""
    query = {"company_id": company_id}
    if filters.get("period"):
        query["period_id"] = filters["period"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for e in entries:
        rows.append({
            "cedula": e.get("cedula", ""),
            "name": e.get("employee_name", ""),
            "salary": e.get("gross_salary", 0),
            "sfs_employee": e.get("sfs_employee", 0),
            "sfs_employer": e.get("sfs_employer", 0),
            "afp_employee": e.get("afp_employee", 0),
            "afp_employer": e.get("afp_employer", 0),
            "isr": e.get("isr", 0)
        })
    
    return {"rows": rows, "total_count": len(rows)}
