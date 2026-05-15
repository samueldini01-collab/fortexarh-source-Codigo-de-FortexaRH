"""
Payroll Export Routes - FortexaRH
Export endpoints for payroll data: Excel, TSS, DGII (IR3, IR4, IR6, IR17, IR13)
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from datetime import datetime, timezone
import uuid
import io
import csv

from utils.payroll_constants import (
    SFS_EMPLOYEE_RATE, AFP_EMPLOYEE_RATE,
    SFS_EMPLOYER_RATE, AFP_EMPLOYER_RATE, SRL_EMPLOYER_RATE, INFOTEP_EMPLOYER_RATE,
    ISR_OBREROS_RATE, calculate_isr_monthly
)

from routes.country_config import COUNTRY_PROFILES


async def _require_dr_company(db_ref, company_id: str, report_name: str):
    """Guard: raise 400 if company's country is not DR."""
    company = await db_ref.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    country_code = (company or {}).get("country", "DO")
    if country_code != "DO":
        profile = COUNTRY_PROFILES.get(country_code, {})
        raise HTTPException(
            status_code=400,
            detail=f"{report_name} es específico de República Dominicana (TSS/SUIR+). "
                   f"Su empresa está configurada como {profile.get('name', country_code)}. "
                   f"Este formato de archivo solo se admite para empresas DO."
        )

router = APIRouter(prefix="/payroll", tags=["Payroll Exports"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


# ===================== EXPORT ENDPOINTS =====================

@router.get("/periods/{period_id}/export/excel")
async def export_period_excel(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export payroll period to Excel format - Returns JSON for frontend processing.

    Columns are emitted as a parallel ``[{key, label}, ...]`` list so the
    frontend can build the CSV/XLSX without hard-coded column knowledge.
    Headers use full human-readable names (matches the Payroll Sheet UI),
    and every income/deduction novelty code gets its own column with the
    sum of its novelties per employee.
    """
    company_id = current_user.get("company_id")

    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")

    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).sort("employee_name", 1).to_list(1000)

    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1}
    )
    company_name = company.get("name", "Sin Nombre") if company else "Sin Nombre"

    # Income/Deduction novelty code catalogs — kept in sync with
    # /app/frontend/src/components/payroll/payrollColumns.jsx (INCOME_CODES / DEDUCTION_CODES).
    INCOME_CODES = [
        ("COM", "Comisiones"), ("VIA", "Viáticos"), ("INC", "Incentivos"),
        ("HED", "Horas Extras Diurnas"), ("HEN", "Horas Extras Nocturnas"),
        ("HEFS", "Horas Extras Fin de Semana"), ("HEFER", "Horas Extras Feriados"),
        ("BON", "Bonificación"), ("REG", "Regalía Pascual"), ("VAC", "Vacaciones"),
        ("OTROING", "Otros Ingresos"),
    ]
    DEDUCTION_CODES = [
        ("ANTIC", "Anticipo"), ("COOP", "Cooperativa"), ("SEG", "Seguro Adicional"),
        ("PENS", "Pensión Alimenticia"), ("EMB", "Embargo"), ("TARD", "Tardanzas"),
        ("AUS", "Ausencias"), ("OTROSD", "Otros Descuentos"),
    ]

    def _sum_code(entry: dict, code: str, novelty_type: str) -> float:
        base = entry.get("base_salary", 0) or 0
        total = 0.0
        for n in entry.get("novelties", []) or []:
            if n.get("code") == code and n.get("novelty_type") == novelty_type:
                amt = n.get("amount", 0) or 0
                total += (base * amt / 100) if n.get("is_percentage") else amt
        return round(total, 2)

    # Column descriptors — order matches the Payroll Sheet defaults
    columns = [
        {"key": "no", "label": "No"},
        {"key": "cedula", "label": "Cédula"},
        {"key": "nombre", "label": "Empleado"},
        {"key": "cargo", "label": "Cargo"},
        {"key": "departamento", "label": "Departamento"},
        {"key": "salario_base", "label": "Salario Base"},
        # Legacy aggregated income (kept for backwards-compat columns)
        {"key": "commissions", "label": "Comisiones"},
        {"key": "bonuses", "label": "Bonificaciones"},
        {"key": "overtime_total", "label": "Horas Extras"},
        # Income novelty codes (each its own column with FULL name)
        *[{"key": f"income_{c}", "label": f"{c} - {n}"} for c, n in INCOME_CODES],
        {"key": "other_income", "label": "Otros Ingresos (legacy)"},
        {"key": "income_novelties_total", "label": "Otros Ingresos (novedades)"},
        {"key": "gross_salary", "label": "Bruto"},
        {"key": "sfs", "label": "Seguro Familiar de Salud"},
        {"key": "afp", "label": "Fondo de Pensiones"},
        {"key": "isr", "label": "ISR"},
        # Deduction novelty codes (each its own column with FULL name)
        *[{"key": f"ded_{c}", "label": f"{c} - {n}"} for c, n in DEDUCTION_CODES],
        {"key": "deduction_novelties_total", "label": "Otras Deducciones (novedades)"},
        {"key": "additional_deductions_total", "label": "Deducciones Adicionales"},
        {"key": "loan_deduction", "label": "Préstamos"},
        {"key": "total_deductions", "label": "Total Deducciones"},
        {"key": "net_salary", "label": "Neto a Pagar"},
    ]

    rows: list[dict] = []
    totals: dict[str, float] = {c["key"]: 0.0 for c in columns if c["key"] not in ("no", "cedula", "nombre", "cargo", "departamento")}

    for idx, entry in enumerate(entries, 1):
        he_diurnas = entry.get("overtime_day_amount", 0) or 0
        he_nocturnas = entry.get("overtime_night_amount", 0) or 0
        he_finsemana = entry.get("overtime_weekend_amount", 0) or 0
        he_feriados = entry.get("overtime_holiday_amount", 0) or 0
        # Horas Extras unificada: legacy + novedades HED/HEN/HEFS/HEFER
        overtime_total = round(
            he_diurnas + he_nocturnas + he_finsemana + he_feriados
            + sum(_sum_code(entry, c, "income") for c in ("HED", "HEN", "HEFS", "HEFER")),
            2,
        )

        row = {
            "no": idx,
            "cedula": entry.get("employee_document") or "",
            "nombre": entry.get("employee_name") or "",
            "cargo": entry.get("position", ""),
            "departamento": entry.get("department", ""),
            "salario_base": round(entry.get("base_salary", 0) or 0, 2),
            "commissions": round(entry.get("commissions", 0) or 0, 2),
            "bonuses": round(entry.get("bonuses", 0) or 0, 2),
            "overtime_total": overtime_total,
            "other_income": round(entry.get("other_income", 0) or 0, 2),
            "income_novelties_total": round(entry.get("total_income_novelties", 0) or 0, 2),
            "gross_salary": round(entry.get("gross_salary", 0) or 0, 2),
            "sfs": round(entry.get("sfs_employee", 0) or 0, 2),
            "afp": round(entry.get("afp_employee", 0) or 0, 2),
            "isr": round(entry.get("isr", 0) or 0, 2),
            "deduction_novelties_total": round(entry.get("total_deduction_novelties", 0) or 0, 2),
            "additional_deductions_total": round(entry.get("total_additional_deductions", 0) or 0, 2),
            "loan_deduction": round(entry.get("loan_deduction", 0) or 0, 2),
            "total_deductions": round(entry.get("total_deductions", 0) or 0, 2),
            "net_salary": round(entry.get("net_salary", 0) or 0, 2),
        }
        for code, _name in INCOME_CODES:
            row[f"income_{code}"] = _sum_code(entry, code, "income")
        for code, _name in DEDUCTION_CODES:
            row[f"ded_{code}"] = _sum_code(entry, code, "deduction")

        rows.append(row)
        for k in totals:
            totals[k] += float(row.get(k, 0) or 0)

    totals = {k: round(v, 2) for k, v in totals.items()}

    return {
        "company_name": company_name,
        "period": {
            "period_id": period.get("period_id"),
            "description": period.get("description", ""),
            "start_date": period.get("start_date", ""),
            "end_date": period.get("end_date", ""),
            "period_type": period.get("period_type", ""),
            "status": period.get("status", "")
        },
        "columns": columns,
        "rows": rows,
        "totals": totals,
        "employee_count": len(entries),
    }


@router.get("/periods/{period_id}/export/tss-autodeterminacion")
async def export_tss_autodeterminacion(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export TSS Autodetermination file"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    rnc = company.get("rnc", "") if company else ""
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow([
        "RNC_PATRONO", "CEDULA", "TIPO_CEDULA", "NSS",
        "NOMBRE", "APELLIDO1", "APELLIDO2",
        "SEXO", "FECHA_NACIMIENTO", "SALARIO_COTIZABLE",
        "APORTE_VOLUNTARIO", "SFS_EMPLEADOR", "SFS_EMPLEADO",
        "AFP_EMPLEADOR", "AFP_EMPLEADO", "SRL", "INFOTEP"
    ])
    
    for entry in entries:
        cedula = (entry.get("employee_document") or "").replace("-", "")
        name_parts = (entry.get("employee_name") or "").split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name1 = name_parts[-1] if len(name_parts) > 1 else ""
        last_name2 = name_parts[-2] if len(name_parts) > 2 else ""
        
        writer.writerow([
            (rnc or "").replace("-", ""),
            cedula,
            "C",
            "",
            first_name,
            last_name1,
            last_name2,
            "M",
            "",
            entry.get("gross_salary", 0),
            0,
            entry.get("sfs_employer", 0),
            entry.get("sfs_employee", 0),
            entry.get("afp_employer", 0),
            entry.get("afp_employee", 0),
            entry.get("srl_employer", 0),
            entry.get("infotep_employer", 0)
        ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=TSS_Autodeterminacion_{period_id}.xls"}
    )


@router.get("/periods/{period_id}/export/tss-novedades")
async def export_tss_novedades(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export TSS Novedades file"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    rnc = company.get("rnc", "") if company else ""
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow([
        "RNC_PATRONO", "CEDULA", "TIPO_NOVEDAD", "FECHA_NOVEDAD",
        "MOTIVO", "OBSERVACIONES"
    ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=TSS_Novedades_{period_id}.xls"}
    )


@router.get("/periods/{period_id}/export/ir3")
async def export_ir3(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export IR-3 report"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    total_isr = sum(e.get("isr", 0) for e in entries)
    total_gross = sum(e.get("gross_salary", 0) for e in entries)
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow(["DECLARACIÓN IR-3 - RETENCIONES DE ASALARIADOS"])
    writer.writerow([])
    writer.writerow(["Empresa:", company.get("name", "") if company else ""])
    writer.writerow(["RNC:", company.get("rnc", "") if company else ""])
    writer.writerow(["Período:", f"{period.get('month', '')}/{period.get('year', '')}"])
    writer.writerow([])
    writer.writerow(["RESUMEN"])
    writer.writerow(["Total Empleados:", len(entries)])
    writer.writerow(["Total Salarios Brutos:", f"RD$ {total_gross:,.2f}"])
    writer.writerow(["Total ISR Retenido:", f"RD$ {total_isr:,.2f}"])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=IR3_{period_id}.xls"}
    )


@router.get("/periods/{period_id}/export/ir4")
async def export_ir4(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export IR-4 report (detail)"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow([
        "Cédula", "Nombre", "Salario Bruto", "ISR Retenido"
    ])
    
    for entry in entries:
        if entry.get("isr", 0) > 0:
            writer.writerow([
                entry.get("employee_document") or "",
                entry.get("employee_name") or "",
                entry.get("gross_salary", 0),
                entry.get("isr", 0)
            ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=IR4_{period_id}.xls"}
    )


@router.get("/periods/{period_id}/export/ir17")
async def export_ir17(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export IR-17 report - Otras Retenciones y Retribuciones Complementarias"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    company_name = company.get("name", "") if company else ""
    company_rnc = company.get("rnc", "") if company else ""
    
    ir17_codes = {
        1: {"name": "ALQUILERES", "rate": 10.00, "total": 0},
        2: {"name": "HONORARIOS POR SERVICIOS INDEPENDIENTES", "rate": 10.00, "total": 0},
        3: {"name": "PREMIOS (Ley 253-12)", "rate": 25.00, "total": 0},
        4: {"name": "TRANSFERENCIA DE TÍTULO Y PROPIEDADES", "rate": 2.00, "total": 0},
        5: {"name": "DIVIDENDOS (Ley 253-12)", "rate": 10.00, "total": 0},
        6: {"name": "INTERESES A PERSONAS JURÍDICAS NO RESIDENTES (Ley 253-12)", "rate": 10.00, "total": 0},
        7: {"name": "INTERESES A PERSONAS JURÍDICAS NO RESIDENTES (Ley 57-2007)", "rate": 5.00, "total": 0},
        8: {"name": "INTERESES A PERSONAS FÍSICAS NO RESIDENTES (Ley 253-12)", "rate": 10.00, "total": 0},
        9: {"name": "INTERESES A PERSONAS FÍSICAS NO RESIDENTES (Leyes 57-2007 y 253-12)", "rate": 5.00, "total": 0},
        10: {"name": "REMESAS AL EXTERIOR (Ley 253-12)", "rate": 27.00, "total": 0},
        11: {"name": "INTERESES PAGADOS POR ENTIDADES NO FINANCIERAS A PF RESIDENTES", "rate": 10.00, "total": 0},
        12: {"name": "PAGOS A PROVEEDORES DEL ESTADO (Ley 253-12)", "rate": 5.00, "total": 0},
        13: {"name": "JUEGOS TELEFÓNICOS (Norma 08-2011)", "rate": 5.00, "total": 0},
        14: {"name": "GANANCIA DE CAPITAL (Norma 07-2011)", "rate": 1.00, "total": 0},
        15: {"name": "JUEGOS VÍA INTERNET (Ley 139-11, Art. 7)", "rate": 10.00, "total": 0},
        16: {"name": "OTRAS RENTAS (Ley 11-92, Art. 309 Lit. f)", "rate": 10.00, "total": 0},
        17: {"name": "OTRAS RENTAS (Decreto 139-98, Art. 70 Lit. a y b)", "rate": 2.00, "total": 0},
        18: {"name": "OTRAS RETENCIONES - OBREROS CONSTRUCCIÓN (Norma 07-2007)", "rate": 2.00, "total": 0},
        19: {"name": "INTERESES POR ENTIDADES FINANCIERAS A PJ RESIDENTES (Norma 13-2011)", "rate": 1.00, "total": 0},
        20: {"name": "INTERESES POR ENTIDADES FINANCIERAS A PF RESIDENTES (Ley 253-12)", "rate": 10.00, "total": 0},
        21: {"name": "ADQUISICIÓN BIENES - GANADERÍA BOVINA (Norma 04-25)", "rate": 1.00, "total": 0},
    }
    
    expenses = await db.expenses.find(
        {
            "company_id": company_id,
            "status": "approved",
            "expense_date": {
                "$gte": f"{period.get('year')}-{period.get('month'):02d}-01",
                "$lte": f"{period.get('year')}-{period.get('month'):02d}-31"
            }
        },
        {"_id": 0}
    ).to_list(500)
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id, "payroll_type": "OBREROS_NG"},
        {"_id": 0}
    ).to_list(1000)
    
    for entry in entries:
        isr = entry.get("isr", 0)
        if isr > 0:
            ir17_codes[18]["total"] += entry.get("gross_salary", 0)
    
    for expense in expenses:
        category = expense.get("category", "").lower()
        amount = expense.get("amount", 0)
        code = expense.get("ir17_code", 0)
        
        if code and code in ir17_codes:
            ir17_codes[code]["total"] += amount
        elif "alquiler" in category or "renta" in category:
            ir17_codes[1]["total"] += amount
        elif "honorario" in category or "servicio" in category:
            ir17_codes[2]["total"] += amount
        elif "premio" in category:
            ir17_codes[3]["total"] += amount
        elif "dividendo" in category:
            ir17_codes[5]["total"] += amount
        elif "interes" in category:
            ir17_codes[11]["total"] += amount
        else:
            ir17_codes[16]["total"] += amount
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow(["FORMULARIO IR-17 - DECLARACIÓN JURADA DE OTRAS RETENCIONES"])
    writer.writerow([])
    writer.writerow(["RNC/Cédula del Agente de Retención:", company_rnc])
    writer.writerow(["Nombre/Razón Social:", company_name])
    writer.writerow(["Período Fiscal:", f"{period.get('month'):02d}/{period.get('year')}"])
    writer.writerow([])
    
    writer.writerow(["DETALLE DE LA RENTA NETA IMPONIBLE O PÉRDIDA FISCAL"])
    writer.writerow([])
    writer.writerow(["No.", "CONCEPTO", "TASA %", "MONTO IMPONIBLE (RD$)", "IMPUESTO RETENIDO (RD$)"])
    
    total_imponible = 0
    total_retenido = 0
    
    for code, data in ir17_codes.items():
        monto = data["total"]
        tasa = data["rate"]
        retencion = round(monto * tasa / 100, 2)
        
        writer.writerow([
            f"{code}.",
            data["name"],
            f"{tasa:.2f}%",
            f"{monto:,.2f}" if monto > 0 else "-",
            f"{retencion:,.2f}" if retencion > 0 else "-"
        ])
        
        total_imponible += monto
        total_retenido += retencion
    
    writer.writerow([])
    writer.writerow(["", "TOTAL MONTO IMPONIBLE", "", f"{total_imponible:,.2f}", ""])
    writer.writerow(["", "TOTAL IMPUESTO A PAGAR", "", "", f"{total_retenido:,.2f}"])
    
    content = "\ufeff" + output.getvalue()
    return Response(
        content=content.encode("utf-8"),
        media_type="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=IR17_{period.get('month'):02d}_{period.get('year')}.xls"}
    )


@router.get("/periods/{period_id}/export/ir6")
async def export_ir6(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export IR-6 report - Anexo de Otras Retenciones del IR-17"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    company_name = company.get("name", "") if company else ""
    company_rnc = company.get("rnc", "") if company else ""
    
    concept_codes = {
        1: "ALQUILERES",
        2: "HONORARIOS",
        3: "PREMIOS",
        4: "TRANSFERENCIAS",
        5: "DIVIDENDOS",
        6: "INTERESES PJ NO RES",
        7: "INTERESES PJ NO RES 5%",
        8: "INTERESES PF NO RES",
        9: "INTERESES PF NO RES 5%",
        10: "REMESAS EXTERIOR",
        11: "INTERESES PF RES",
        12: "PROVEEDORES ESTADO",
        13: "JUEGOS TEL",
        14: "GANANCIA CAPITAL",
        15: "JUEGOS INTERNET",
        16: "OTRAS RENTAS",
        17: "OTRAS RENTAS 2%",
        18: "OBREROS CONST.",
        19: "INTERESES PJ FIN",
        20: "INTERESES PF FIN",
        21: "GANADERÍA",
    }
    
    expenses = await db.expenses.find(
        {
            "company_id": company_id,
            "status": "approved",
            "expense_date": {
                "$gte": f"{period.get('year')}-{period.get('month'):02d}-01",
                "$lte": f"{period.get('year')}-{period.get('month'):02d}-31"
            }
        },
        {"_id": 0}
    ).to_list(500)
    
    obreros_entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id, "payroll_type": "OBREROS_NG"},
        {"_id": 0}
    ).to_list(1000)
    
    suppliers = await db.suppliers.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(500)
    supplier_lookup = {s.get("supplier_id"): s for s in suppliers}
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow(["ANEXO IR-6 - DETALLE DE OTRAS RETENCIONES"])
    writer.writerow([])
    writer.writerow(["RNC/Cédula Agente Retención:", company_rnc])
    writer.writerow(["Nombre/Razón Social:", company_name])
    writer.writerow(["Período:", f"{period.get('month'):02d}/{period.get('year')}"])
    writer.writerow([])
    
    writer.writerow([
        "FECHA",
        "MES",
        "DÍA", 
        "FORMA DE PAGO",
        "NOMBRE DEL BENEFICIADO",
        "RNC/CÉDULA O PASAPORTE",
        "DIRECCIÓN",
        "CÓDIGO CONCEPTO",
        "MONTO DEL PAGO (RD$)",
        "MONTO SUJETO A RETENCIÓN (RD$)",
        "TASA",
        "IMPUESTO RETENIDO (RD$)"
    ])
    
    total_pago = 0
    total_sujeto = 0
    total_retenido = 0
    row_count = 0
    
    for expense in expenses:
        amount = expense.get("amount", 0)
        if amount <= 0:
            continue
        
        category = expense.get("category", "").lower()
        code = expense.get("ir17_code", 16)
        
        if "alquiler" in category:
            code, rate = 1, 10.00
        elif "honorario" in category or "servicio" in category:
            code, rate = 2, 10.00
        elif "premio" in category:
            code, rate = 3, 25.00
        elif "dividendo" in category:
            code, rate = 5, 10.00
        elif "interes" in category:
            code, rate = 11, 10.00
        else:
            code, rate = 16, 10.00
        
        retencion = round(amount * rate / 100, 2)
        
        expense_date = expense.get("expense_date", "")
        mes = expense_date[5:7] if len(expense_date) >= 7 else ""
        dia = expense_date[8:10] if len(expense_date) >= 10 else ""
        
        supplier_id = expense.get("supplier_id")
        supplier = supplier_lookup.get(supplier_id, {})
        
        writer.writerow([
            expense_date,
            mes,
            dia,
            expense.get("payment_method", "TRANSFERENCIA"),
            expense.get("vendor_name", supplier.get("name", "")),
            expense.get("vendor_rnc", supplier.get("rnc", "")),
            supplier.get("address", ""),
            code,
            f"{amount:,.2f}",
            f"{amount:,.2f}",
            f"{rate:.2f}%",
            f"{retencion:,.2f}"
        ])
        
        total_pago += amount
        total_sujeto += amount
        total_retenido += retencion
        row_count += 1
    
    for entry in obreros_entries:
        gross = entry.get("gross_salary", 0)
        isr = entry.get("isr", 0)
        if isr <= 0:
            continue
        
        writer.writerow([
            "",
            f"{period.get('month'):02d}",
            "15",
            "NÓMINA",
            entry.get("employee_name") or "",
            entry.get("employee_document") or "",
            "",
            18,
            f"{gross:,.2f}",
            f"{gross:,.2f}",
            "2.00%",
            f"{isr:,.2f}"
        ])
        
        total_pago += gross
        total_sujeto += gross
        total_retenido += isr
        row_count += 1
    
    writer.writerow([])
    writer.writerow([
        "TOTALES",
        "",
        "",
        "",
        f"{row_count} registros",
        "",
        "",
        "",
        f"{total_pago:,.2f}",
        f"{total_sujeto:,.2f}",
        "",
        f"{total_retenido:,.2f}"
    ])
    
    content = "\ufeff" + output.getvalue()
    return Response(
        content=content.encode("utf-8"),
        media_type="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=IR6_Anexo_{period.get('month'):02d}_{period.get('year')}.xls"}
    )


@router.get("/periods/{period_id}/dgii-preview")
async def preview_dgii_reports(period_id: str, current_user: dict = Depends(get_current_user)):
    """Preview all DGII reports data for a period"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    total_isr_asalariados = sum(e.get("isr", 0) for e in entries)
    total_gross = sum(e.get("gross_salary", 0) for e in entries)
    employees_with_isr = len([e for e in entries if e.get("isr", 0) > 0])
    
    expenses = await db.expenses.find(
        {
            "company_id": company_id,
            "status": "approved",
            "expense_date": {
                "$gte": f"{period.get('year')}-{period.get('month'):02d}-01",
                "$lte": f"{period.get('year')}-{period.get('month'):02d}-31"
            }
        },
        {"_id": 0}
    ).to_list(500)
    
    total_otras_retenciones = 0
    for expense in expenses:
        amount = expense.get("amount", 0)
        category = expense.get("category", "").lower()
        if "premio" in category:
            total_otras_retenciones += amount * 0.15
        else:
            total_otras_retenciones += amount * 0.10
    
    total_retrib = sum(e.get("bonuses", 0) + e.get("other_income", 0) for e in entries)
    retrib_retencion = total_retrib * 0.27
    
    return {
        "period": {
            "period_id": period_id,
            "month": period.get("month"),
            "year": period.get("year"),
            "description": period.get("description", "")
        },
        "company": {
            "name": company.get("name", "") if company else "",
            "rnc": company.get("rnc", "") if company else ""
        },
        "ir3": {
            "name": "IR-3 - Retenciones de Asalariados",
            "total_employees": len(entries),
            "employees_with_isr": employees_with_isr,
            "total_gross": round(total_gross, 2),
            "total_isr": round(total_isr_asalariados, 2)
        },
        "ir17": {
            "name": "IR-17 - Otras Retenciones",
            "total_otras_retenciones": round(total_otras_retenciones, 2),
            "total_retrib_complementarias": round(retrib_retencion, 2),
            "total_ir17": round(total_otras_retenciones + retrib_retencion, 2),
            "expense_count": len(expenses)
        },
        "ir6": {
            "name": "IR-6 - Anexo Detalle Retenciones",
            "record_count": len(expenses),
            "total_retenido": round(total_otras_retenciones, 2)
        },
        "total_a_pagar_dgii": round(total_isr_asalariados + total_otras_retenciones + retrib_retencion, 2)
    }


@router.get("/annual-report/ir13/{year}")
async def export_ir13(year: int, current_user: dict = Depends(get_current_user)):
    """Export IR-13 annual report"""
    company_id = current_user.get("company_id")
    
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": year},
        {"_id": 0}
    ).to_list(100)
    
    if not periods:
        raise HTTPException(status_code=404, detail="No hay períodos para este año")
    
    all_entries = []
    for period in periods:
        entries = await db.payroll_entries.find(
            {"period_id": period["period_id"], "company_id": company_id},
            {"_id": 0}
        ).to_list(1000)
        all_entries.extend(entries)
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    
    employee_totals = {}
    for entry in all_entries:
        emp_id = entry.get("employee_id")
        if emp_id not in employee_totals:
            employee_totals[emp_id] = {
                "document": entry.get("employee_document") or "",
                "name": entry.get("employee_name") or "",
                "total_gross": 0,
                "total_isr": 0
            }
        employee_totals[emp_id]["total_gross"] += entry.get("gross_salary", 0)
        employee_totals[emp_id]["total_isr"] += entry.get("isr", 0)
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow(["DECLARACIÓN IR-13 - RETENCIONES ANUALES"])
    writer.writerow([])
    writer.writerow(["Empresa:", company.get("name", "") if company else ""])
    writer.writerow(["RNC:", company.get("rnc", "") if company else ""])
    writer.writerow(["Año Fiscal:", year])
    writer.writerow([])
    writer.writerow(["Cédula", "Nombre", "Total Ingresos", "Total ISR Retenido"])
    
    for emp in employee_totals.values():
        writer.writerow([
            emp["document"],
            emp["name"],
            f"{emp['total_gross']:,.2f}",
            f"{emp['total_isr']:,.2f}"
        ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=IR13_{year}.xls"}
    )


# ===================== TSS REPORT GENERATION =====================

@router.get("/periods/{period_id}/tss-report")
async def generate_tss_report(period_id: str, current_user: dict = Depends(get_current_user)):
    """Generate TSS report in TXT format for SUIR+ system submission - Dominican Republic only"""
    company_id = current_user.get("company_id")
    await _require_dr_company(db, company_id, "Reporte TSS (SUIR+)")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    payroll_type = period.get("payroll_type", "REG")
    if payroll_type == "OBREROS_NG":
        raise HTTPException(
            status_code=400, 
            detail="El reporte TSS no aplica para nóminas de Obreros NG 07/2007. Este tipo de nómina solo requiere ISR 2%."
        )
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    company_rnc = company.get("rnc", "000000000") if company else "000000000"
    company_name = company.get("name", "EMPRESA") if company else "EMPRESA"
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    if not entries:
        raise HTTPException(status_code=400, detail="No hay empleados en este período de nómina")
    
    year = period.get("year", datetime.now().year)
    month = period.get("month", datetime.now().month)
    period_str = f"{month:02d}{year}"
    
    lines = []
    
    header = f"E|{company_rnc}|{period_str}|{company_name}"
    lines.append(header)
    
    total_salario_cotizable = 0
    total_sfs_empleado = 0
    total_afp_empleado = 0
    total_sfs_patronal = 0
    total_afp_patronal = 0
    total_srl = 0
    total_infotep = 0
    employee_count = 0
    
    for entry in entries:
        employee_doc = entry.get("employee_document") or ""
        employee_name = entry.get("employee_name") or ""
        salario_cotizable = entry.get("gross_salary", 0)
        sfs_empleado = entry.get("sfs_employee", 0)
        afp_empleado = entry.get("afp_employee", 0)
        sfs_patronal = entry.get("sfs_employer", 0)
        afp_patronal = entry.get("afp_employer", 0)
        srl = entry.get("srl_employer", 0)
        infotep = entry.get("infotep_employer", 0)
        
        detail_line = (
            f"D|{employee_doc}|{employee_name}|"
            f"{salario_cotizable:.2f}|{sfs_empleado:.2f}|{afp_empleado:.2f}|"
            f"{sfs_patronal:.2f}|{afp_patronal:.2f}|{srl:.2f}|{infotep:.2f}"
        )
        lines.append(detail_line)
        
        total_salario_cotizable += salario_cotizable
        total_sfs_empleado += sfs_empleado
        total_afp_empleado += afp_empleado
        total_sfs_patronal += sfs_patronal
        total_afp_patronal += afp_patronal
        total_srl += srl
        total_infotep += infotep
        employee_count += 1
    
    summary = (
        f"S|{employee_count}|{total_salario_cotizable:.2f}|"
        f"{total_sfs_empleado:.2f}|{total_afp_empleado:.2f}|"
        f"{total_sfs_patronal:.2f}|{total_afp_patronal:.2f}|"
        f"{total_srl:.2f}|{total_infotep:.2f}"
    )
    lines.append(summary)
    
    content = "\r\n".join(lines)
    filename = f"AM_{company_rnc}_{period_str}.txt"
    
    return Response(
        content=content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/periods/{period_id}/tss-preview")
async def preview_tss_report(period_id: str, current_user: dict = Depends(get_current_user)):
    """Preview TSS report data as JSON before downloading - Dominican Republic only"""
    company_id = current_user.get("company_id")
    await _require_dr_company(db, company_id, "Preview TSS")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    payroll_type = period.get("payroll_type", "REG")
    if payroll_type == "OBREROS_NG":
        return {
            "error": True,
            "message": "El reporte TSS no aplica para nóminas de Obreros NG 07/2007",
            "reason": "Este tipo de nómina solo requiere retención de ISR 2% sobre mano de obra, sin aportes a la TSS."
        }
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    company_rnc = company.get("rnc", "000000000") if company else "000000000"
    company_name = company.get("name", "EMPRESA") if company else "EMPRESA"
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    year = period.get("year", datetime.now().year)
    month = period.get("month", datetime.now().month)
    
    employees = []
    totals = {
        "salario_cotizable": 0,
        "sfs_empleado": 0,
        "afp_empleado": 0,
        "total_empleado": 0,
        "sfs_patronal": 0,
        "afp_patronal": 0,
        "srl": 0,
        "infotep": 0,
        "total_patronal": 0
    }
    
    for entry in entries:
        emp_data = {
            "cedula": entry.get("employee_document") or "",
            "nombre": entry.get("employee_name") or "",
            "salario_cotizable": entry.get("gross_salary", 0),
            "sfs_empleado": entry.get("sfs_employee", 0),
            "afp_empleado": entry.get("afp_employee", 0),
            "sfs_patronal": entry.get("sfs_employer", 0),
            "afp_patronal": entry.get("afp_employer", 0),
            "srl": entry.get("srl_employer", 0),
            "infotep": entry.get("infotep_employer", 0)
        }
        emp_data["total_empleado"] = emp_data["sfs_empleado"] + emp_data["afp_empleado"]
        emp_data["total_patronal"] = emp_data["sfs_patronal"] + emp_data["afp_patronal"] + emp_data["srl"] + emp_data["infotep"]
        
        employees.append(emp_data)
        
        totals["salario_cotizable"] += emp_data["salario_cotizable"]
        totals["sfs_empleado"] += emp_data["sfs_empleado"]
        totals["afp_empleado"] += emp_data["afp_empleado"]
        totals["total_empleado"] += emp_data["total_empleado"]
        totals["sfs_patronal"] += emp_data["sfs_patronal"]
        totals["afp_patronal"] += emp_data["afp_patronal"]
        totals["srl"] += emp_data["srl"]
        totals["infotep"] += emp_data["infotep"]
        totals["total_patronal"] += emp_data["total_patronal"]
    
    for key in totals:
        totals[key] = round(totals[key], 2)
    
    return {
        "company": {
            "rnc": company_rnc,
            "name": company_name
        },
        "period": {
            "year": year,
            "month": month,
            "description": period.get("description", ""),
            "payroll_type": payroll_type
        },
        "filename": f"AM_{company_rnc}_{month:02d}{year}.txt",
        "employee_count": len(employees),
        "employees": employees,
        "totals": totals,
        "rates": {
            "sfs_empleado": f"{SFS_EMPLOYEE_RATE * 100:.2f}%",
            "afp_empleado": f"{AFP_EMPLOYEE_RATE * 100:.2f}%",
            "sfs_patronal": f"{SFS_EMPLOYER_RATE * 100:.2f}%",
            "afp_patronal": f"{AFP_EMPLOYER_RATE * 100:.2f}%",
            "srl": f"{SRL_EMPLOYER_RATE * 100:.2f}%",
            "infotep": f"{INFOTEP_EMPLOYER_RATE * 100:.2f}%"
        }
    }
