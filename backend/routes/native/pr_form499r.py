"""🇵🇷 Puerto Rico — Form 499R-2/W-2PR (annual W-2 PR) PDF."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import db
from utils.auth import get_current_user

from . import router
from ._helpers import require_country


@router.get("/pr/form-499r")
async def generate_pr_form_499r(year: int, current_user: dict = Depends(get_current_user)):
    """🇵🇷 Puerto Rico — Form 499R-2/W-2PR (Comprobante de Retención anual).
    Resumen anual por empleado. Filed with Hacienda PR by January 31.
    """
    company_id = current_user.get("company_id")
    await require_country(company_id, "PR", "Form 499R-2/W-2PR")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": year}, {"_id": 0}
    ).to_list(50)
    period_ids = [p["period_id"] for p in periods]
    if not period_ids:
        raise HTTPException(status_code=404, detail=f"No hay nóminas para {year}")
    entries = await db.payroll_entries.find(
        {"company_id": company_id, "period_id": {"$in": period_ids}}, {"_id": 0}
    ).to_list(10000)

    employee_ids = list({e["employee_id"] for e in entries})
    employees_data = await db.employees.find(
        {"company_id": company_id, "employee_id": {"$in": employee_ids}}, {"_id": 0}
    ).to_list(5000)
    emp_map = {e["employee_id"]: e for e in employees_data}

    per_emp: dict[str, dict[str, float]] = {}
    for entry in entries:
        eid = entry["employee_id"]
        if eid not in per_emp:
            per_emp[eid] = {"wages": 0.0, "tax_withheld": 0.0, "ss_emp": 0.0, "med_emp": 0.0}
        per_emp[eid]["wages"] += entry.get("gross_salary", 0)
        per_emp[eid]["tax_withheld"] += entry.get("isr", 0)
        per_emp[eid]["ss_emp"] += entry.get("sfs_employee", 0)
        per_emp[eid]["med_emp"] += entry.get("afp_employee", 0)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Form 499R-2 W-2PR {year}",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=14, alignment=1,
                        textColor=colors.HexColor("#0f172a"), spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Normal"], fontSize=10, alignment=1,
                        textColor=colors.HexColor("#475569"), spaceAfter=8)
    section = ParagraphStyle("sec", parent=styles["Heading3"], fontSize=11,
                             textColor=colors.HexColor("#0f172a"), spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9, spaceAfter=4)
    story = []

    company_name = company.get("company_name") or company.get("name") or "Patrono"
    ein = company.get("rnc") or company.get("tax_id") or "00-0000000"

    story.append(Paragraph(f"FORM 499R-2/W-2PR — COMPROBANTE DE RETENCIÓN {year}", h1))
    story.append(Paragraph("Departamento de Hacienda · Estado Libre Asociado de Puerto Rico", h2))

    story.append(Paragraph("Información del Patrono", section))
    employer_data = [
        ["Nombre del patrono", company_name],
        ["Número Patronal (EIN)", ein],
        ["Año natural", str(year)],
        ["Total empleados", str(len(per_emp))],
    ]
    t = Table(employer_data, colWidths=[60 * mm, 120 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#94a3b8")),
    ]))
    story.append(t)

    story.append(Spacer(1, 8))
    story.append(Paragraph("Comprobantes individuales", section))
    rows = [["#", "SS / ID", "Empleado", "Salarios", "Retención IRPR", "SS Emp.", "Medicare Emp."]]
    totals = {"w": 0.0, "th": 0.0, "ss": 0.0, "med": 0.0}
    for idx, (eid, t_data) in enumerate(per_emp.items(), 1):
        emp = emp_map.get(eid, {})
        ssn = (emp.get("ssn") or emp.get("document_number") or "")[:11]
        name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        rows.append([
            str(idx), ssn, name,
            f"${t_data['wages']:,.2f}", f"${t_data['tax_withheld']:,.2f}",
            f"${t_data['ss_emp']:,.2f}", f"${t_data['med_emp']:,.2f}",
        ])
        totals["w"] += t_data["wages"]
        totals["th"] += t_data["tax_withheld"]
        totals["ss"] += t_data["ss_emp"]
        totals["med"] += t_data["med_emp"]
    rows.append(["", "", "TOTAL",
                 f"${totals['w']:,.2f}", f"${totals['th']:,.2f}",
                 f"${totals['ss']:,.2f}", f"${totals['med']:,.2f}"])
    t2 = Table(rows, colWidths=[10 * mm, 28 * mm, 50 * mm, 25 * mm, 28 * mm, 22 * mm, 25 * mm], repeatRows=1)
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dcfce7")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(t2)

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<i>Generado por FortexaRH el {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
        f"Fecha de radicación: 31 de enero {year + 1} (Hacienda PR).</i>",
        body,
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    safe_ein = "".join(c for c in ein if c.isalnum())
    filename = f"Form499R_{safe_ein}_{year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
