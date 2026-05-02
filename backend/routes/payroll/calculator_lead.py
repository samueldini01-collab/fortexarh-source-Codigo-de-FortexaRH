"""Lead capture + PDF report for the public payroll calculator — iter245.

Powers the landing-page lead magnet:
    user inputs salary/country → sees breakdown → enters email → receives
    a branded PDF copy. Email is stored as a marketing lead in
    ``db.payroll_calculator_leads`` for follow-up.

Public endpoints (no auth):
- ``POST /api/payroll/calculator/lead``        — store lead, return PDF URL.
- ``POST /api/payroll/calculator/pdf``         — inline: compute + store lead + return PDF bytes.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import db
from routes.country_config import COUNTRY_PROFILES

from . import router
from .calculator import (
    CALCULATOR_DISCLAIMER,
    CALCULATOR_VERSION,
    _isr_for_country,
)


# ===================== MODELS =====================

class LeadCaptureRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=120)
    country: str = Field(..., min_length=2, max_length=3)
    gross_monthly: float = Field(..., gt=0)
    consent_marketing: bool = Field(default=False)


# ===================== SHARED BREAKDOWN COMPUTATION =====================

def _compute_breakdown(country_code: str, gross: float) -> dict:
    """Mirror of calculator.public_payroll_calculator — kept here as a pure
    function so the PDF endpoint and the lead endpoint share identical math."""
    profile = COUNTRY_PROFILES[country_code]
    ss = profile.get("social_security") or {}
    employee_deductions_cfg = ss.get("employee_deductions", []) or []
    employer_contributions_cfg = ss.get("employer_contributions", []) or []

    employee_breakdown = []
    total_employee_deductions = 0.0
    for ded in employee_deductions_cfg:
        rate = float(ded.get("rate", 0) or 0)
        cap = ded.get("cap")
        base = min(gross, float(cap)) if cap else gross
        amount = round(base * rate, 2)
        employee_breakdown.append({
            "code": ded.get("code", "SS"),
            "label": ded.get("label") or ded.get("name") or ded.get("code", "SS"),
            "rate": rate,
            "amount": amount,
        })
        total_employee_deductions += amount

    employer_breakdown = []
    total_employer_contributions = 0.0
    for con in employer_contributions_cfg:
        rate = float(con.get("rate", 0) or 0)
        cap = con.get("cap")
        base = min(gross, float(cap)) if cap else gross
        amount = round(base * rate, 2)
        employer_breakdown.append({
            "code": con.get("code", "SS-ER"),
            "label": con.get("label") or con.get("name") or con.get("code", "SS-ER"),
            "rate": rate,
            "amount": amount,
        })
        total_employer_contributions += amount

    isr_result = _isr_for_country(country_code, gross)
    isr_amount = float(isr_result.get("isr_monthly", 0) or 0)
    total_employee_deductions += isr_amount
    net_monthly = round(gross - total_employee_deductions, 2)
    fiscal_cost = round(gross + total_employer_contributions, 2)

    return {
        "profile": profile,
        "employee_breakdown": employee_breakdown,
        "employer_breakdown": employer_breakdown,
        "isr_amount": isr_amount,
        "isr_bracket": isr_result.get("tax_bracket", ""),
        "total_employee_deductions": total_employee_deductions,
        "total_employer_contributions": total_employer_contributions,
        "net_monthly": net_monthly,
        "fiscal_cost": fiscal_cost,
    }


# ===================== PDF BUILDER =====================

def _build_pdf(country_code: str, gross: float, full_name: Optional[str], breakdown: dict) -> bytes:
    profile = breakdown["profile"]
    currency_sym = profile.get("currency_symbol") or profile.get("currency", "")
    country_name = profile.get("name", country_code)
    flag = profile.get("flag", "")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title=f"FortexaRH — Cálculo de Nómina {country_code}",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "h1", parent=styles["Heading1"], fontSize=18, alignment=1,
        textColor=colors.HexColor("#0f172a"), spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "h2", parent=styles["Normal"], fontSize=11, alignment=1,
        textColor=colors.HexColor("#475569"), spaceAfter=14,
    )
    section = ParagraphStyle(
        "sec", parent=styles["Heading3"], fontSize=12,
        textColor=colors.HexColor("#0f172a"), spaceBefore=10, spaceAfter=4,
    )
    body = ParagraphStyle(
        "body", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#334155"), spaceAfter=4,
    )

    story = []
    story.append(Paragraph(
        f"CÁLCULO DE NÓMINA — {flag} {country_name.upper()}", h1,
    ))
    story.append(Paragraph(
        f"Generado por <b>FortexaRH</b> · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        h2,
    ))

    # Summary box
    recipient = full_name or "Beneficiario"
    summary = [
        ["Beneficiario", recipient],
        ["País", f"{flag} {country_name} ({country_code})"],
        ["Moneda", profile.get("currency", "")],
        ["Salario bruto mensual", f"{currency_sym}{gross:,.2f}"],
        ["Salario neto mensual",
         f"<b>{currency_sym}{breakdown['net_monthly']:,.2f}</b>"],
        ["Costo fiscal al empleador",
         f"{currency_sym}{breakdown['fiscal_cost']:,.2f}"],
    ]
    summary_rows = [[Paragraph(a, body), Paragraph(b, body)] for a, b in summary]
    t = Table(summary_rows, colWidths=[65 * mm, 100 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#94a3b8")),
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#dcfce7")),
    ]))
    story.append(t)

    # Employee deductions
    story.append(Paragraph("Deducciones del empleado", section))
    emp_rows = [["Concepto", "Tasa", f"Monto ({profile.get('currency', '')})"]]
    for d in breakdown["employee_breakdown"]:
        emp_rows.append([d["label"], f"{d['rate'] * 100:.2f}%", f"{currency_sym}{d['amount']:,.2f}"])
    emp_rows.append([
        f"ISR ({breakdown['isr_bracket']})",
        "—",
        f"{currency_sym}{breakdown['isr_amount']:,.2f}",
    ])
    emp_rows.append([
        "TOTAL deducciones empleado", "",
        f"{currency_sym}{breakdown['total_employee_deductions']:,.2f}",
    ])
    te = Table(emp_rows, colWidths=[90 * mm, 30 * mm, 45 * mm])
    te.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fef3c7")),
    ]))
    story.append(te)

    # Employer contributions
    story.append(Paragraph("Aportes patronales (a cargo del empleador)", section))
    er_rows = [["Concepto", "Tasa", f"Monto ({profile.get('currency', '')})"]]
    for c in breakdown["employer_breakdown"]:
        er_rows.append([c["label"], f"{c['rate'] * 100:.2f}%", f"{currency_sym}{c['amount']:,.2f}"])
    er_rows.append([
        "TOTAL aportes patronales", "",
        f"{currency_sym}{breakdown['total_employer_contributions']:,.2f}",
    ])
    tr = Table(er_rows, colWidths=[90 * mm, 30 * mm, 45 * mm])
    tr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fef3c7")),
    ]))
    story.append(tr)

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<i>Calculador versión {CALCULATOR_VERSION}. {CALCULATOR_DISCLAIMER}</i>", body,
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>FortexaRH</b> — Nómina y RRHH para los 28 países de América · "
        "<a href='https://fortexarh.com'>fortexarh.com</a>", body,
    ))

    doc.build(story)
    return buffer.getvalue()


# ===================== ENDPOINTS =====================

async def _record_lead(request: Request, payload: LeadCaptureRequest) -> dict:
    lead = {
        "lead_id": f"lead_{uuid.uuid4().hex[:16]}",
        "email": payload.email,
        "full_name": payload.full_name,
        "country": payload.country.upper(),
        "gross_monthly": payload.gross_monthly,
        "consent_marketing": bool(payload.consent_marketing),
        "source": "public_calculator",
        "user_agent": (request.headers.get("user-agent") or "")[:300],
        "ip_address": (request.client.host if request.client else None),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Upsert by email to avoid duplicates — refreshes last-used country/gross
    await db.payroll_calculator_leads.update_one(
        {"email": payload.email},
        {
            "$set": {
                "full_name": lead["full_name"],
                "country": lead["country"],
                "gross_monthly": lead["gross_monthly"],
                "consent_marketing": lead["consent_marketing"],
                "last_seen_at": lead["created_at"],
            },
            "$setOnInsert": {
                "lead_id": lead["lead_id"],
                "email": lead["email"],
                "source": lead["source"],
                "created_at": lead["created_at"],
            },
            "$inc": {"calculations_count": 1},
        },
        upsert=True,
    )
    stored = await db.payroll_calculator_leads.find_one({"email": payload.email}, {"_id": 0})
    return stored or lead


@router.post("/calculator/lead")
async def capture_calculator_lead(payload: LeadCaptureRequest, request: Request):
    """Store a marketing lead from the public calculator. Returns the lead's
    id + computed net salary so the UI can show confirmation.
    """
    country_code = payload.country.upper().strip()
    if country_code not in COUNTRY_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"País '{country_code}' no soportado",
        )
    lead = await _record_lead(request, payload)
    breakdown = _compute_breakdown(country_code, payload.gross_monthly)
    return {
        "success": True,
        "lead_id": lead["lead_id"],
        "calculations_count": lead.get("calculations_count", 1),
        "net_monthly": breakdown["net_monthly"],
        "message": "Lead capturado. Revise el PDF en la siguiente página.",
    }


@router.post("/calculator/pdf")
async def calculator_pdf(payload: LeadCaptureRequest, request: Request):
    """Compute breakdown, store the lead, and return the branded PDF."""
    country_code = payload.country.upper().strip()
    if country_code not in COUNTRY_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"País '{country_code}' no soportado",
        )
    await _record_lead(request, payload)
    breakdown = _compute_breakdown(country_code, payload.gross_monthly)
    pdf_bytes = _build_pdf(country_code, payload.gross_monthly, payload.full_name, breakdown)
    filename = (
        f"FortexaRH_Nomina_{country_code}_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
