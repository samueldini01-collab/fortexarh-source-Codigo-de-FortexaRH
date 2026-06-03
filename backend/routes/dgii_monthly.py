"""
DGII Monthly Consolidated Reports — FortexaRH

Generates DGII/TSS reports CONSOLIDATED by calendar month. When the company
runs quincenal payrolls, both Q1 and Q2 entries of the same year/month are
aggregated into a SINGLE line per employee — which is the format DGII/TSS
actually expects.

All endpoints accept ``year`` and ``month`` query params instead of a single
``period_id`` (the old behavior, still available in ``payroll_exports.py``).

Endpoints (all DR-only):
    GET /api/dgii-reports/monthly/preview      → JSON breakdown for UI
    GET /api/dgii-reports/monthly/ir3          → Excel IR-3
    GET /api/dgii-reports/monthly/ir4          → Excel IR-4 (detail)
    GET /api/dgii-reports/monthly/tss-autodeterminacion → TSS-Auto (tab-delimited)
    GET /api/dgii-reports/monthly/dgii-table-validation → JSON: per-employee
        comparison between our calculated ISR and the official DGII 2023 table.
"""
from __future__ import annotations

import io
import csv
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from config import db
from routes.country_config import COUNTRY_PROFILES
from utils.auth import get_current_user
from utils.payroll_constants import calculate_isr_monthly


router = APIRouter(prefix="/dgii-reports/monthly", tags=["DGII Monthly Reports"])


# ===================== HELPERS =====================

async def _require_dr(company_id: str, report_name: str = "Este reporte"):
    """Raise 400 if the company isn't configured as DR."""
    company = await db.companies.find_one(
        {"company_id": company_id}, {"_id": 0, "country": 1}
    )
    country_code = (company or {}).get("country", "DO")
    if country_code != "DO":
        profile = COUNTRY_PROFILES.get(country_code, {})
        raise HTTPException(
            status_code=400,
            detail=(
                f"{report_name} es específico de República Dominicana (DGII/TSS). "
                f"Su empresa está configurada como {profile.get('name', country_code)}."
            ),
        )


async def _consolidate_month(company_id: str, year: int, month: int) -> dict:
    """Return periods and one aggregated row per employee for the month.

    Aggregation: sums gross_salary, deductions, employer contributions across
    all payroll entries belonging to periods with the given year+month
    (whether the company runs quincenal_1/quincenal_2/mensual).
    """
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": int(year), "month": int(month)},
        {"_id": 0},
    ).to_list(50)

    if not periods:
        return {"periods": [], "rows": [], "totals": _empty_totals()}

    period_ids = [p["period_id"] for p in periods]
    entries = await db.payroll_entries.find(
        {"company_id": company_id, "period_id": {"$in": period_ids}},
        {"_id": 0},
    ).to_list(5000)

    # Aggregate per employee
    by_emp: dict[str, dict] = {}
    for e in entries:
        emp_id = e.get("employee_id")
        if not emp_id:
            continue
        agg = by_emp.setdefault(emp_id, {
            "employee_id": emp_id,
            "employee_name": e.get("employee_name", ""),
            "employee_document": e.get("employee_document", ""),
            "department": e.get("department", ""),
            "position": e.get("position", ""),
            "base_salary": 0.0,
            "bonuses": 0.0,
            "commissions": 0.0,
            "other_income": 0.0,
            "overtime": 0.0,
            "income_novelties": 0.0,
            "deduction_novelties": 0.0,
            "gross_salary": 0.0,
            "sfs_employee": 0.0,
            "afp_employee": 0.0,
            "isr": 0.0,
            "loan_deduction": 0.0,
            "total_additional_deductions": 0.0,
            "total_deductions": 0.0,
            "net_salary": 0.0,
            "sfs_employer": 0.0,
            "afp_employer": 0.0,
            "srl_employer": 0.0,
            "infotep_employer": 0.0,
            "total_employer_contributions": 0.0,
            "entries_count": 0,
        })
        agg["base_salary"] += float(e.get("base_salary", 0) or 0)
        agg["bonuses"] += float(e.get("bonuses", 0) or 0)
        agg["commissions"] += float(e.get("commissions", 0) or 0)
        agg["other_income"] += float(e.get("other_income", 0) or 0)
        agg["overtime"] += (
            float(e.get("overtime_day_amount", 0) or 0)
            + float(e.get("overtime_night_amount", 0) or 0)
            + float(e.get("overtime_weekend_amount", 0) or 0)
            + float(e.get("overtime_holiday_amount", 0) or 0)
        )
        agg["income_novelties"] += float(e.get("total_income_novelties", 0) or 0)
        agg["deduction_novelties"] += float(e.get("total_deduction_novelties", 0) or 0)
        agg["gross_salary"] += float(e.get("gross_salary", 0) or 0)
        agg["sfs_employee"] += float(e.get("sfs_employee", 0) or 0)
        agg["afp_employee"] += float(e.get("afp_employee", 0) or 0)
        agg["isr"] += float(e.get("isr", 0) or 0)
        agg["loan_deduction"] += float(e.get("loan_deduction", 0) or 0)
        agg["total_additional_deductions"] += float(e.get("total_additional_deductions", 0) or 0)
        agg["total_deductions"] += float(e.get("total_deductions", 0) or 0)
        agg["net_salary"] += float(e.get("net_salary", 0) or 0)
        agg["sfs_employer"] += float(e.get("sfs_employer", 0) or 0)
        agg["afp_employer"] += float(e.get("afp_employer", 0) or 0)
        agg["srl_employer"] += float(e.get("srl_employer", 0) or 0)
        agg["infotep_employer"] += float(e.get("infotep_employer", 0) or 0)
        agg["total_employer_contributions"] += float(e.get("total_employer_contributions", 0) or 0)
        agg["entries_count"] += 1

    rows = [
        {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}
        for r in by_emp.values()
    ]
    rows.sort(key=lambda r: (r.get("employee_name") or "").lower())

    totals = _empty_totals()
    for r in rows:
        for k in totals.keys():
            totals[k] = round(totals[k] + float(r.get(k, 0) or 0), 2)

    return {
        "periods": [
            {
                "period_id": p["period_id"],
                "period_type": p.get("period_type"),
                "status": p.get("status"),
                "description": p.get("description"),
            }
            for p in periods
        ],
        "rows": rows,
        "totals": totals,
        "employee_count": len(rows),
    }


def _empty_totals() -> dict:
    return {
        "base_salary": 0.0, "bonuses": 0.0, "commissions": 0.0,
        "other_income": 0.0, "overtime": 0.0,
        "income_novelties": 0.0, "deduction_novelties": 0.0,
        "gross_salary": 0.0,
        "sfs_employee": 0.0, "afp_employee": 0.0, "isr": 0.0,
        "loan_deduction": 0.0, "total_additional_deductions": 0.0,
        "total_deductions": 0.0, "net_salary": 0.0,
        "sfs_employer": 0.0, "afp_employer": 0.0, "srl_employer": 0.0,
        "infotep_employer": 0.0, "total_employer_contributions": 0.0,
    }


# ===================== ENDPOINTS =====================


@router.get("/preview")
async def monthly_preview(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
):
    """Return the consolidated month view: 1 row per employee, summed across
    quincenas of the same month. Used by the UI for the drill-down tables.
    """
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "Consolidación mensual DGII")
    data = await _consolidate_month(company_id, year, month)
    return {
        "year": int(year),
        "month": int(month),
        **data,
    }


@router.get("/ir3")
async def monthly_ir3(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
):
    """IR-3 consolidated for the whole month."""
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "IR-3 mensual")

    data = await _consolidate_month(company_id, year, month)
    if not data["rows"]:
        raise HTTPException(status_code=404, detail="No hay datos de nómina para el mes seleccionado")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}

    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')

    writer.writerow(["DECLARACIÓN IR-3 — RETENCIONES DE ASALARIADOS"])
    writer.writerow([])
    writer.writerow(["Empresa:", company.get("name", "")])
    writer.writerow(["RNC:", company.get("rnc", "")])
    writer.writerow(["Período:", f"{int(month):02d}/{int(year)}"])
    writer.writerow(["Empleados:", data["employee_count"]])
    writer.writerow([])

    writer.writerow(["RESUMEN"])
    writer.writerow(["Total Salarios Brutos:", f"RD$ {data['totals']['gross_salary']:,.2f}"])
    writer.writerow(["Total ISR Retenido:",   f"RD$ {data['totals']['isr']:,.2f}"])
    writer.writerow([])

    writer.writerow(["DETALLE POR EMPLEADO"])
    writer.writerow(["Cédula", "Nombre", "Salario Bruto Mensual", "ISR Mensual Retenido"])
    for r in data["rows"]:
        writer.writerow([
            r.get("employee_document") or "",
            r.get("employee_name") or "",
            f"{r['gross_salary']:.2f}",
            f"{r['isr']:.2f}",
        ])

    content = "\ufeff" + output.getvalue()
    rnc = (company.get("rnc") or "").replace("-", "")
    filename = f"IR3_{rnc}_{int(year)}{int(month):02d}.xls"
    return Response(
        content=content.encode("utf-8"),
        media_type="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/ir4")
async def monthly_ir4(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
):
    """IR-4 detail: 1 line per employee, consolidated monthly."""
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "IR-4 mensual")

    data = await _consolidate_month(company_id, year, month)
    if not data["rows"]:
        raise HTTPException(status_code=404, detail="No hay datos de nómina para el mes seleccionado")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}

    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')

    writer.writerow(["FORMULARIO IR-4 — DETALLE MENSUAL DE RETENCIONES"])
    writer.writerow([])
    writer.writerow(["Empresa:", company.get("name", "")])
    writer.writerow(["RNC:", company.get("rnc", "")])
    writer.writerow(["Período:", f"{int(month):02d}/{int(year)}"])
    writer.writerow([])

    writer.writerow([
        "Cédula",
        "Nombre Completo",
        "Salario Bruto Mensual",
        "AFP Empleado",
        "SFS Empleado",
        "Otras Retenciones",
        "ISR Retenido",
        "Salario Neto",
    ])

    for r in data["rows"]:
        writer.writerow([
            r.get("employee_document") or "",
            r.get("employee_name") or "",
            f"{r['gross_salary']:.2f}",
            f"{r['afp_employee']:.2f}",
            f"{r['sfs_employee']:.2f}",
            f"{r.get('total_additional_deductions', 0) + r.get('deduction_novelties', 0) + r.get('loan_deduction', 0):.2f}",
            f"{r['isr']:.2f}",
            f"{r['net_salary']:.2f}",
        ])

    writer.writerow([])
    writer.writerow([
        "",
        "TOTALES",
        f"{data['totals']['gross_salary']:.2f}",
        f"{data['totals']['afp_employee']:.2f}",
        f"{data['totals']['sfs_employee']:.2f}",
        "",
        f"{data['totals']['isr']:.2f}",
        f"{data['totals']['net_salary']:.2f}",
    ])

    content = "\ufeff" + output.getvalue()
    rnc = (company.get("rnc") or "").replace("-", "")
    filename = f"IR4_{rnc}_{int(year)}{int(month):02d}.xls"
    return Response(
        content=content.encode("utf-8"),
        media_type="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/tss-autodeterminacion")
async def monthly_tss_autodeterminacion(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
):
    """TSS Autodeterminación file — ALWAYS monthly (consolidates quincenas).

    Format: tab-delimited file matching SUIR+ Autodeterminación structure.
    """
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "TSS Autodeterminación mensual")

    data = await _consolidate_month(company_id, year, month)
    if not data["rows"]:
        raise HTTPException(status_code=404, detail="No hay datos de nómina para el mes seleccionado")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    rnc = (company.get("rnc") or "").replace("-", "")

    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')

    writer.writerow([
        "RNC_PATRONO", "CEDULA", "TIPO_CEDULA", "NSS",
        "NOMBRE", "APELLIDO1", "APELLIDO2",
        "SEXO", "FECHA_NACIMIENTO",
        "SALARIO_COTIZABLE_MENSUAL",
        "APORTE_VOLUNTARIO", "SFS_EMPLEADOR", "SFS_EMPLEADO",
        "AFP_EMPLEADOR", "AFP_EMPLEADO", "SRL", "INFOTEP",
    ])

    for r in data["rows"]:
        cedula = (r.get("employee_document") or "").replace("-", "")
        name_parts = (r.get("employee_name") or "").split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name1 = name_parts[-1] if len(name_parts) > 1 else ""
        last_name2 = name_parts[-2] if len(name_parts) > 2 else ""

        writer.writerow([
            rnc, cedula, "C", "",
            first_name, last_name1, last_name2,
            "M", "",
            f"{r['gross_salary']:.2f}",
            "0.00",
            f"{r['sfs_employer']:.2f}",
            f"{r['sfs_employee']:.2f}",
            f"{r['afp_employer']:.2f}",
            f"{r['afp_employee']:.2f}",
            f"{r['srl_employer']:.2f}",
            f"{r['infotep_employer']:.2f}",
        ])

    content = "\ufeff" + output.getvalue()
    filename = f"TSS_Autodeterminacion_{rnc}_{int(year)}{int(month):02d}.xls"
    return Response(
        content=content.encode("utf-8"),
        media_type="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/dgii-table-validation")
async def dgii_table_validation(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
):
    """Validates each employee's monthly ISR against the official DGII formula
    (which is mathematically identical to the published DGII 2023 retention
    table). Returns per-employee deltas + a summary so HR can confirm the
    consolidated month matches the table exactly.

    Tolerance: ``RD$0.50`` accounts for the table's 50-peso step rounding —
    anything below that is treated as a match.
    """
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "Validación tabla DGII")

    data = await _consolidate_month(company_id, year, month)
    if not data["rows"]:
        raise HTTPException(status_code=404, detail="No hay datos de nómina para el mes seleccionado")

    tolerance = 0.50
    results = []
    matches = 0
    diffs = 0
    for r in data["rows"]:
        expected = calculate_isr_monthly(r["gross_salary"])
        expected_isr = float(expected.get("isr_monthly") or 0)
        actual_isr = float(r.get("isr") or 0)
        delta = round(actual_isr - expected_isr, 2)
        is_match = abs(delta) <= tolerance
        if is_match:
            matches += 1
        else:
            diffs += 1
        results.append({
            "employee_id": r["employee_id"],
            "employee_name": r["employee_name"],
            "employee_document": r["employee_document"],
            "gross_salary": r["gross_salary"],
            "dgii_table_isr": round(expected_isr, 2),
            "calculated_isr": round(actual_isr, 2),
            "delta": delta,
            "match": is_match,
            "tax_bracket": expected.get("tax_bracket"),
        })

    return {
        "year": int(year),
        "month": int(month),
        "tolerance": tolerance,
        "summary": {
            "employees": len(results),
            "matches": matches,
            "discrepancies": diffs,
            "total_calculated_isr": round(data["totals"]["isr"], 2),
            "total_dgii_isr": round(sum(r["dgii_table_isr"] for r in results), 2),
        },
        "results": results,
    }
