"""
DGII / TSS native XLSX template generators — FortexaRH

These endpoints produce REAL .xlsx files that mirror the structure of
the official Excel templates published by:
  - TSS (Tesorería de la Seguridad Social): SUIR+ v5.3 Autodeterminación,
    v5.1 Novedades, v1.4 Bonificación.
  - DGII: IR-4 (Cálculo de Retenciones Mensuales del Asalariado).

The legacy tab-delimited exports in ``dgii_monthly.py`` are kept for
back-compat. UIs that want the OFFICIAL formats (which SUIR+/DGII portals
import directly) should call these endpoints.

All endpoints:
  - Are DR-only (HTTP 400 for other countries).
  - Take ``year`` + ``month`` query params (NOT period_id) so they consolidate
    quincenal payrolls.
  - Sit under ``/api/dgii-reports/native/...``.
"""
from __future__ import annotations

import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from config import db
from routes.country_config import COUNTRY_PROFILES
from routes.dgii_monthly import _consolidate_month, _require_dr
from utils.auth import get_current_user


router = APIRouter(prefix="/dgii-reports/native", tags=["DGII Native Templates"])


# ===================== STYLE HELPERS =====================

_HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
_HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
_TITLE_FONT = Font(bold=True, size=12)
_SUBTITLE_FONT = Font(bold=True, italic=True, size=10, color="808080")
_BORDER = Border(
    left=Side(style="thin", color="BFBFBF"),
    right=Side(style="thin", color="BFBFBF"),
    top=Side(style="thin", color="BFBFBF"),
    bottom=Side(style="thin", color="BFBFBF"),
)


def _split_name(full_name: str) -> tuple[str, str, str]:
    """SUIR+ wants Names / 1st surname / 2nd surname in 3 separate columns."""
    parts = (full_name or "").strip().split()
    if not parts:
        return "", "", ""
    if len(parts) == 1:
        return parts[0], "", ""
    if len(parts) == 2:
        return parts[0], parts[1], ""
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    # 4+ parts: assume first 2 = nombres, then 1st & 2nd apellido
    return f"{parts[0]} {parts[1]}", parts[-2], parts[-1]


def _autosize(ws, max_width: int = 30) -> None:
    for col_cells in ws.columns:
        col_letter = get_column_letter(col_cells[0].column)
        max_len = 0
        for cell in col_cells:
            v = cell.value
            if v is None:
                continue
            length = len(str(v))
            if length > max_len:
                max_len = length
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, 10), max_width)


# ===================== TSS AUTODETERMINACIÓN v5.3 =====================


@router.get("/tss-autodeterminacion-v53")
async def tss_autodeterminacion_v53(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
):
    """Generate the official TSS Autodeterminación v5.3 XLSX (SUIR+ ready).

    Layout follows the official Plantilla-Excel-Archivo-de-Autodeterminacion-v5.3.xls:
      Header: Tipo Archivo / RNC / Período / # de Empleados (rows 5-9)
      Columns 11-12: TRABAJADORES (SDSS / DGII / INFOTEP groups)
        Clave Nómina | Tipo Doc | Número Doc | Nombres | 1er. Apellido | 2do. Apellido |
        Sexo | Fecha Nacimiento | Salario Cotizable | Aporte Voluntario | Salario ISR |
        Tipo Ingreso | Otras Remuneraciones | RNC/Cédula Agente Ret | Remuneración Otros |
        Saldo a favor (Saldo 13) | Regalía Pascual | Preaviso/Cesantía | Retención Pensión |
        Salario INFOTEP
    """
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "TSS Autodeterminación v5.3")

    data = await _consolidate_month(company_id, year, month)
    if not data["rows"]:
        raise HTTPException(status_code=404, detail="No hay datos de nómina para el mes seleccionado")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    rnc = (company.get("rnc") or "").replace("-", "")

    wb = Workbook()
    ws = wb.active
    ws.title = "Plantilla de Autodeterminación"

    # Header block (mirrors the official template positions)
    ws["A5"] = "Plantilla de Archivo AutoDeterminación"
    ws["A5"].font = _TITLE_FONT
    ws["F6"] = "Ver. 5.3"
    ws["F6"].font = _SUBTITLE_FONT
    ws["A6"] = "Tipo de Archivo:"
    ws["B6"] = "AM"  # Autodeterminación Mensual
    ws["A7"] = "RNC o Cédula:"
    ws["B7"] = rnc
    ws["A8"] = "Período:"
    ws["B8"] = f"{int(month):02d}{int(year)}"
    ws["E8"] = "<-- MMAAAA"
    ws["E8"].font = _SUBTITLE_FONT
    ws["C10"] = "# de Empleados:"
    ws["E10"] = len(data["rows"])

    # Column group headers (row 11)
    ws.cell(row=11, column=2,  value="TRABAJADORES").font = _TITLE_FONT
    ws.cell(row=11, column=10, value="SDSS").font = _TITLE_FONT
    ws.cell(row=11, column=14, value="DGII").font = _TITLE_FONT
    ws.cell(row=11, column=21, value="INFOTEP").font = _TITLE_FONT

    # Detail headers (rows 12-13, merged conceptually)
    headers = [
        ("Clave\nNómina",         "B"),
        ("Tipo\nDoc.",            "C"),
        ("Número\nDocumento",     "D"),
        ("Nombres",               "E"),
        ("1er. Apellido",         "F"),
        ("2do. Apellido",         "G"),
        ("Sexo",                  "H"),
        ("Fecha\nNacimiento",     "I"),
        ("Salario\nCotizable",    "J"),
        ("Aporte\nVoluntario",    "K"),
        ("Salario\nISR",          "L"),
        ("Tipo\nIngreso",         "M"),
        ("Otras\nRemuneraciones", "N"),
        ("RNC/Céd.\nAgente Ret",  "O"),
        ("Remuneración\nOtros Agentes",  "P"),
        ("Saldo a favor\ndel período", "Q"),
        ("Regalía Pascual\n(Saldo 13)", "R"),
        ("Preaviso, Cesantía,\nViático e Indemnizaciones", "S"),
        ("Retención Pensión\nAlimenticia", "T"),
        ("Salario\nINFOTEP", "U"),
    ]
    for label, col in headers:
        cell = ws[f"{col}12"]
        cell.value = label
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = _BORDER

    ws.row_dimensions[12].height = 36
    ws.freeze_panes = "A13"

    # Data rows
    start_row = 13
    for idx, r in enumerate(data["rows"]):
        cedula = (r.get("employee_document") or "").replace("-", "")
        # Look up the employee for sex / DOB / payroll_clave
        emp = await db.employees.find_one(
            {"employee_id": r["employee_id"], "company_id": company_id},
            {"_id": 0, "gender": 1, "birth_date": 1, "payroll_clave": 1, "salary": 1, "id_type": 1, "tipo_ingreso": 1},
        ) or {}

        nombres, ape1, ape2 = _split_name(r.get("employee_name", ""))
        gender = (emp.get("gender") or "M").upper()[:1]
        if gender not in ("M", "F"):
            gender = "M"
        birth = emp.get("birth_date") or ""
        # Format DD/MM/YYYY if ISO
        if isinstance(birth, str) and len(birth) >= 10 and birth[4] == "-":
            birth = f"{birth[8:10]}/{birth[5:7]}/{birth[0:4]}"
        id_type = (emp.get("id_type") or "C")[:1].upper()  # C=Cédula, P=Pasaporte, N=NSS
        if id_type not in ("C", "P", "N"):
            id_type = "C"

        # ISR taxable monthly = gross - SFS - AFP
        gross = float(r.get("gross_salary") or 0)
        salario_isr = round(gross - float(r.get("sfs_employee") or 0) - float(r.get("afp_employee") or 0), 2)

        # Tipo Ingreso = 'Normal' por defecto (catálogo SUIR+)
        tipo_ingreso = emp.get("tipo_ingreso") or "Normal"

        row_data = [
            emp.get("payroll_clave") or str(idx + 1),    # Clave Nómina
            id_type,                                      # Tipo Doc.
            cedula,                                       # Número Documento
            nombres, ape1, ape2,
            gender,
            birth,
            f"{gross:.2f}",                              # Salario Cotizable
            "0.00",                                      # Aporte Voluntario
            f"{salario_isr:.2f}",                        # Salario ISR
            tipo_ingreso,                                 # Tipo Ingreso
            "0.00",                                       # Otras Remuneraciones
            "",                                           # RNC/Céd Agente Ret (Otros)
            "0.00",                                       # Remuneración Otros Agentes
            "0.00",                                       # Saldo a favor del período
            "0.00",                                       # Regalía Pascual (Saldo 13)
            "0.00",                                       # Preaviso/Cesantía/Viático
            "0.00",                                       # Retención Pensión Alimenticia
            f"{gross:.2f}",                              # Salario INFOTEP
        ]
        for col_idx, value in enumerate(row_data, start=2):  # B = col 2
            cell = ws.cell(row=start_row + idx, column=col_idx, value=value)
            cell.border = _BORDER
            if col_idx >= 9 and isinstance(value, str) and value.replace(".", "").replace("-", "").isdigit():
                cell.alignment = Alignment(horizontal="right")

    _autosize(ws, max_width=24)

    # Auxiliary catalog sheets (mirrors the official template)
    aux = wb.create_sheet("Catalogos")
    aux["A1"] = "TARCHIVO"; aux["B1"] = "TDOC"; aux["C1"] = "SEXO"; aux["D1"] = "TINGRESO"
    for cell in (aux["A1"], aux["B1"], aux["C1"], aux["D1"]):
        cell.font = _HEADER_FONT; cell.fill = _HEADER_FILL
    tarchivo = [("AM", "Autodeterminación Mensual"), ("AR", "Autodeterminación Rectificativa")]
    tdoc = [("C", "Cédula"), ("P", "Pasaporte"), ("N", "NSS / Otro")]
    sexos = [("M", "Masculino"), ("F", "Femenino")]
    tingresos = [
        "Normal",
        "Trabajador ocasional (no fijo)",
        "Asalariado por hora o labora tiempo parcial",
        "No laboró mes completo por razones varias",
        "Salario prorrateado semanal/bisemanal",
        "Pensionado antes de la Ley 87-01",
        "Exento por Ley de pago al SDSS",
        "Trabajador con salario sectorizado",
    ]
    for i, (code, desc) in enumerate(tarchivo, start=2):
        aux.cell(row=i, column=1, value=f"{code} — {desc}")
    for i, (code, desc) in enumerate(tdoc, start=2):
        aux.cell(row=i, column=2, value=f"{code} — {desc}")
    for i, (code, desc) in enumerate(sexos, start=2):
        aux.cell(row=i, column=3, value=f"{code} — {desc}")
    for i, ti in enumerate(tingresos, start=2):
        aux.cell(row=i, column=4, value=ti)
    _autosize(aux, max_width=50)

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    filename = f"TSS_Autodeterminacion_v53_{rnc}_{int(month):02d}{int(year)}.xlsx"
    return Response(
        content=out.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ===================== IR-4 OFFICIAL =====================


@router.get("/ir4-official")
async def ir4_official(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
):
    """Generate the OFFICIAL DGII IR-4 XLSX (Cálculo Retenciones Mensuales Asalariado).

    Mirrors the column layout of the official IR-4.xls:
      A. No.
      B. Apellidos y Nombres Completos
      C. Cédula / RNC
      D. Sueldos pagados por el agente de retención
      E. Otras remuneraciones pagadas por el agente de retención
      F. Remuneraciones pagadas por otros empleadores
      G. Total Pagado en el Mes (D + E + F)
      H. Retención Seguridad Social
      I. Sueldos y otros pagos Sujetos a Retención (G - H)
      J. Liquidación Período
      K. Saldo a favor del Asalariado
      L. Nuevo Saldo a favor Asalariado a compensar
      M. Diferencia a Pagar
    """
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "IR-4 oficial")

    data = await _consolidate_month(company_id, year, month)
    if not data["rows"]:
        raise HTTPException(status_code=404, detail="No hay datos de nómina para el mes seleccionado")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}

    wb = Workbook()
    ws = wb.active
    ws.title = "IR-4"

    # Header block (mirrors official)
    ws["D2"] = "DIRECCIÓN GENERAL DE IMPUESTOS INTERNOS"
    ws["D2"].font = Font(bold=True, size=13)
    ws["D3"] = "CÁLCULO DE LAS RETENCIONES MENSUALES DEL ASALARIADO  (IR-4)"
    ws["D3"].font = _TITLE_FONT

    ws["A5"] = "AGENTE DE RETENCIÓN"
    ws["A5"].font = Font(bold=True)
    ws["B5"] = company.get("name", "")
    ws["G5"] = "RNC"
    ws["G5"].font = Font(bold=True)
    ws["H5"] = company.get("rnc", "")

    ws["A6"] = "DESDE"; ws["A6"].font = Font(bold=True)
    ws["B6"] = f"{int(month):02d}/{int(year)}"
    ws["D6"] = "HASTA"; ws["D6"].font = Font(bold=True)
    ws["E6"] = f"{int(month):02d}/{int(year)}"

    # Section banners
    ws["A8"] = "IDENTIFICACIÓN DEL ASALARIADO"
    ws["A8"].font = _TITLE_FONT
    ws["D8"] = "REMUNERACIONES PERCIBIDAS"
    ws["D8"].font = _TITLE_FONT

    # Column headers (rows 9-10)
    columns = [
        ("No.",                                                             "A"),
        ("Apellidos y Nombres Completos",                                   "B"),
        ("Cédula / RNC",                                                    "C"),
        ("C. Sueldos pagados por el\nAgente de Retención",                  "D"),
        ("D. Otras remuneraciones\npagadas por el Agente de Retención",     "E"),
        ("E. Remuneraciones pagadas\npor otros empleadores",                "F"),
        ("F. Total Pagado en el Mes\n(C + D + E)",                          "G"),
        ("G. Retención\nSeguridad Social",                                  "H"),
        ("H. Sueldos y otros pagos\nSujetos a Retención (F - G)",           "I"),
        ("I. Liquidación\nPeríodo",                                         "J"),
        ("J. Saldo a favor\ndel Asalariado",                                "K"),
        ("K. Nuevo Saldo a favor\nAsalariado a compensar",                  "L"),
        ("L. Diferencia\na Pagar",                                          "M"),
    ]
    for label, col in columns:
        cell = ws[f"{col}10"]
        cell.value = label
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = _BORDER
    ws.row_dimensions[10].height = 42
    ws.freeze_panes = "A11"

    # Data rows
    total_sueldos = 0.0
    total_seg_social = 0.0
    total_retencion = 0.0
    for idx, r in enumerate(data["rows"], start=1):
        row = 10 + idx
        sueldos = float(r.get("base_salary") or 0)  # C
        otras = float(r.get("commissions") or 0) + float(r.get("bonuses") or 0) + \
                float(r.get("overtime") or 0) + float(r.get("other_income") or 0) + \
                float(r.get("income_novelties") or 0)  # D
        otros_emp = 0.0  # E (no manejamos otros empleadores)
        total_pagado = sueldos + otras + otros_emp  # F
        ret_seg = float(r.get("sfs_employee") or 0) + float(r.get("afp_employee") or 0)  # G
        sujetos = total_pagado - ret_seg  # H
        liquidacion = float(r.get("isr") or 0)  # I

        total_sueldos += sueldos
        total_seg_social += ret_seg
        total_retencion += liquidacion

        values = [
            idx,
            r.get("employee_name", ""),
            r.get("employee_document", ""),
            sueldos,
            otras,
            otros_emp,
            total_pagado,
            ret_seg,
            sujetos,
            liquidacion,
            0.0,  # J
            0.0,  # K
            liquidacion,  # L (diferencia a pagar)
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col_idx, value=value)
            cell.border = _BORDER
            if isinstance(value, (int, float)) and col_idx >= 4:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")

    # Totals row
    totals_row = 11 + len(data["rows"])
    ws.cell(row=totals_row, column=2, value="TOTALES").font = Font(bold=True)
    ws.cell(row=totals_row, column=4, value=total_sueldos).font = Font(bold=True)
    ws.cell(row=totals_row, column=4).number_format = "#,##0.00"
    ws.cell(row=totals_row, column=8, value=total_seg_social).font = Font(bold=True)
    ws.cell(row=totals_row, column=8).number_format = "#,##0.00"
    ws.cell(row=totals_row, column=10, value=total_retencion).font = Font(bold=True)
    ws.cell(row=totals_row, column=10).number_format = "#,##0.00"
    ws.cell(row=totals_row, column=13, value=total_retencion).font = Font(bold=True)
    ws.cell(row=totals_row, column=13).number_format = "#,##0.00"

    _autosize(ws, max_width=24)
    # Force wider Name column
    ws.column_dimensions["B"].width = 32

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    rnc = (company.get("rnc") or "").replace("-", "")
    filename = f"IR4_Oficial_{rnc}_{int(month):02d}{int(year)}.xlsx"
    return Response(
        content=out.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
