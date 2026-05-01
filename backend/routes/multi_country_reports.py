"""
Multi-Country Fiscal Reports - FortexaRH
Universal fiscal reporting for all 28 supported countries.

Generates CSV and PDF fiscal summary reports that adapt to the company's country,
using the country profile's agency name, currency, and exact tax/SS codes.

This is the foundation layer — for DR-specific formats (TSS TXT, IR-3, IR-17),
see /routes/dgii_reports.py and /routes/payroll_exports.py.
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from typing import Optional
from datetime import datetime, timezone
import io
import csv

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from config import db
from utils.auth import get_current_user
from routes.country_config import COUNTRY_PROFILES, get_company_rates_flat, calculate_isr_dynamic
from utils.payroll_constants import calculate_isr_monthly as _calc_isr_dr

router = APIRouter(prefix="/multi-country-reports", tags=["Multi-Country Fiscal Reports"])


# ===================== HELPERS =====================

async def _collect_period_data(company_id: str, period: str):
    """Fetch payroll entries + employee data for a period (YYYY-MM or period_id)."""
    # Match either by period YYYY-MM or specific period_id
    if period.startswith("period_"):
        entries_query = {"company_id": company_id, "period_id": period}
        period_info = await db.payroll_periods.find_one({"period_id": period, "company_id": company_id}, {"_id": 0})
    else:
        # Period format "YYYY-MM" — match periods for that month
        period_info = None
        try:
            year, month = period.split("-")
            periods = await db.payroll_periods.find(
                {"company_id": company_id, "year": int(year), "month": int(month)},
                {"_id": 0}
            ).to_list(50)
            period_ids = [p["period_id"] for p in periods]
            entries_query = {"company_id": company_id, "period_id": {"$in": period_ids}}
            if periods:
                period_info = periods[0]
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de período inválido. Use YYYY-MM o period_id.")

    entries = await db.payroll_entries.find(entries_query, {"_id": 0}).to_list(5000)

    # Enrich entries with employee data
    emp_ids = list({e.get("employee_id") for e in entries if e.get("employee_id")})
    emps = {}
    if emp_ids:
        rows = await db.employees.find(
            {"company_id": company_id, "employee_id": {"$in": emp_ids}},
            {"_id": 0, "employee_id": 1, "document_number": 1, "first_name": 1, "last_name": 1, "department": 1, "position": 1}
        ).to_list(5000)
        emps = {r["employee_id"]: r for r in rows}

    return entries, emps, period_info


def _sum_detail_for_entry(entry: dict, rates: dict):
    """Map DB fields (sfs_employee etc.) to country-specific labels/codes for display.
    Only includes slots that exist in the country profile.
    """
    emp_deds = rates.get("employee_deductions_detail", [])
    er_conts = rates.get("employer_contributions_detail", [])

    # Employee side: slot 0 -> sfs_employee (DB), slot 1 -> afp_employee (DB)
    emp_rows = []
    gross = float(entry.get("gross_salary", 0) or 0)
    if len(emp_deds) >= 1:
        emp_rows.append({"code": emp_deds[0]["code"], "name": emp_deds[0]["name"],
                         "rate": emp_deds[0]["rate"], "amount": float(entry.get("sfs_employee", 0) or 0)})
    if len(emp_deds) >= 2:
        emp_rows.append({"code": emp_deds[1]["code"], "name": emp_deds[1]["name"],
                         "rate": emp_deds[1]["rate"], "amount": float(entry.get("afp_employee", 0) or 0)})
    # Any extra employee deductions (slot ≥3) — calculate on the fly from gross
    for d in emp_deds[2:]:
        emp_rows.append({"code": d["code"], "name": d["name"], "rate": d["rate"],
                         "amount": round(gross * d["rate"], 2)})

    # Employer side: DB stores 4 slots (sfs_employer, afp_employer, srl_employer, infotep_employer)
    er_rows = []
    db_fields = ["sfs_employer", "afp_employer", "srl_employer", "infotep_employer"]
    for i, cont in enumerate(er_conts):
        if i < 4:
            amt = float(entry.get(db_fields[i], 0) or 0)
        else:
            amt = round(gross * cont["rate"], 2)
        er_rows.append({"code": cont["code"], "name": cont["name"], "rate": cont["rate"], "amount": amt})

    return emp_rows, er_rows


# ===================== ENDPOINTS =====================

@router.get("/available-reports")
async def list_available_reports(current_user: dict = Depends(get_current_user)):
    """Return the list of fiscal reports available for the current company's country."""
    company_id = current_user.get("company_id")
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    country_code = (company or {}).get("country", "DO")
    profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES["DO"])
    return {
        "country_code": country_code,
        "country_name": profile["name"],
        "currency": profile["currency"],
        "currency_symbol": profile["currency_symbol"],
        "agency": profile.get("income_tax", {}).get("agency", ""),
        "social_security_system": profile.get("social_security", {}).get("system_name", ""),
        "country_specific_reports": profile.get("reports", []),
        "universal_reports": [
            {
                "id": "fiscal_summary_csv",
                "name": "Resumen Fiscal (CSV)",
                "description": f"Archivo CSV adaptado a {profile['name']} con contribuciones por empleado",
                "endpoint": f"/api/multi-country-reports/fiscal-summary?period=YYYY-MM&format=csv",
            },
            {
                "id": "fiscal_summary_pdf",
                "name": "Resumen Fiscal (PDF)",
                "description": f"Reporte PDF legible con totales y detalle por empleado",
                "endpoint": f"/api/multi-country-reports/fiscal-summary?period=YYYY-MM&format=pdf",
            },
        ]
    }


@router.get("/fiscal-summary")
async def fiscal_summary(
    period: str,
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    """
    Universal fiscal summary report — works for ALL 28 supported countries.

    Parameters:
      period: YYYY-MM (e.g. 2026-03) or period_id (e.g. period_abc123)
      format: csv | pdf

    Returns a country-adapted report with:
      - Company header (name, tax id, country, currency)
      - Tax authority / social security agency names
      - Per-employee rows: gross salary, each employee deduction by country code, ISR, net
      - Per-employee employer contributions by country code
      - Totals footer
    """
    if format not in ("csv", "pdf"):
        raise HTTPException(status_code=400, detail="Formato inválido. Use: csv o pdf")

    company_id = current_user.get("company_id")
    rates = await get_company_rates_flat(company_id)
    country_code = rates["country_code"]
    profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES["DO"])

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    entries, emps, period_info = await _collect_period_data(company_id, period)

    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para el período {period}")

    emp_deds_profile = rates.get("employee_deductions_detail", [])
    er_conts_profile = rates.get("employer_contributions_detail", [])
    agency = profile.get("income_tax", {}).get("agency", "")
    ss_system = profile.get("social_security", {}).get("system_name", "")
    currency_symbol = rates.get("currency_symbol", "")
    company_name = company.get("company_name") or company.get("name") or "EMPRESA"
    tax_id = company.get("rnc") or company.get("tax_id") or ""

    # Build common per-row data
    rows = []
    totals = {
        "gross": 0.0, "isr": 0.0, "net": 0.0,
        "emp_deductions": {d["code"]: 0.0 for d in emp_deds_profile},
        "er_contributions": {c["code"]: 0.0 for c in er_conts_profile},
    }
    for entry in entries:
        emp = emps.get(entry.get("employee_id"), {})
        emp_rows, er_rows = _sum_detail_for_entry(entry, rates)
        gross = float(entry.get("gross_salary", 0) or 0)
        isr = float(entry.get("isr", 0) or 0)
        net = float(entry.get("net_salary", 0) or 0)
        row = {
            "employee_id": entry.get("employee_id", ""),
            "document": emp.get("document_number") or entry.get("employee_document") or "",
            "first_name": emp.get("first_name") or entry.get("employee_name", "").split(" ", 1)[0],
            "last_name": emp.get("last_name") or (entry.get("employee_name", "").split(" ", 1)[1] if " " in (entry.get("employee_name") or "") else ""),
            "department": emp.get("department", ""),
            "position": emp.get("position", ""),
            "gross_salary": round(gross, 2),
            "isr": round(isr, 2),
            "net_salary": round(net, 2),
            "employee_deductions": emp_rows,
            "employer_contributions": er_rows,
        }
        rows.append(row)
        totals["gross"] += gross
        totals["isr"] += isr
        totals["net"] += net
        for er in emp_rows:
            totals["emp_deductions"][er["code"]] = totals["emp_deductions"].get(er["code"], 0.0) + er["amount"]
        for er in er_rows:
            totals["er_contributions"][er["code"]] = totals["er_contributions"].get(er["code"], 0.0) + er["amount"]

    # Round totals
    totals["gross"] = round(totals["gross"], 2)
    totals["isr"] = round(totals["isr"], 2)
    totals["net"] = round(totals["net"], 2)
    totals["emp_deductions"] = {k: round(v, 2) for k, v in totals["emp_deductions"].items()}
    totals["er_contributions"] = {k: round(v, 2) for k, v in totals["er_contributions"].items()}

    filename_safe_period = period.replace("/", "-")
    filename_base = f"FiscalSummary_{country_code}_{filename_safe_period}"

    if format == "csv":
        return _render_csv(rows, totals, profile, rates, company_name, tax_id, period, filename_base,
                           emp_deds_profile, er_conts_profile, agency, ss_system)
    else:
        return _render_pdf(rows, totals, profile, rates, company_name, tax_id, period, filename_base,
                           emp_deds_profile, er_conts_profile, agency, ss_system, currency_symbol)


def _render_csv(rows, totals, profile, rates, company_name, tax_id, period, filename_base,
                emp_deds_profile, er_conts_profile, agency, ss_system):
    output = io.StringIO()
    w = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    w.writerow([f"REPORTE FISCAL — {profile['name']}"])
    w.writerow([f"Empresa: {company_name}", f"ID Fiscal: {tax_id}"])
    w.writerow([f"Período: {period}", f"Moneda: {rates['currency']} ({rates['currency_symbol']})"])
    w.writerow([f"Agencia Fiscal: {agency}", f"Sistema Seguridad Social: {ss_system}"])
    w.writerow([f"Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"])
    w.writerow([])
    # Header row
    header = ["#", "Documento", "Nombres", "Apellidos", "Depto", "Cargo", "Salario Bruto"]
    for d in emp_deds_profile:
        header.append(f"{d['code']} ({d['rate']*100:.2f}%)")
    header += ["ISR", "Salario Neto"]
    for c in er_conts_profile:
        header.append(f"{c['code']} ({c['rate']*100:.2f}%)")
    w.writerow(header)
    # Data rows
    for idx, r in enumerate(rows, 1):
        line = [idx, r["document"], r["first_name"], r["last_name"], r["department"], r["position"],
                f"{r['gross_salary']:.2f}"]
        emp_by_code = {e["code"]: e["amount"] for e in r["employee_deductions"]}
        for d in emp_deds_profile:
            line.append(f"{emp_by_code.get(d['code'], 0):.2f}")
        line += [f"{r['isr']:.2f}", f"{r['net_salary']:.2f}"]
        er_by_code = {e["code"]: e["amount"] for e in r["employer_contributions"]}
        for c in er_conts_profile:
            line.append(f"{er_by_code.get(c['code'], 0):.2f}")
        w.writerow(line)
    # Totals
    w.writerow([])
    totals_line = ["TOTAL", "", "", "", "", "", f"{totals['gross']:.2f}"]
    for d in emp_deds_profile:
        totals_line.append(f"{totals['emp_deductions'].get(d['code'], 0):.2f}")
    totals_line += [f"{totals['isr']:.2f}", f"{totals['net']:.2f}"]
    for c in er_conts_profile:
        totals_line.append(f"{totals['er_contributions'].get(c['code'], 0):.2f}")
    w.writerow(totals_line)

    content = output.getvalue()
    return Response(
        content=content.encode("utf-8-sig"),  # BOM for Excel compatibility
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.csv"'}
    )


def _render_pdf(rows, totals, profile, rates, company_name, tax_id, period, filename_base,
                emp_deds_profile, er_conts_profile, agency, ss_system, currency_symbol):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=10 * mm, rightMargin=10 * mm,
        topMargin=12 * mm, bottomMargin=10 * mm,
        title=f"Reporte Fiscal {profile['name']} {period}"
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=14, spaceAfter=4, textColor=colors.HexColor("#0f172a"))
    h2 = ParagraphStyle("h2", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#475569"))
    story = []

    # Header
    story.append(Paragraph(f"{profile.get('flag', '')} REPORTE FISCAL — {profile['name']}", h1))
    story.append(Paragraph(f"<b>Empresa:</b> {company_name} &nbsp;&nbsp; <b>ID Fiscal:</b> {tax_id}", h2))
    story.append(Paragraph(f"<b>Período:</b> {period} &nbsp;&nbsp; <b>Moneda:</b> {rates['currency']} ({currency_symbol})", h2))
    story.append(Paragraph(f"<b>Agencia:</b> {agency} &nbsp;&nbsp; <b>SS:</b> {ss_system}", h2))
    story.append(Paragraph(f"<i>Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</i>", h2))
    story.append(Spacer(1, 6))

    # Build table headers dynamically
    table_header = ["#", "Documento", "Nombre", "Bruto"]
    for d in emp_deds_profile:
        table_header.append(f"{d['code']}\n{d['rate']*100:.2f}%")
    table_header += ["ISR", "Neto"]

    # Data table (employee deductions side + ISR + net)
    data = [table_header]
    for idx, r in enumerate(rows, 1):
        line = [str(idx), r["document"] or "—",
                f"{r['first_name']} {r['last_name']}".strip(),
                f"{currency_symbol} {r['gross_salary']:,.2f}"]
        emp_by_code = {e["code"]: e["amount"] for e in r["employee_deductions"]}
        for d in emp_deds_profile:
            line.append(f"{emp_by_code.get(d['code'], 0):,.2f}")
        line += [f"{r['isr']:,.2f}", f"{currency_symbol} {r['net_salary']:,.2f}"]
        data.append(line)
    # Totals
    totals_line = ["", "", "TOTAL", f"{currency_symbol} {totals['gross']:,.2f}"]
    for d in emp_deds_profile:
        totals_line.append(f"{totals['emp_deductions'].get(d['code'], 0):,.2f}")
    totals_line += [f"{totals['isr']:,.2f}", f"{currency_symbol} {totals['net']:,.2f}"]
    data.append(totals_line)

    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fef3c7")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(Paragraph("<b>Deducciones del Empleado</b>", styles["Heading4"]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Employer side
    if er_conts_profile:
        er_header = ["#", "Documento", "Nombre", "Bruto"]
        for c in er_conts_profile:
            er_header.append(f"{c['code']}\n{c['rate']*100:.2f}%")
        er_header.append("Total Aporte")
        er_data = [er_header]
        for idx, r in enumerate(rows, 1):
            line = [str(idx), r["document"] or "—",
                    f"{r['first_name']} {r['last_name']}".strip(),
                    f"{currency_symbol} {r['gross_salary']:,.2f}"]
            er_by_code = {e["code"]: e["amount"] for e in r["employer_contributions"]}
            total_aporte = 0.0
            for c in er_conts_profile:
                amt = er_by_code.get(c["code"], 0)
                line.append(f"{amt:,.2f}")
                total_aporte += amt
            line.append(f"{currency_symbol} {total_aporte:,.2f}")
            er_data.append(line)
        # Totals
        total_aporte_global = sum(totals["er_contributions"].get(c["code"], 0) for c in er_conts_profile)
        totals_er_line = ["", "", "TOTAL", f"{currency_symbol} {totals['gross']:,.2f}"]
        for c in er_conts_profile:
            totals_er_line.append(f"{totals['er_contributions'].get(c['code'], 0):,.2f}")
        totals_er_line.append(f"{currency_symbol} {total_aporte_global:,.2f}")
        er_data.append(totals_er_line)

        er_tbl = Table(er_data, repeatRows=1)
        er_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ccfbf1")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(Paragraph("<b>Contribuciones del Empleador</b>", styles["Heading4"]))
        story.append(er_tbl)

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<i>Este reporte es un resumen fiscal generado por FortexaRH adaptado al motor fiscal de {profile['name']}. "
        f"Para cumplimiento oficial ante {agency or 'la autoridad fiscal'}, consulte los formatos específicos del país.</i>",
        styles["Italic"]
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'}
    )


# ===================== FISCAL COMPARISON CALCULATOR =====================

from pydantic import BaseModel
from typing import List


class ComparisonRequest(BaseModel):
    gross_monthly: float
    countries: List[str]  # e.g. ["DO", "CO", "MX", "US"]
    include_employee: bool = True  # employee-side breakdown
    include_employer: bool = True  # employer-side breakdown
    display_currency: Optional[str] = None  # e.g. "USD", "EUR" — if set, adds FX-converted values
    gross_currency: Optional[str] = None  # currency of the gross_monthly input (if None, assumes each country's own)


# Simple in-memory FX cache (1 hour TTL)
_fx_cache: dict = {"timestamp": 0, "rates": {}}
_FX_CACHE_TTL = 3600  # 1 hour


async def _get_fx_rates(base: str = "USD") -> dict:
    """Fetch FX rates from open.er-api.com (free, no API key, ~166 currencies).
    Returns dict mapping currency_code -> rate (1 base = rate units of target).
    Cached for 1 hour.
    """
    import time
    import httpx
    now = time.time()
    cache_key = base.upper()
    if _fx_cache.get("base") == cache_key and (now - _fx_cache.get("timestamp", 0)) < _FX_CACHE_TTL:
        return _fx_cache.get("rates", {})
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(f"https://open.er-api.com/v6/latest/{base}")
            data = resp.json()
            if data.get("result") == "success":
                rates = data.get("rates") or {}
                if rates:
                    _fx_cache["rates"] = rates
                    _fx_cache["base"] = cache_key
                    _fx_cache["timestamp"] = now
                    return rates
    except Exception as e:
        print(f"[FX] Failed to fetch rates: {e}")
    return _fx_cache.get("rates", {})


def _convert(amount: float, from_curr: str, to_curr: str, rates_from_usd: dict) -> Optional[float]:
    """Convert amount from one currency to another using USD-based rates.
    rates_from_usd: {"USD": 1, "EUR": 0.85, "DOP": 60.5, ...}
    """
    if from_curr == to_curr:
        return round(amount, 2)
    rate_from = rates_from_usd.get(from_curr)
    rate_to = rates_from_usd.get(to_curr)
    if not rate_from or not rate_to:
        return None
    # amount in USD = amount / rate_from, then * rate_to
    converted = (amount / rate_from) * rate_to
    return round(converted, 2)


def _compute_country_cost(gross: float, country_code: str) -> dict:
    """For a single country, compute: employee deductions, ISR, net, employer contributions, total cost."""
    profile = COUNTRY_PROFILES.get(country_code.upper())
    if not profile:
        return None

    emp_deds = profile["social_security"]["employee_deductions"]
    er_conts = profile["social_security"]["employer_contributions"]

    # Employee SS deductions
    employee_breakdown = []
    total_employee_ss = 0.0
    for d in emp_deds:
        amt = round(gross * d["rate"], 2)
        cap = d.get("cap_monthly")
        if cap is not None and cap > 0 and amt > cap:
            amt = cap
        employee_breakdown.append({
            "code": d["code"],
            "name": d["name"],
            "rate": d["rate"],
            "rate_pct": round(d["rate"] * 100, 3),
            "amount": amt,
        })
        total_employee_ss += amt

    # ISR (DR uses DGII table for precision; others use bracket-based)
    income_tax = profile.get("income_tax") or {}
    if country_code.upper() == "DO":
        isr_val = _calc_isr_dr(gross)["isr_monthly"]
    else:
        isr_val = calculate_isr_dynamic(gross, income_tax)["isr_monthly"]
    isr_val = round(isr_val, 2)

    # Employer contributions
    employer_breakdown = []
    total_employer = 0.0
    for c in er_conts:
        amt = round(gross * c["rate"], 2)
        cap = c.get("cap_monthly")
        if cap is not None and cap > 0 and amt > cap:
            amt = cap
        employer_breakdown.append({
            "code": c["code"],
            "name": c["name"],
            "rate": c["rate"],
            "rate_pct": round(c["rate"] * 100, 3),
            "amount": amt,
        })
        total_employer += amt

    total_employee_deductions = round(total_employee_ss + isr_val, 2)
    net_salary = round(gross - total_employee_deductions, 2)
    total_employer = round(total_employer, 2)
    total_cost_to_company = round(gross + total_employer, 2)

    return {
        "country_code": country_code.upper(),
        "country_name": profile["name"],
        "flag": profile.get("flag", ""),
        "currency": profile["currency"],
        "currency_symbol": profile["currency_symbol"],
        "region": profile.get("region", ""),
        "agency": income_tax.get("agency", ""),
        "social_security_system": profile["social_security"].get("system_name", ""),
        "gross_salary": round(gross, 2),
        "employee": {
            "breakdown": employee_breakdown,
            "total_ss": round(total_employee_ss, 2),
            "isr": isr_val,
            "total_deductions": total_employee_deductions,
            "net_salary": net_salary,
            "effective_tax_rate_pct": round((total_employee_deductions / gross * 100) if gross > 0 else 0, 2),
        },
        "employer": {
            "breakdown": employer_breakdown,
            "total_contributions": total_employer,
            "total_cost_to_company": total_cost_to_company,
            "cost_overhead_pct": round((total_employer / gross * 100) if gross > 0 else 0, 2),
        }
    }


@router.post("/cost-comparison")
async def fiscal_cost_comparison(
    payload: ComparisonRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Compare the fiscal cost of the same gross salary across multiple countries.

    Input:
      { "gross_monthly": 3000, "countries": ["DO","CO","MX","US","ES"] }

    Output: for each country, a full breakdown of employee deductions, ISR, net salary,
    employer contributions, and total cost to company — all in the country's local currency
    (NOTE: no FX conversion is applied; amounts are shown in each country's currency).
    Useful for cross-border hiring decisions.
    """
    if payload.gross_monthly <= 0:
        raise HTTPException(status_code=400, detail="gross_monthly debe ser > 0")
    if not payload.countries or len(payload.countries) < 1:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos 1 país")
    if len(payload.countries) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 países por comparación")

    results = []
    unsupported = []
    for cc in payload.countries:
        data = _compute_country_cost(payload.gross_monthly, cc)
        if data is None:
            unsupported.append(cc)
            continue
        if not payload.include_employee:
            data.pop("employee", None)
        if not payload.include_employer:
            data.pop("employer", None)
        results.append(data)

    # FX conversion — optional, only if display_currency is set
    fx_info = None
    if payload.display_currency:
        display_curr = payload.display_currency.upper()
        import time
        rates = await _get_fx_rates(base="USD")
        if rates:
            fx_info = {"display_currency": display_curr, "base": "USD", "rate_source": "open.er-api.com", "cached": (time.time() - _fx_cache.get("timestamp", 0)) < _FX_CACHE_TTL - 5}
            for r in results:
                local = r["currency"]
                converted = {
                    "display_currency": display_curr,
                    "gross_salary": _convert(r["gross_salary"], local, display_curr, rates),
                }
                if "employee" in r:
                    converted["total_deductions"] = _convert(r["employee"]["total_deductions"], local, display_curr, rates)
                    converted["net_salary"] = _convert(r["employee"]["net_salary"], local, display_curr, rates)
                if "employer" in r:
                    converted["total_contributions"] = _convert(r["employer"]["total_contributions"], local, display_curr, rates)
                    converted["total_cost_to_company"] = _convert(r["employer"]["total_cost_to_company"], local, display_curr, rates)
                r["converted"] = converted

    # Sort: by total_cost_to_company ascending (cheapest first)
    # If FX conversion applied, sort by converted total cost so comparison is apples-to-apples
    if payload.include_employer:
        if fx_info and all(r.get("converted", {}).get("total_cost_to_company") is not None for r in results):
            results.sort(key=lambda r: r["converted"]["total_cost_to_company"])
        else:
            results.sort(key=lambda r: r.get("employer", {}).get("total_cost_to_company", 0))

    return {
        "gross_monthly": payload.gross_monthly,
        "countries_compared": len(results),
        "unsupported_countries": unsupported,
        "results": results,
        "fx": fx_info,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": ("Montos en moneda local. Campo 'converted' muestra equivalencia en " + payload.display_currency.upper()) if payload.display_currency else "Los montos están en la moneda local de cada país. No se aplica conversión de divisas."
    }


# ===================== EXECUTIVE PDF EXPORT (Fiscal Comparison) =====================

class ComparisonPDFRequest(BaseModel):
    gross_monthly: float
    countries: List[str]
    display_currency: Optional[str] = None
    company_name: Optional[str] = None  # optional override


@router.post("/cost-comparison-pdf")
async def cost_comparison_pdf(
    payload: ComparisonPDFRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate an Executive PDF report of the fiscal cost comparison.
    Includes cover, comparative table, key insights, recommendation, and methodology footer.
    Suitable for board presentations / hiring decisions.
    """
    if payload.gross_monthly <= 0:
        raise HTTPException(status_code=400, detail="gross_monthly debe ser > 0")
    if not payload.countries or len(payload.countries) > 10:
        raise HTTPException(status_code=400, detail="Países: 1-10 requeridos")

    # Compute results (reuse helpers)
    results = []
    unsupported = []
    for cc in payload.countries:
        data = _compute_country_cost(payload.gross_monthly, cc)
        if data is None:
            unsupported.append(cc)
            continue
        results.append(data)

    if not results:
        raise HTTPException(status_code=400, detail="Ningún país válido")

    # FX conversion
    fx_info = None
    display_curr = (payload.display_currency or "").upper() or None
    if display_curr:
        rates = await _get_fx_rates(base="USD")
        if rates:
            fx_info = {"display_currency": display_curr, "rate_source": "open.er-api.com"}
            for r in results:
                local = r["currency"]
                r["converted"] = {
                    "display_currency": display_curr,
                    "gross_salary": _convert(r["gross_salary"], local, display_curr, rates),
                    "total_deductions": _convert(r["employee"]["total_deductions"], local, display_curr, rates),
                    "net_salary": _convert(r["employee"]["net_salary"], local, display_curr, rates),
                    "total_contributions": _convert(r["employer"]["total_contributions"], local, display_curr, rates),
                    "total_cost_to_company": _convert(r["employer"]["total_cost_to_company"], local, display_curr, rates),
                }

    # Sort: cheapest first
    if fx_info and all(r.get("converted", {}).get("total_cost_to_company") is not None for r in results):
        results.sort(key=lambda r: r["converted"]["total_cost_to_company"])
    else:
        results.sort(key=lambda r: r["employer"]["total_cost_to_company"])

    cheapest = results[0]
    most_expensive = results[-1]

    # Get company info
    company_id = current_user.get("company_id")
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    company_name = payload.company_name or company.get("company_name") or company.get("name") or "FortexaRH"

    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title=f"Análisis Fiscal Comparativo — {len(results)} países"
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=22,
                                 textColor=colors.HexColor("#0f172a"), spaceAfter=4, alignment=1)
    subtitle = ParagraphStyle("sub", parent=styles["Normal"], fontSize=11,
                              textColor=colors.HexColor("#475569"), spaceAfter=14, alignment=1)
    section = ParagraphStyle("sec", parent=styles["Heading2"], fontSize=13,
                             textColor=colors.HexColor("#1e293b"), spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10,
                          textColor=colors.HexColor("#334155"), spaceAfter=6, leading=14)
    callout = ParagraphStyle("callout", parent=styles["Normal"], fontSize=10,
                             textColor=colors.HexColor("#0f766e"), spaceAfter=4)

    story = []

    # ========= COVER =========
    story.append(Spacer(1, 30))
    story.append(Paragraph("ANÁLISIS FISCAL COMPARATIVO", title_style))
    story.append(Paragraph(f"<i>Decisión Estratégica de Contratación Internacional</i>", subtitle))
    story.append(Spacer(1, 20))

    # Cover summary card
    cover_data = [
        ["Empresa solicitante", company_name],
        ["Salario bruto evaluado", f"{payload.gross_monthly:,.2f} (moneda local de cada país)"],
        ["Países comparados", f"{len(results)} de {len(payload.countries)} solicitados"],
        ["Moneda de visualización", display_curr or "Local de cada país"],
        ["Generado", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
    ]
    cover_tbl = Table(cover_data, colWidths=[55 * mm, 105 * mm])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f1f5f9")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(cover_tbl)
    story.append(Spacer(1, 20))

    # ========= EXECUTIVE SUMMARY =========
    story.append(Paragraph("Resumen Ejecutivo", section))
    cheapest_curr = cheapest["currency_symbol"]
    cheapest_cost = cheapest["employer"]["total_cost_to_company"]
    cheapest_overhead = cheapest["employer"]["cost_overhead_pct"]
    cheapest_usd = ""
    if cheapest.get("converted") and cheapest["converted"].get("total_cost_to_company") is not None:
        cheapest_usd = f" (≈ {cheapest['converted']['display_currency']} {cheapest['converted']['total_cost_to_company']:,.2f})"

    spread = round(most_expensive["employer"]["cost_overhead_pct"] - cheapest_overhead, 2)
    summary_text = (
        f"De {len(results)} países evaluados, <b>{cheapest['flag']} {cheapest['country_name']}</b> "
        f"presenta el menor costo total para la empresa: "
        f"<b>{cheapest_curr} {cheapest_cost:,.2f}{cheapest_usd}</b> "
        f"con un overhead de <b>+{cheapest_overhead}%</b> sobre el salario bruto. "
        f"El país más caro es <b>{most_expensive['flag']} {most_expensive['country_name']}</b> "
        f"con +{most_expensive['employer']['cost_overhead_pct']}% — un <b>spread de {spread} puntos porcentuales</b>."
    )
    story.append(Paragraph(summary_text, body))
    story.append(Spacer(1, 8))

    # ========= COMPARATIVE TABLE =========
    story.append(Paragraph("Tabla Comparativa por País", section))
    if fx_info:
        header = ["#", "País", "Bruto Local", "Empleado SS+ISR", "Neto", "Aporte Patronal",
                 f"Costo Total\n({display_curr})", "Overhead"]
    else:
        header = ["#", "País", "Bruto Local", "Empleado SS+ISR", "Neto", "Aporte Patronal",
                 "Costo Total Local", "Overhead"]
    data = [header]
    for idx, r in enumerate(results, 1):
        sym = r["currency_symbol"]
        cost_total_str = f"{sym} {r['employer']['total_cost_to_company']:,.2f}"
        if r.get("converted") and r["converted"].get("total_cost_to_company") is not None:
            cost_total_str = f"{r['converted']['display_currency']} {r['converted']['total_cost_to_company']:,.2f}\n({sym} {r['employer']['total_cost_to_company']:,.0f})"
        country_label = f"{r['flag']} {r['country_name']}"
        if idx == 1:
            country_label += " ★"
        data.append([
            str(idx),
            Paragraph(f"<b>{country_label}</b><br/><font size=7 color='#64748b'>{r['agency'] or '—'}</font>", body),
            f"{sym} {r['gross_salary']:,.2f}",
            f"{sym} {r['employee']['total_deductions']:,.2f}",
            f"{sym} {r['employee']['net_salary']:,.2f}",
            f"{sym} {r['employer']['total_contributions']:,.2f}",
            cost_total_str,
            f"+{r['employer']['cost_overhead_pct']}%",
        ])
    tbl = Table(data, colWidths=[8 * mm, 38 * mm, 25 * mm, 24 * mm, 22 * mm, 24 * mm, 30 * mm, 17 * mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (-1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#dcfce7")),  # green tint for #1
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fef3c7")),  # yellow for last
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<i>★ País con menor costo total para la empresa</i>", callout))
    story.append(Spacer(1, 12))

    # ========= COST BAR CHART (visual) =========
    story.append(Paragraph("Visualización del Costo Total al Empleador", section))
    if fx_info:
        max_cost = max(r["converted"]["total_cost_to_company"] for r in results if r.get("converted"))
        chart_unit = display_curr
    else:
        max_cost = max(r["employer"]["total_cost_to_company"] for r in results)
        chart_unit = "moneda local"
    chart_rows = []
    for r in results:
        if fx_info and r.get("converted"):
            value = r["converted"]["total_cost_to_company"]
            label = f"{display_curr} {value:,.0f}"
        else:
            value = r["employer"]["total_cost_to_company"]
            label = f"{r['currency_symbol']} {value:,.0f}"
        bar_pct = (value / max_cost) if max_cost else 0
        bar_width = max(2, int(bar_pct * 100))  # width 0-100mm
        bar_html = (f"<font color='#0ea5e9'>{'█' * (bar_width // 4)}</font>"
                    if r == cheapest else
                    f"<font color='#f59e0b'>{'█' * (bar_width // 4)}</font>"
                    if r == most_expensive else
                    f"<font color='#64748b'>{'█' * (bar_width // 4)}</font>")
        chart_rows.append([
            f"{r['flag']} {r['country_code']}",
            Paragraph(bar_html, body),
            label,
            f"+{r['employer']['cost_overhead_pct']}%",
        ])
    chart_tbl = Table(chart_rows, colWidths=[28 * mm, 78 * mm, 38 * mm, 18 * mm])
    chart_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e2e8f0")),
    ]))
    story.append(chart_tbl)
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<i>Escala relativa al máximo. Unidades: {chart_unit}.</i>", callout))
    story.append(Spacer(1, 12))

    # ========= RECOMMENDATION =========
    story.append(Paragraph("Recomendación Estratégica", section))
    savings_pct = round(((most_expensive["employer"]["total_cost_to_company"] -
                          cheapest["employer"]["total_cost_to_company"]) /
                         most_expensive["employer"]["total_cost_to_company"]) * 100, 2) if most_expensive["employer"]["total_cost_to_company"] else 0

    rec_text = (
        f"<b>Para una contratación a costo optimizado, contratar en {cheapest['flag']} {cheapest['country_name']} "
        f"genera ahorros de hasta {savings_pct}% comparado con {most_expensive['flag']} {most_expensive['country_name']}.</b><br/><br/>"
        f"<b>Consideraciones adicionales:</b><br/>"
        f"• Sistema de seguridad social: <b>{cheapest['social_security_system']}</b><br/>"
        f"• Agencia tributaria: <b>{cheapest['agency'] or 'N/A'}</b><br/>"
        f"• Moneda local: <b>{cheapest['currency']} ({cheapest['currency_symbol']})</b><br/>"
        f"• Overhead total: <b>+{cheapest['employer']['cost_overhead_pct']}%</b> (de los más bajos del análisis)<br/><br/>"
        f"<i>Recordatorio: este análisis es puramente fiscal. Decisiones de contratación deben considerar también: "
        f"disponibilidad de talento, costo de vida, marcos legales laborales, husos horarios, idioma, regulación de visados y políticas de teletrabajo.</i>"
    )
    story.append(Paragraph(rec_text, body))
    story.append(Spacer(1, 14))

    # ========= METHODOLOGY =========
    story.append(Paragraph("Metodología", section))
    methodology_text = (
        "Los cálculos se basan en los perfiles fiscales del motor multi-país de FortexaRH (28 países soportados, "
        "5 regiones). Las tasas de seguridad social y bandas de impuesto sobre la renta se aplican según el perfil "
        "vigente del país. El costo total empleador incluye salario bruto + todas las contribuciones patronales obligatorias "
        "(salud, pensión, riesgo laboral, prestaciones sociales según país)."
    )
    if fx_info:
        methodology_text += (
            f" Las cifras convertidas usan tasas de cambio en vivo de <b>{fx_info['rate_source']}</b> "
            f"(actualizadas máx. cada hora)."
        )
    methodology_text += (
        " <i>Este informe es un análisis comparativo de referencia. Para cumplimiento fiscal específico de cada país "
        "consulte siempre con un contador local certificado.</i>"
    )
    story.append(Paragraph(methodology_text, body))

    # Footer info
    story.append(Spacer(1, 14))
    footer_data = [[
        Paragraph(
            f"<font size=8 color='#94a3b8'>Generado por <b>FortexaRH</b> · Motor Fiscal Multi-País · "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</font>",
            body
        )
    ]]
    footer_tbl = Table(footer_data, colWidths=[170 * mm])
    footer_tbl.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#94a3b8")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(footer_tbl)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    filename = f"AnalisisFiscalComparativo_{len(results)}paises_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
