"""
Native Country-Specific Fiscal Reports - FortexaRH

Implements the official flat-file formats required by each country's tax/SS authority.

Currently implemented:
  - 🇨🇴 Colombia: PILA UGPP (Planilla Integrada de Liquidación de Aportes)
  - 🇲🇽 México: IMSS SUA (Sistema Único de Autodeterminación) + INFONAVIT

Each format is generated based on payroll_entries + employee data + the country profile in country_config.

⚠️ DISCLAIMER: These are reference implementations of public format specifications.
Before submitting to official agencies, files must be validated by a local certified
accountant. FortexaRH is not responsible for rejected filings.
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from typing import Optional
from datetime import datetime, timezone
import io

from config import db
from utils.auth import get_current_user
from routes.country_config import COUNTRY_PROFILES, get_company_rates_flat
from routes.multi_country_reports import _collect_period_data

router = APIRouter(prefix="/native-reports", tags=["Native Fiscal Reports"])


# ===================== HELPERS =====================

async def _require_country(company_id: str, expected_country: str, format_name: str):
    """Guard: raise 400 if company's country doesn't match expected one."""
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    country_code = (company or {}).get("country", "DO")
    if country_code != expected_country:
        profile = COUNTRY_PROFILES.get(country_code, {})
        expected_profile = COUNTRY_PROFILES.get(expected_country, {})
        raise HTTPException(
            status_code=400,
            detail=f"{format_name} es un formato oficial de {expected_profile.get('name', expected_country)}. "
                   f"Su empresa está configurada como {profile.get('name', country_code)}. "
                   f"Cambie el país desde Configuración o use el Reporte Fiscal Universal."
        )
    return country_code


def _pad_str(s: str, length: int, align: str = "left", fill: str = " ") -> str:
    """Pad/truncate a string to exact length."""
    s = (s or "").strip()
    if len(s) > length:
        return s[:length]
    return s.ljust(length, fill) if align == "left" else s.rjust(length, fill)


def _pad_num(n, length: int, decimals: int = 0) -> str:
    """Pad a number with leading zeros, no decimal point. Used for monetary fields in TXT formats."""
    if n is None:
        n = 0
    if decimals > 0:
        # Multiply by 10^decimals and use as int
        val = int(round(float(n) * (10 ** decimals)))
    else:
        val = int(round(float(n)))
    s = str(abs(val))
    return s.rjust(length, "0")[:length]


def _clean_doc(doc: str) -> str:
    """Remove non-numeric chars from a document number."""
    return "".join(c for c in (doc or "") if c.isdigit())


# ===================== COLOMBIA: PILA UGPP =====================
# Format reference: Resolución 0454/2019 + 5050/2019 (UGPP)
# Two record types:
#   Type 1: Header (1 record per file) - 343 bytes
#   Type 2: Employee detail (1 record per employee) - 942 bytes

@router.get("/co/pila")
async def generate_co_pila(period: str, current_user: dict = Depends(get_current_user)):
    """Generate Colombia PILA (Planilla Integrada de Liquidación de Aportes) flat file.

    Format: TXT with two record types per UGPP Resolución 0454/2019.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "CO", "PILA UGPP")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    rates = await get_company_rates_flat(company_id)
    entries, emps, period_info = await _collect_period_data(company_id, period)

    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    nit = _clean_doc(company.get("rnc") or company.get("tax_id") or "0")
    company_name = (company.get("company_name") or company.get("name") or "EMPRESA")[:200]

    # Header (Type 1) - 343 bytes simplified
    period_str = period.replace("-", "")[:6]  # YYYYMM
    if len(period_str) < 6:
        period_str = datetime.now(timezone.utc).strftime("%Y%m")

    lines = []
    # ===== TIPO 1: HEADER =====
    header = []
    header.append(_pad_str("1", 1))                          # 1: Tipo registro
    header.append(_pad_str("E", 1))                          # 2: Modalidad planilla (E=Empresa)
    header.append(_pad_num("0", 10))                         # 3: Secuencia
    header.append(_pad_str("31", 2))                         # 4: Tipo aportante (31=Empresa privada)
    header.append(_pad_str("NI", 2))                         # 5: Tipo documento (NI=NIT)
    header.append(_pad_num(nit, 16))                         # 6: NIT
    header.append(_pad_str("0", 1))                          # 7: DV (dígito verificación, simplificado)
    header.append(_pad_str(company_name, 200))               # 8: Razón social
    header.append(_pad_str("CO", 2))                         # 9: País
    header.append(_pad_str(period_str, 6))                   # 10: Período pago salud (AAAAMM)
    header.append(_pad_str(period_str, 6))                   # 11: Período pago demás (AAAAMM)
    header.append(_pad_num(len(entries), 5))                 # 12: # empleados
    # Sums (simplified - 12 chars each)
    total_gross = sum(e.get("gross_salary", 0) for e in entries)
    total_salud_emp = sum(e.get("sfs_employee", 0) + e.get("sfs_employer", 0) for e in entries)  # SFS slot=SALUD
    total_pension = sum(e.get("afp_employee", 0) + e.get("afp_employer", 0) for e in entries)  # AFP slot=PENSION
    total_arl = sum(e.get("srl_employer", 0) for e in entries)
    total_ccf = sum(e.get("infotep_employer", 0) for e in entries)
    header.append(_pad_num(total_gross, 12))                 # 13: Total IBC
    header.append(_pad_num(total_pension, 12))               # 14: Total pensión
    header.append(_pad_num(total_salud_emp, 12))             # 15: Total salud
    header.append(_pad_num(total_arl, 12))                   # 16: Total ARL
    header.append(_pad_num(total_ccf, 12))                   # 17: Total CCF/parafiscales
    header.append(_pad_num(0, 12))                           # 18: Total ICBF (placeholder)
    header.append(_pad_num(0, 12))                           # 19: Total SENA (placeholder)
    header.append(_pad_num(total_gross + total_pension + total_salud_emp + total_arl + total_ccf, 12))  # 20: Total general
    header.append(_pad_str("01", 2))                         # 21: Forma presentación (01=Electrónica)
    header.append(_pad_str("N", 1))                          # 22: Mora (N=No)
    header.append(_pad_num(0, 9))                            # 23: Días mora
    header.append(_pad_str(period_str + "01", 8))            # 24: Fecha pago
    lines.append("".join(header))

    # ===== TIPO 2: EMPLOYEES =====
    salud_rate_emp = rates["sfs_employee_rate"]   # CO: SALUD 4%
    salud_rate_er = rates["sfs_employer_rate"]    # CO: SALUD_EMP 8.5%
    pension_rate_emp = rates["afp_employee_rate"]  # CO: PENSION 4%
    pension_rate_er = rates["afp_employer_rate"]   # CO: PENSION_EMP 12%
    arl_rate = rates["srl_employer_rate"]          # CO: ARL 0.522%
    ccf_rate = rates["infotep_employer_rate"]      # CO: CCF 4%

    for idx, entry in enumerate(entries, 1):
        emp = emps.get(entry.get("employee_id"), {})
        gross = float(entry.get("gross_salary", 0) or 0)
        first_name = (emp.get("first_name") or "").upper()[:20]
        last_name = (emp.get("last_name") or "").upper()
        # Split last_name into 1st and 2nd surname
        parts = last_name.split(" ", 1)
        primer_apellido = (parts[0] if parts else "")[:20]
        segundo_apellido = (parts[1] if len(parts) > 1 else "")[:30]
        doc = _clean_doc(emp.get("document_number") or "0")

        rec = []
        rec.append(_pad_str("2", 1))                                  # 1: Tipo registro
        rec.append(_pad_num(idx, 5))                                  # 2: Secuencia
        rec.append(_pad_str("CC", 2))                                 # 3: Tipo doc empleado (CC default)
        rec.append(_pad_num(doc, 16))                                 # 4: # documento
        rec.append(_pad_str(primer_apellido, 20))                     # 5: Primer apellido
        rec.append(_pad_str(segundo_apellido, 30))                    # 6: Segundo apellido
        rec.append(_pad_str(first_name, 20))                          # 7: Primer nombre
        rec.append(_pad_str("", 30))                                  # 8: Segundo nombre
        rec.append(_pad_str("DE", 2))                                 # 9: Tipo cotizante (DE=Dependiente)
        rec.append(_pad_str("00", 2))                                 # 10: Subtipo
        rec.append(_pad_str("X", 1) if False else _pad_str(" ", 1))   # 11: Extranjero no obligado
        rec.append(_pad_str(" ", 1))                                  # 12: Colombiano residente exterior
        rec.append(_pad_str("11", 2))                                 # 13: Código depto (11=Bogotá default)
        rec.append(_pad_str("001", 3))                                # 14: Código municipio
        rec.append(_pad_str(" ", 11))                                 # 15: Novedad ingreso (vacío)
        rec.append(_pad_str(" ", 11))                                 # 16: Novedad retiro (vacío)
        rec.append(_pad_str(" ", 11))                                 # 17: Variación salario permanente
        rec.append(_pad_str(" ", 11))                                 # 18: Variación transitoria
        rec.append(_pad_str(" ", 1))                                  # 19: Suspensión por licencia
        rec.append(_pad_str(" ", 1))                                  # 20: Incapacidad general
        rec.append(_pad_str(" ", 1))                                  # 21: Licencia maternidad
        rec.append(_pad_str(" ", 1))                                  # 22: Vacaciones / licencia remunerada
        rec.append(_pad_str(" ", 1))                                  # 23: Aportes voluntarios
        rec.append(_pad_str(" ", 1))                                  # 24: Variaciones
        rec.append(_pad_str(" ", 1))                                  # 25: Bonificación
        rec.append(_pad_str(" ", 1))                                  # 26: Días cotización corregir
        rec.append(_pad_str(" ", 1))                                  # 27: Tipo correcciones
        rec.append(_pad_num(0, 9))                                    # 28: Cotización pensión voluntaria
        rec.append(_pad_str(" ", 6))                                  # 29: Código adm. pensión (placeholder)
        rec.append(_pad_str(" ", 6))                                  # 30: Cód. adm. pensión traslado
        rec.append(_pad_str("EPS001", 6))                             # 31: Cód. EPS (placeholder)
        rec.append(_pad_str(" ", 6))                                  # 32: Cód. EPS traslado
        rec.append(_pad_str("CCF001", 6))                             # 33: Cód. CCF
        # Days
        rec.append(_pad_num(30, 2))                                   # 34: Días cotizados pensión
        rec.append(_pad_num(30, 2))                                   # 35: Días cotizados salud
        rec.append(_pad_num(30, 2))                                   # 36: Días cotizados ARL
        rec.append(_pad_num(30, 2))                                   # 37: Días cotizados CCF
        # IBC (Ingreso Base de Cotización) - 9 chars
        rec.append(_pad_num(gross, 9))                                # 38: IBC pensión
        rec.append(_pad_num(gross, 9))                                # 39: IBC salud
        rec.append(_pad_num(gross, 9))                                # 40: IBC ARL
        rec.append(_pad_num(gross, 9))                                # 41: IBC CCF
        rec.append(_pad_num(gross, 9))                                # 42: Tarifa salario integral
        # Tarifas en %, 7 chars con 4 decimales (ej: 0040000=4%)
        rec.append(_pad_num((pension_rate_emp + pension_rate_er) * 100, 7, decimals=4))  # 43: Tarifa pensión
        rec.append(_pad_num(float(entry.get("afp_employee", 0) or 0) + float(entry.get("afp_employer", 0) or 0), 9))  # 44: Cot. obligatoria pensión
        rec.append(_pad_num(0, 9))                                    # 45: Cot. voluntaria afiliado
        rec.append(_pad_num(0, 9))                                    # 46: Cot. voluntaria empleador
        rec.append(_pad_num(0, 9))                                    # 47: Aporte solidaridad
        rec.append(_pad_num(0, 9))                                    # 48: Aporte subsistencia
        rec.append(_pad_num(0, 9))                                    # 49: Total pensión
        rec.append(_pad_num((salud_rate_emp + salud_rate_er) * 100, 7, decimals=4))  # 50: Tarifa salud
        rec.append(_pad_num(float(entry.get("sfs_employee", 0) or 0) + float(entry.get("sfs_employer", 0) or 0), 9))  # 51: Cotización salud
        rec.append(_pad_num(0, 9))                                    # 52: UPC adicional
        rec.append(_pad_num(0, 9))                                    # 53: Valor incapacidades
        rec.append(_pad_num(0, 9))                                    # 54: Valor licencia maternidad
        rec.append(_pad_num(arl_rate * 100, 9, decimals=4))           # 55: Tarifa ARL
        rec.append(_pad_str("1", 1))                                  # 56: Centro trabajo (clase riesgo I)
        rec.append(_pad_num(float(entry.get("srl_employer", 0) or 0), 9))  # 57: Cot. ARL
        rec.append(_pad_num(ccf_rate * 100, 7, decimals=4))           # 58: Tarifa CCF
        rec.append(_pad_num(float(entry.get("infotep_employer", 0) or 0), 9))  # 59: Aporte CCF
        rec.append(_pad_num(0, 9))                                    # 60: Aporte SENA
        rec.append(_pad_num(0, 9))                                    # 61: Aporte ICBF
        rec.append(_pad_num(0, 9))                                    # 62: Aporte ESAP
        rec.append(_pad_num(0, 9))                                    # 63: Aporte MEN
        rec.append(_pad_str(" ", 9))                                  # 64: CIIU
        rec.append(_pad_str(" ", 11))                                 # 65: Fecha ingreso
        rec.append(_pad_str(" ", 11))                                 # 66: Fecha retiro
        rec.append(_pad_str(" ", 11))                                 # 67: Fecha inicio licencia
        rec.append(_pad_str(" ", 11))                                 # 68: Fecha fin licencia
        rec.append(_pad_str(" ", 11))                                 # 69: Fecha inicio incapacidad
        rec.append(_pad_str(" ", 11))                                 # 70: Fecha fin incapacidad
        # Pad to 942 chars
        line = "".join(rec)
        line = (line + " " * 942)[:942]
        lines.append(line)

    content = "\n".join(lines) + "\n"
    filename = f"PILA_{nit}_{period_str}.txt"
    return Response(
        content=content.encode("latin-1", errors="replace"),  # ASCII-extended (PILA spec)
        media_type="text/plain; charset=iso-8859-1",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== MEXICO: IMSS SUA + INFONAVIT =====================
# Format reference: SUA - Sistema Único de Autodeterminación (IMSS)
# Two files commonly required:
#   1. SUA_Movimientos.txt - employee movements (alta, baja, modificaciones)
#   2. SUA_Cuotas.txt - bimonthly contribution liquidation

@router.get("/mx/imss-cuotas")
async def generate_mx_imss_cuotas(period: str, current_user: dict = Depends(get_current_user)):
    """Generate Mexico IMSS-SUA contributions file (cuotas obrero-patronales).

    Format: TXT fixed-width per IMSS SUA specification.
    Each record represents an employee's monthly contribution.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "MX", "IMSS SUA Cuotas")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    entries, emps, period_info = await _collect_period_data(company_id, period)

    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    rfc = (company.get("rnc") or company.get("tax_id") or "XAXX010101000")[:13].upper()
    registro_patronal = company.get("registro_patronal") or "A0000000000"
    period_str = period.replace("-", "")[:6]

    lines = []
    for entry in entries:
        emp = emps.get(entry.get("employee_id"), {})
        nss = _clean_doc(emp.get("nss") or emp.get("document_number") or "0")[:11]
        first_name = (emp.get("first_name") or "").upper()
        last_name = (emp.get("last_name") or "").upper()
        parts = last_name.split(" ", 1)
        ap_paterno = (parts[0] if parts else "")[:27]
        ap_materno = (parts[1] if len(parts) > 1 else "")[:27]
        gross = float(entry.get("gross_salary", 0) or 0)
        # SDI = Salario Diario Integrado (gross / 30)
        sdi = round(gross / 30, 2)

        # IMSS slots (rates from MX profile):
        # Employee: IMSS_EMP (~2.375% combined), ISR
        # Employer: IMSS_EMP_PATRON (~10.525%), INFONAVIT (5%), AFORE (RCV 2%)
        imss_obrero = float(entry.get("sfs_employee", 0) or 0)  # Slot 0 employee
        imss_patron = float(entry.get("sfs_employer", 0) or 0)  # Slot 0 employer
        rcv = float(entry.get("afp_employer", 0) or 0)          # Slot 1 employer (AFORE)
        infonavit = float(entry.get("srl_employer", 0) or 0)    # Slot 2 employer
        # Default 30 días cotizados
        dias_cot = 30

        rec = []
        rec.append(_pad_str(registro_patronal, 11))      # Registro patronal
        rec.append(_pad_str(nss, 11))                    # NSS
        rec.append(_pad_str(rfc, 13))                    # RFC trabajador (placeholder = empresa)
        rec.append(_pad_str("AAAA000000AAA", 18))        # CURP (placeholder)
        rec.append(_pad_str(ap_paterno, 27))             # Apellido paterno
        rec.append(_pad_str(ap_materno, 27))             # Apellido materno
        rec.append(_pad_str(first_name, 27))             # Nombre
        rec.append(_pad_str("1", 1))                     # Tipo trabajador (1=permanente)
        rec.append(_pad_str("00", 2))                    # Jornada/semana
        rec.append(_pad_num(sdi * 100, 8))               # SDI en centavos (8 dígitos)
        rec.append(_pad_str(period_str, 6))              # Período (AAAAMM)
        rec.append(_pad_num(dias_cot, 2))                # Días cotizados
        rec.append(_pad_num(0, 2))                       # Días incapacidad
        rec.append(_pad_num(0, 2))                       # Días ausentismo
        rec.append(_pad_num(imss_obrero * 100, 10))      # Cuota obrero (centavos)
        rec.append(_pad_num(imss_patron * 100, 10))      # Cuota patronal (centavos)
        rec.append(_pad_num(rcv * 100, 10))              # Aportación RCV (AFORE)
        rec.append(_pad_num(infonavit * 100, 10))        # Aportación INFONAVIT
        rec.append(_pad_num(0, 10))                      # Crédito INFONAVIT (descuento)
        rec.append(_pad_num((imss_obrero + imss_patron + rcv + infonavit) * 100, 12))  # Total
        lines.append("".join(rec))

    content = "\n".join(lines) + "\n"
    filename = f"IMSS_SUA_Cuotas_{rfc}_{period_str}.txt"
    return Response(
        content=content.encode("latin-1", errors="replace"),
        media_type="text/plain; charset=iso-8859-1",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/mx/infonavit")
async def generate_mx_infonavit(period: str, current_user: dict = Depends(get_current_user)):
    """Generate Mexico INFONAVIT bimonthly contribution file.

    Format: TXT fixed-width per INFONAVIT spec.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "MX", "INFONAVIT")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    entries, emps, _ = await _collect_period_data(company_id, period)

    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    rfc = (company.get("rnc") or company.get("tax_id") or "XAXX010101000")[:13].upper()
    registro_patronal = company.get("registro_patronal") or "A0000000000"
    period_str = period.replace("-", "")[:6]

    lines = []
    for entry in entries:
        emp = emps.get(entry.get("employee_id"), {})
        nss = _clean_doc(emp.get("nss") or emp.get("document_number") or "0")[:11]
        first_name = (emp.get("first_name") or "").upper()
        last_name = (emp.get("last_name") or "").upper()
        parts = last_name.split(" ", 1)
        ap_paterno = (parts[0] if parts else "")[:27]
        ap_materno = (parts[1] if len(parts) > 1 else "")[:27]
        gross = float(entry.get("gross_salary", 0) or 0)
        sdi = round(gross / 30, 2)
        infonavit = float(entry.get("srl_employer", 0) or 0)

        rec = []
        rec.append(_pad_str(registro_patronal, 11))      # Registro patronal
        rec.append(_pad_str(nss, 11))                    # NSS
        rec.append(_pad_str(rfc, 13))                    # RFC
        rec.append(_pad_str(ap_paterno, 27))
        rec.append(_pad_str(ap_materno, 27))
        rec.append(_pad_str(first_name, 27))
        rec.append(_pad_num(sdi * 100, 8))               # SDI
        rec.append(_pad_str(period_str, 6))              # Período bimestral
        rec.append(_pad_num(60, 2))                      # Días bimestre (max 60)
        rec.append(_pad_num(infonavit * 100, 10))        # Aportación 5%
        rec.append(_pad_num(0, 10))                      # Amortización crédito
        rec.append(_pad_str(" ", 10))                    # # crédito (vacío si no aplica)
        rec.append(_pad_num(infonavit * 100, 10))        # Total a pagar
        lines.append("".join(rec))

    content = "\n".join(lines) + "\n"
    filename = f"INFONAVIT_{rfc}_{period_str}.txt"
    return Response(
        content=content.encode("latin-1", errors="replace"),
        media_type="text/plain; charset=iso-8859-1",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== CATALOG: NATIVE FORMATS BY COUNTRY =====================

NATIVE_FORMATS = {
    "DO": [
        {"code": "TSS_AUTODET", "name": "TSS Autodeterminación (Tipo A)", "agency": "TSS", "frequency": "monthly", "endpoint": "/api/dgii-reports/tss/autodeterminacion", "implemented": True},
        {"code": "TSS_NOVEDADES", "name": "TSS Novedades (Tipo N)", "agency": "TSS", "frequency": "monthly", "endpoint": "/api/dgii-reports/tss/novedades", "implemented": True},
        {"code": "IR3", "name": "IR-3 (Retenciones ISR)", "agency": "DGII", "frequency": "monthly", "endpoint": "/api/dgii-reports/ir3", "implemented": True},
        {"code": "IR17", "name": "IR-17 (Anual)", "agency": "DGII", "frequency": "annual", "endpoint": "/api/dgii-reports/ir17", "implemented": True},
    ],
    "CO": [
        {"code": "PILA", "name": "PILA UGPP (Planilla Integrada)", "agency": "UGPP", "frequency": "monthly", "endpoint": "/api/native-reports/co/pila", "implemented": True},
    ],
    "MX": [
        {"code": "IMSS_SUA", "name": "IMSS SUA Cuotas", "agency": "IMSS", "frequency": "monthly", "endpoint": "/api/native-reports/mx/imss-cuotas", "implemented": True},
        {"code": "INFONAVIT", "name": "INFONAVIT Bimestral", "agency": "INFONAVIT", "frequency": "bimonthly", "endpoint": "/api/native-reports/mx/infonavit", "implemented": True},
    ],
    "US": [{"code": "FORM_941", "name": "IRS Form 941 (PDF)", "agency": "IRS", "frequency": "quarterly", "endpoint": "/api/native-reports/us/form-941", "implemented": True}],
    "ES": [
        {"code": "MODELO_111", "name": "Modelo 111 (Retenciones IRPF)", "agency": "AEAT", "frequency": "quarterly", "endpoint": "/api/native-reports/es/modelo-111", "implemented": True},
        {"code": "TC1", "name": "TC1 FAN (Cotización SS)", "agency": "TGSS", "frequency": "monthly", "endpoint": "/api/native-reports/es/tc1", "implemented": True},
    ],
    "GB": [{"code": "RTI_FPS", "name": "HMRC RTI FPS (XML)", "agency": "HMRC", "frequency": "monthly", "endpoint": "/api/native-reports/gb/rti-fps", "implemented": True}],
    "FR": [{"code": "DSN", "name": "DSN (Déclaration Sociale Nominative)", "agency": "URSSAF", "frequency": "monthly", "endpoint": "/api/native-reports/fr/dsn", "implemented": True}],
    "CA": [{"code": "T4", "name": "T4 Statement of Remuneration", "agency": "CRA", "frequency": "annual", "endpoint": "/api/native-reports/ca/t4", "implemented": True}],
    "BR": [{"code": "ESOCIAL", "name": "eSocial S-1200", "agency": "Receita Federal", "frequency": "monthly", "endpoint": "/api/native-reports/br/esocial", "implemented": True}],
    "AR": [{"code": "F931", "name": "F.931 AFIP", "agency": "AFIP", "frequency": "monthly", "endpoint": "/api/native-reports/ar/f931", "implemented": True}],
    "CL": [{"code": "PREVIRED", "name": "PreviRed", "agency": "PreviRed", "frequency": "monthly", "implemented": False}],
    "PE": [{"code": "PLAME", "name": "PLAME SUNAT", "agency": "SUNAT", "frequency": "monthly", "implemented": False}],
    "EC": [{"code": "IESS_PLANILLA", "name": "IESS Planilla", "agency": "IESS", "frequency": "monthly", "implemented": False}],
    "VE": [{"code": "IVSS_FORMA", "name": "IVSS Forma", "agency": "IVSS", "frequency": "monthly", "implemented": False}],
    "BO": [{"code": "F110", "name": "Formulario 110", "agency": "SIN", "frequency": "monthly", "implemented": False}],
    "PY": [{"code": "F109", "name": "Formulario 109 IPS", "agency": "IPS", "frequency": "monthly", "implemented": False}],
    "UY": [{"code": "BPS_1146", "name": "BPS Formulario 1146", "agency": "BPS", "frequency": "monthly", "implemented": False}],
    "GY": [{"code": "NIS", "name": "NIS Returns", "agency": "NIS", "frequency": "monthly", "implemented": False}],
    "SR": [{"code": "SZF", "name": "SZF Filing", "agency": "SZF", "frequency": "monthly", "implemented": False}],
    "CR": [{"code": "CCSS_PLANILLA", "name": "CCSS Planilla", "agency": "CCSS", "frequency": "monthly", "implemented": False}],
    "SV": [{"code": "F1_ISSS", "name": "Formulario F-1 ISSS", "agency": "ISSS", "frequency": "monthly", "implemented": False}],
    "GT": [{"code": "IGSS_PLANILLA", "name": "IGSS Planilla", "agency": "IGSS", "frequency": "monthly", "implemented": False}],
    "HN": [{"code": "IHSS_PLANILLA", "name": "IHSS Planilla", "agency": "IHSS", "frequency": "monthly", "implemented": False}],
    "NI": [{"code": "INSS_PLANILLA", "name": "INSS Planilla", "agency": "INSS", "frequency": "monthly", "implemented": False}],
    "PA": [{"code": "CSS_PLANILLA", "name": "CSS Planilla", "agency": "CSS", "frequency": "monthly", "implemented": False}],
    "CU": [{"code": "ONAT_FORM", "name": "ONAT Form", "agency": "ONAT", "frequency": "monthly", "implemented": False}],
    "HT": [{"code": "ONA_DECLAR", "name": "ONA Déclaration", "agency": "ONA", "frequency": "monthly", "implemented": False}],
    "PR": [{"code": "FORM_499R", "name": "Form 499 R", "agency": "Hacienda PR", "frequency": "annual", "implemented": False}],
}


@router.get("/catalog")
async def get_native_formats_catalog(current_user: dict = Depends(get_current_user)):
    """Return the global catalog of native fiscal formats per country with implementation status."""
    summary = {
        "total_countries": len(NATIVE_FORMATS),
        "total_formats": sum(len(v) for v in NATIVE_FORMATS.values()),
        "implemented_formats": sum(1 for v in NATIVE_FORMATS.values() for f in v if f.get("implemented")),
        "countries": []
    }
    for code, formats in NATIVE_FORMATS.items():
        profile = COUNTRY_PROFILES.get(code, {})
        impl_count = sum(1 for f in formats if f.get("implemented"))
        summary["countries"].append({
            "code": code,
            "name": profile.get("name", code),
            "flag": profile.get("flag", ""),
            "region": profile.get("region", ""),
            "currency": profile.get("currency", ""),
            "agency": (profile.get("income_tax") or {}).get("agency", ""),
            "social_security_system": (profile.get("social_security") or {}).get("system_name", ""),
            "formats": formats,
            "implemented_count": impl_count,
            "total_count": len(formats),
            "compliance_status": "complete" if impl_count == len(formats) else ("partial" if impl_count > 0 else "universal_only"),
        })
    return summary


# ===================== UNITED STATES: IRS FORM 941 =====================
# Quarterly Federal Tax Return for Employers
# https://www.irs.gov/forms-pubs/about-form-941
# Reports: federal income tax withheld, SS wages/tax, Medicare wages/tax

from fastapi import Query
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _us_quarter_period(period: str):
    """Convert period (YYYY-MM or YYYY-Qn) into (year, quarter, months_list)."""
    period = (period or "").strip().upper()
    if "Q" in period:
        year_part, q_part = period.split("Q")
        year = int(year_part.rstrip("-"))
        quarter = int(q_part)
    else:
        # YYYY-MM
        year, month = period.split("-")
        year = int(year)
        month = int(month)
        quarter = (month - 1) // 3 + 1
    months = [(quarter - 1) * 3 + i + 1 for i in range(3)]
    return year, quarter, months


@router.get("/us/form-941")
async def generate_us_form_941(period: str, current_user: dict = Depends(get_current_user)):
    """Generate US IRS Form 941 (Quarterly Federal Tax Return) as a PDF report.

    Aggregates payroll data for the quarter and produces a PDF that mirrors the
    structure of Form 941 with all calculated values ready for filing.

    Period accepts YYYY-Qn (e.g. 2026-Q1) or YYYY-MM (auto-derives quarter).
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "US", "IRS Form 941")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    year, quarter, months = _us_quarter_period(period)

    # Aggregate all payroll periods in this quarter
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": year, "month": {"$in": months}},
        {"_id": 0}
    ).to_list(50)
    period_ids = [p["period_id"] for p in periods]
    if not period_ids:
        raise HTTPException(status_code=404, detail=f"No hay nóminas para el trimestre Q{quarter} de {year}")

    entries = await db.payroll_entries.find(
        {"company_id": company_id, "period_id": {"$in": period_ids}},
        {"_id": 0}
    ).to_list(5000)

    # Distinct employees in the quarter
    employee_ids = list({e["employee_id"] for e in entries})
    num_employees = len(employee_ids)

    # Aggregate amounts
    total_wages = sum(e.get("gross_salary", 0) for e in entries)
    total_fed_tax = sum(e.get("isr", 0) for e in entries)  # Federal income tax withheld
    # SS = sfs slot for US (6.2% emp + 6.2% er = 12.4%)
    ss_wages = total_wages
    ss_emp = sum(e.get("sfs_employee", 0) for e in entries)
    ss_er = sum(e.get("sfs_employer", 0) for e in entries)
    ss_total = ss_emp + ss_er
    # Medicare = afp slot for US (1.45% emp + 1.45% er = 2.9%)
    medicare_wages = total_wages
    medicare_emp = sum(e.get("afp_employee", 0) for e in entries)
    medicare_er = sum(e.get("afp_employer", 0) for e in entries)
    medicare_total = medicare_emp + medicare_er

    line_3 = round(total_fed_tax, 2)
    line_5a_taxable_ss_wages = round(ss_wages, 2)
    line_5a_ss_tax = round(ss_total, 2)
    line_5c_medicare_wages = round(medicare_wages, 2)
    line_5c_medicare_tax = round(medicare_total, 2)
    line_5e_total_ss_medicare = round(line_5a_ss_tax + line_5c_medicare_tax, 2)
    line_6_total_taxes = round(line_3 + line_5e_total_ss_medicare, 2)
    line_10_total_taxes_after_adj = line_6_total_taxes  # No adjustments in this simplified version
    line_12_total_taxes = line_10_total_taxes_after_adj  # No deposit-related modifications
    line_13a_deposits = 0.0  # User must input separately
    line_14_balance_due = round(max(0.0, line_12_total_taxes - line_13a_deposits), 2)

    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Form 941 Q{quarter} {year}"
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=16, alignment=1,
                        textColor=colors.HexColor("#1e293b"), spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Normal"], fontSize=10, alignment=1,
                        textColor=colors.HexColor("#475569"), spaceAfter=10)
    section = ParagraphStyle("sec", parent=styles["Heading3"], fontSize=11,
                             textColor=colors.HexColor("#0f172a"), spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9,
                          textColor=colors.HexColor("#334155"), spaceAfter=4)
    story = []

    company_name = company.get("company_name") or company.get("name") or "Employer"
    ein = (company.get("rnc") or company.get("tax_id") or "00-0000000")
    address = company.get("address") or "—"

    story.append(Paragraph("FORM 941 — EMPLOYER'S QUARTERLY FEDERAL TAX RETURN", h1))
    story.append(Paragraph(f"Reporting Quarter: <b>Q{quarter} {year}</b> · Department of the Treasury · Internal Revenue Service", h2))

    # Employer info
    story.append(Paragraph("Employer Information", section))
    employer_data = [
        ["Name", company_name],
        ["EIN (Employer Identification Number)", ein],
        ["Trade name", company.get("trade_name") or "—"],
        ["Address", address],
        ["Quarter", f"Q{quarter} ({year}) — Months: {', '.join(str(m) for m in months)}"],
        ["Number of employees who received wages", str(num_employees)],
    ]
    t = Table(employer_data, colWidths=[70 * mm, 110 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#94a3b8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)

    # Part 1: Answer these questions for this quarter
    story.append(Spacer(1, 6))
    story.append(Paragraph("Part 1 — Answer these questions for this quarter", section))

    p1_data = [
        ["Line", "Description", "Amount (USD)"],
        ["1", "Number of employees who received wages, tips, or other compensation", f"{num_employees}"],
        ["2", "Wages, tips, and other compensation", f"${total_wages:,.2f}"],
        ["3", "Federal income tax withheld from wages, tips, and other compensation", f"${line_3:,.2f}"],
        ["4", "If no wages subject to social security or Medicare tax, check here", "☐"],
        ["5a", "Taxable social security wages × 0.124", f"${line_5a_taxable_ss_wages:,.2f}  →  ${line_5a_ss_tax:,.2f}"],
        ["5b", "Taxable social security tips × 0.124", "$0.00"],
        ["5c", "Taxable Medicare wages and tips × 0.029", f"${line_5c_medicare_wages:,.2f}  →  ${line_5c_medicare_tax:,.2f}"],
        ["5d", "Taxable wages & tips subject to Additional Medicare Tax × 0.009", "$0.00"],
        ["5e", "Total social security and Medicare taxes (Add 5a + 5b + 5c + 5d)", f"${line_5e_total_ss_medicare:,.2f}"],
        ["5f", "Section 3121(q) Notice and Demand—Tax due on unreported tips", "$0.00"],
        ["6", "Total taxes before adjustments (Add lines 3 + 5e + 5f)", f"${line_6_total_taxes:,.2f}"],
        ["7", "Current quarter's adjustment for fractions of cents", "$0.00"],
        ["8", "Current quarter's adjustment for sick pay", "$0.00"],
        ["9", "Current quarter's adjustments for tips and group-term life insurance", "$0.00"],
        ["10", "Total taxes after adjustments (Combine lines 6 through 9)", f"${line_10_total_taxes_after_adj:,.2f}"],
        ["11", "Qualified small business payroll tax credit for increasing research activities", "$0.00"],
        ["12", "Total taxes after adjustments and credits (Subtract line 11 from line 10)", f"${line_12_total_taxes:,.2f}"],
        ["13a", "Total deposits for this quarter (manual input required)", f"${line_13a_deposits:,.2f}"],
        ["14", "Balance due (If line 12 is more than line 13a)", f"${line_14_balance_due:,.2f}"],
        ["15", "Overpayment (If line 13a is more than line 12)", "$0.00"],
    ]
    t1 = Table(p1_data, colWidths=[15 * mm, 115 * mm, 50 * mm])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        # Highlight key totals
        ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#fef3c7")),
        ("BACKGROUND", (0, 10), (-1, 10), colors.HexColor("#fef3c7")),
        ("BACKGROUND", (0, 12), (-1, 12), colors.HexColor("#fef3c7")),
        ("BACKGROUND", (0, 16), (-1, 16), colors.HexColor("#dcfce7")),
        ("FONTNAME", (0, 16), (-1, 16), "Helvetica-Bold"),
        ("BACKGROUND", (0, 19), (-1, 19), colors.HexColor("#fee2e2")),
        ("FONTNAME", (0, 19), (-1, 19), "Helvetica-Bold"),
    ]))
    story.append(t1)

    # Part 2: Deposit schedule
    story.append(Spacer(1, 8))
    story.append(Paragraph("Part 2 — Tell us about your deposit schedule and tax liability for this quarter", section))
    p2_text = (
        "<b>Line 16:</b> Check one of the following:<br/>"
        "☐ Line 12 was less than $2,500 — no schedule required.<br/>"
        "☐ You were a monthly schedule depositor — fill the breakdown below.<br/>"
        "☐ You were a semi-weekly schedule depositor — complete Schedule B (Form 941).<br/>"
    )
    story.append(Paragraph(p2_text, body))

    # Monthly liability breakdown
    monthly_breakdown = []
    for m in months:
        m_periods = [p["period_id"] for p in periods if p.get("month") == m]
        m_entries = [e for e in entries if e.get("period_id") in m_periods]
        m_wages = sum(e.get("gross_salary", 0) for e in m_entries)
        m_isr = sum(e.get("isr", 0) for e in m_entries)
        m_ss = sum(e.get("sfs_employee", 0) + e.get("sfs_employer", 0) for e in m_entries)
        m_med = sum(e.get("afp_employee", 0) + e.get("afp_employer", 0) for e in m_entries)
        m_total = round(m_isr + m_ss + m_med, 2)
        month_name = ["—", "January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"][m]
        monthly_breakdown.append([month_name, f"${m_wages:,.2f}", f"${m_isr:,.2f}",
                                  f"${m_ss:,.2f}", f"${m_med:,.2f}", f"${m_total:,.2f}"])
    monthly_breakdown.append(["Total Q" + str(quarter), f"${total_wages:,.2f}", f"${total_fed_tax:,.2f}",
                              f"${ss_total:,.2f}", f"${medicare_total:,.2f}", f"${line_12_total_taxes:,.2f}"])
    t2 = Table([["Month", "Wages", "Fed. Income Tax", "SS Tax", "Medicare Tax", "Total Liability"]] + monthly_breakdown,
               colWidths=[35 * mm, 28 * mm, 28 * mm, 25 * mm, 28 * mm, 28 * mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dcfce7")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(t2)

    # Footer disclaimer
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<i>Generated by FortexaRH on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
        f"This is a calculation summary intended to facilitate filling out the official IRS Form 941. "
        f"Before filing, validate all figures with a Certified Public Accountant (CPA) and submit through "
        f"https://www.irs.gov/payments or your authorized e-file provider.</i>",
        body
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    filename = f"Form941_Q{quarter}_{year}_{ein.replace('-', '')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== SPAIN: MODELO 111 =====================
# Quarterly retentions on personal income (IRPF)
# Filed with AEAT (Agencia Estatal de Administración Tributaria)
# https://sede.agenciatributaria.gob.es/

def _es_quarter_period(period: str):
    """Convert period (YYYY-MM or YYYY-Qn) → (year, quarter, months)."""
    period = (period or "").strip().upper()
    if "T" in period or "Q" in period:
        sep = "T" if "T" in period else "Q"
        year_part, q_part = period.split(sep)
        year = int(year_part.rstrip("-"))
        quarter = int(q_part)
    else:
        year, month = period.split("-")
        year = int(year)
        quarter = (int(month) - 1) // 3 + 1
    months = [(quarter - 1) * 3 + i + 1 for i in range(3)]
    return year, quarter, months


@router.get("/es/modelo-111")
async def generate_es_modelo_111(period: str, current_user: dict = Depends(get_current_user)):
    """Generate Spain Modelo 111 (IRPF Quarterly Retentions).

    AEAT format: TXT plain file with header line + summary line.
    Period: YYYY-Tn (e.g. 2026-T1) or YYYY-MM (auto-derives quarter).
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "ES", "Modelo 111 IRPF")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    year, quarter, months = _es_quarter_period(period)

    # Aggregate quarter
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": year, "month": {"$in": months}},
        {"_id": 0}
    ).to_list(50)
    period_ids = [p["period_id"] for p in periods]
    if not period_ids:
        raise HTTPException(status_code=404, detail=f"No hay nóminas para el trimestre {quarter}T de {year}")
    entries = await db.payroll_entries.find(
        {"company_id": company_id, "period_id": {"$in": period_ids}},
        {"_id": 0}
    ).to_list(5000)

    nif = (company.get("rnc") or company.get("tax_id") or "B00000000")[:9].upper()
    company_name = (company.get("company_name") or company.get("name") or "EMPRESA")[:40]

    # Section "Rendimientos del trabajo" (most common case)
    num_perceptors = len({e["employee_id"] for e in entries})
    base_retenciones = sum(e.get("gross_salary", 0) for e in entries)
    importe_retenciones = sum(e.get("isr", 0) for e in entries)

    # Modelo 111 structure (simplified, AEAT-style fixed format)
    # See https://sede.agenciatributaria.gob.es for the official formal description
    lines = []

    # === REGISTRO TIPO 1: DECLARANTE === (250 chars approx)
    rec1 = []
    rec1.append("1")                                          # Tipo registro
    rec1.append("111")                                        # Modelo
    rec1.append(str(year))                                    # Ejercicio (4)
    rec1.append(_pad_str(nif, 9))                             # NIF declarante
    rec1.append(_pad_str(company_name, 40))                   # Razón social
    rec1.append(_pad_str("T", 1))                             # Tipo periodo (T=Trimestral)
    rec1.append(_pad_str(f"{quarter}T", 2))                   # Período (1T/2T/3T/4T)
    rec1.append(_pad_num(num_perceptors, 5))                  # # perceptores totales
    rec1.append(_pad_num(base_retenciones * 100, 13))         # Base total (en céntimos)
    rec1.append(_pad_num(importe_retenciones * 100, 13))      # Importe total retenciones (en céntimos)
    rec1.append(_pad_num(0, 13))                              # Resultado anterior declaración complementaria
    rec1.append(_pad_num(importe_retenciones * 100, 13))      # Resultado a ingresar
    rec1.append(_pad_str("I", 1))                             # Tipo declaración (I=Ingreso, N=Negativa, X=Sin actividad)
    rec1.append(_pad_str(" ", 200))                           # Reservado/relleno
    lines.append("".join(rec1))

    # === REGISTRO TIPO 2: PERCEPTORES (one per employee) ===
    employee_ids = list({e["employee_id"] for e in entries})
    employees_data = await db.employees.find(
        {"company_id": company_id, "employee_id": {"$in": employee_ids}},
        {"_id": 0}
    ).to_list(5000)
    emp_map = {e["employee_id"]: e for e in employees_data}

    # Sum per employee
    employee_totals = {}
    for entry in entries:
        eid = entry["employee_id"]
        if eid not in employee_totals:
            employee_totals[eid] = {"base": 0.0, "ret": 0.0}
        employee_totals[eid]["base"] += entry.get("gross_salary", 0)
        employee_totals[eid]["ret"] += entry.get("isr", 0)

    for eid, totals in employee_totals.items():
        emp = emp_map.get(eid, {})
        nif_emp = (emp.get("document_number") or "00000000A")[:9].upper()
        first_name = (emp.get("first_name") or "").upper()[:20]
        last_name = (emp.get("last_name") or "").upper()
        parts = last_name.split(" ", 1)
        ap1 = (parts[0] if parts else "")[:20]
        ap2 = (parts[1] if len(parts) > 1 else "")[:20]
        rec2 = []
        rec2.append("2")                                         # Tipo registro
        rec2.append("111")                                       # Modelo
        rec2.append(str(year))                                   # Ejercicio
        rec2.append(_pad_str(nif, 9))                            # NIF declarante
        rec2.append(_pad_str(nif_emp, 9))                        # NIF perceptor
        rec2.append(_pad_str(ap1, 20))                           # Apellido 1
        rec2.append(_pad_str(ap2, 20))                           # Apellido 2
        rec2.append(_pad_str(first_name, 20))                    # Nombre
        rec2.append(_pad_str("01", 2))                           # Clave (01 = Rendimientos del trabajo)
        rec2.append(_pad_str(" ", 1))                            # Subclave
        rec2.append(_pad_num(totals["base"] * 100, 13))          # Base perceptor (céntimos)
        rec2.append(_pad_num(totals["ret"] * 100, 13))           # Retención perceptor (céntimos)
        rec2.append(_pad_str(" ", 100))                          # Reservado
        lines.append("".join(rec2))

    content = "\n".join(lines) + "\n"
    filename = f"Modelo111_{nif}_{year}T{quarter}.txt"
    return Response(
        content=content.encode("latin-1", errors="replace"),
        media_type="text/plain; charset=iso-8859-1",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== SPAIN: TC1 FAN =====================
# Monthly Social Security contribution settlement
# Filed with TGSS (Tesorería General de la Seguridad Social) — Sistema RED
# Format: FAN (Fichero de Apoyo de Notificaciones)

@router.get("/es/tc1")
async def generate_es_tc1(period: str, current_user: dict = Depends(get_current_user)):
    """Generate Spain TC1 FAN (Monthly Social Security Settlement) for TGSS Sistema RED.

    Format: TXT plain file with header (registro 01) + employees (registro 02) + footer (registro 99).
    Period: YYYY-MM.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "ES", "TC1 FAN")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    rates = await get_company_rates_flat(company_id)

    entries, emps, period_info = await _collect_period_data(company_id, period)
    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    nif = (company.get("rnc") or company.get("tax_id") or "B00000000")[:9].upper()
    ccc = company.get("ccc") or "28000000000"  # Código Cuenta Cotización (default Madrid)
    period_str = period.replace("-", "")[:6]

    company_name = (company.get("company_name") or company.get("name") or "EMPRESA")[:40]

    lines = []

    # === REGISTRO 01: CABECERA ===
    rec_h = []
    rec_h.append(_pad_str("01", 2))
    rec_h.append(_pad_str("FAN", 3))                          # Tipo fichero
    rec_h.append(_pad_str(period_str, 6))                     # Período liquidación
    rec_h.append(_pad_str(ccc, 11))                           # Código Cuenta Cotización
    rec_h.append(_pad_str(nif, 9))                            # NIF empresa
    rec_h.append(_pad_str(company_name, 40))                  # Razón social
    rec_h.append(_pad_str(datetime.now(timezone.utc).strftime("%Y%m%d"), 8))  # Fecha generación
    rec_h.append(_pad_str("L00", 3))                          # Tipo liquidación (L00=Normal)
    rec_h.append(_pad_str(" ", 50))                           # Reservado
    lines.append("".join(rec_h))

    # === REGISTRO 02: TRABAJADORES ===
    total_base = 0.0
    total_cuota_emp = 0.0
    total_cuota_er = 0.0
    for entry in entries:
        emp = emps.get(entry.get("employee_id"), {})
        naf = (emp.get("naf") or emp.get("document_number") or "000000000000")[:12]  # Núm. afiliación SS
        ipf = (emp.get("document_number") or "00000000A")[:9].upper()  # NIF/NIE trabajador
        first_name = (emp.get("first_name") or "").upper()[:20]
        last_name = (emp.get("last_name") or "").upper()
        parts = last_name.split(" ", 1)
        ap1 = (parts[0] if parts else "")[:20]
        ap2 = (parts[1] if len(parts) > 1 else "")[:20]

        gross = float(entry.get("gross_salary", 0) or 0)
        # ES rates: emp_emp ~6.45% (CC + Desempleo + FP), er ~30%
        cuota_emp = float(entry.get("sfs_employee", 0) or 0) + float(entry.get("afp_employee", 0) or 0)
        cuota_er = (float(entry.get("sfs_employer", 0) or 0) +
                    float(entry.get("afp_employer", 0) or 0) +
                    float(entry.get("srl_employer", 0) or 0) +
                    float(entry.get("infotep_employer", 0) or 0))

        rec = []
        rec.append(_pad_str("02", 2))                         # Tipo registro
        rec.append(_pad_str(naf, 12))                         # Núm. afiliación SS
        rec.append(_pad_str(ipf, 9))                          # NIF/NIE
        rec.append(_pad_str(ap1, 20))                         # Apellido 1
        rec.append(_pad_str(ap2, 20))                         # Apellido 2
        rec.append(_pad_str(first_name, 20))                  # Nombre
        rec.append(_pad_str("111", 3))                        # CNAE/Tipo contrato
        rec.append(_pad_str("00", 2))                         # Coeficiente tiempo parcial
        rec.append(_pad_num(30, 2))                           # Días cotizados
        rec.append(_pad_num(gross * 100, 11))                 # Base cotización CC (céntimos)
        rec.append(_pad_num(gross * 100, 11))                 # Base cotización contingencias profesionales
        rec.append(_pad_num(gross * 100, 11))                 # Base AT/EP
        rec.append(_pad_num(cuota_emp * 100, 11))             # Cuota trabajador
        rec.append(_pad_num(cuota_er * 100, 11))              # Cuota empresa
        rec.append(_pad_num((cuota_emp + cuota_er) * 100, 11))  # Cuota total
        rec.append(_pad_str(" ", 50))                         # Reservado
        lines.append("".join(rec))

        total_base += gross
        total_cuota_emp += cuota_emp
        total_cuota_er += cuota_er

    # === REGISTRO 99: TOTALES ===
    rec_f = []
    rec_f.append(_pad_str("99", 2))
    rec_f.append(_pad_num(len(entries), 7))                   # # trabajadores
    rec_f.append(_pad_num(total_base * 100, 13))              # Base total
    rec_f.append(_pad_num(total_cuota_emp * 100, 13))         # Total cuota trabajador
    rec_f.append(_pad_num(total_cuota_er * 100, 13))          # Total cuota empresa
    rec_f.append(_pad_num((total_cuota_emp + total_cuota_er) * 100, 13))  # Total a ingresar
    rec_f.append(_pad_str(" ", 50))
    lines.append("".join(rec_f))

    content = "\n".join(lines) + "\n"
    filename = f"TC1_FAN_{ccc}_{period_str}.txt"
    return Response(
        content=content.encode("latin-1", errors="replace"),
        media_type="text/plain; charset=iso-8859-1",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== UNITED KINGDOM: HMRC RTI FPS (XML) =====================
# Real Time Information - Full Payment Submission
# Submitted to HMRC each pay day
# https://www.gov.uk/guidance/run-payroll-using-rti

import xml.etree.ElementTree as ET
from xml.dom import minidom


def _xml_pretty(root) -> str:
    """Pretty-print an ElementTree root."""
    rough = ET.tostring(root, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")


@router.get("/gb/rti-fps")
async def generate_gb_rti_fps(period: str, current_user: dict = Depends(get_current_user)):
    """Generate UK HMRC RTI FPS (Full Payment Submission) XML.

    Format: XML per HMRC RTI specification (simplified).
    Period: YYYY-MM.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "GB", "HMRC RTI FPS")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    entries, emps, period_info = await _collect_period_data(company_id, period)
    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    employer_paye = company.get("paye_reference") or "123/AB12345"
    accounts_office = company.get("accounts_office_reference") or "123PA12345678"
    company_name = (company.get("company_name") or company.get("name") or "Employer Ltd")[:56]
    period_str = period.replace("-", "")[:6]

    # Get tax year (UK tax year: April 6 → April 5)
    year, month = period.split("-")
    year = int(year)
    month = int(month)
    if month >= 4:
        tax_year_end = year + 1
    else:
        tax_year_end = year
    tax_year_str = f"{tax_year_end - 1}-{str(tax_year_end)[2:]}"  # e.g., "2025-26"

    # Build XML
    root = ET.Element("GovTalkMessage")
    root.set("xmlns", "http://www.govtalk.gov.uk/CM/envelope")
    header = ET.SubElement(root, "Header")
    msg_details = ET.SubElement(header, "MessageDetails")
    ET.SubElement(msg_details, "Class").text = "HMRC-PAYE-RTI-FPS"
    ET.SubElement(msg_details, "Qualifier").text = "request"
    ET.SubElement(msg_details, "Function").text = "submit"
    ET.SubElement(msg_details, "GatewayTimestamp").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    body = ET.SubElement(root, "Body")
    ir_envelope = ET.SubElement(body, "IRenvelope")
    ir_envelope.set("xmlns", "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/24-25/1")
    ir_header = ET.SubElement(ir_envelope, "IRheader")
    keys = ET.SubElement(ir_header, "Keys")
    key_taxoffice = ET.SubElement(keys, "Key")
    key_taxoffice.set("Type", "TaxOfficeNumber")
    key_taxoffice.text = employer_paye.split("/")[0]
    key_taxoffice2 = ET.SubElement(keys, "Key")
    key_taxoffice2.set("Type", "TaxOfficeReference")
    key_taxoffice2.text = employer_paye.split("/")[-1]
    ET.SubElement(ir_header, "PeriodEnd").text = f"{year}-{int(month):02d}-30"

    fps = ET.SubElement(ir_envelope, "FullPaymentSubmission")
    employer = ET.SubElement(fps, "EmpRefs")
    ET.SubElement(employer, "OfficeNo").text = employer_paye.split("/")[0]
    ET.SubElement(employer, "PayeRef").text = employer_paye.split("/")[-1]
    ET.SubElement(employer, "AOref").text = accounts_office

    # Aggregate per-employee data
    employee_totals = {}
    for entry in entries:
        eid = entry["employee_id"]
        if eid not in employee_totals:
            employee_totals[eid] = {"gross": 0.0, "tax": 0.0, "ni_emp": 0.0, "ni_er": 0.0, "net": 0.0}
        employee_totals[eid]["gross"] += entry.get("gross_salary", 0)
        employee_totals[eid]["tax"] += entry.get("isr", 0)
        # GB SS slots: NIC_EMP (12% over £242 threshold), NIC_EMP_EMP (13.8%)
        employee_totals[eid]["ni_emp"] += entry.get("sfs_employee", 0)
        employee_totals[eid]["ni_er"] += entry.get("sfs_employer", 0)
        employee_totals[eid]["net"] += entry.get("net_salary", 0)

    for eid, totals in employee_totals.items():
        emp = emps.get(eid, {})
        emp_xml = ET.SubElement(fps, "Employee")
        nino = (emp.get("nino") or emp.get("national_insurance_number") or "")[:9].upper()
        emp_details = ET.SubElement(emp_xml, "EmployeeDetails")
        if nino:
            ET.SubElement(emp_details, "NINO").text = nino
        name = ET.SubElement(emp_details, "Name")
        ET.SubElement(name, "Fore").text = (emp.get("first_name") or "").strip()[:35]
        ET.SubElement(name, "Sur").text = (emp.get("last_name") or "").strip()[:35]
        # Address (simplified)
        if emp.get("address"):
            addr = ET.SubElement(emp_details, "Address")
            ET.SubElement(addr, "Line").text = emp["address"][:35]

        employment = ET.SubElement(emp_xml, "Employment")
        ET.SubElement(employment, "PayId").text = (emp.get("employee_id") or "")[:35]
        ET.SubElement(employment, "PaymentToANonIndividual").text = "no"
        ET.SubElement(employment, "FiguresToDate").text = ""

        figures = ET.SubElement(employment, "PaymentToDate")
        ET.SubElement(figures, "TaxablePay").text = f"{totals['gross']:.2f}"
        ET.SubElement(figures, "TaxDeducted").text = f"{totals['tax']:.2f}"
        ET.SubElement(figures, "EmployeeNICsInPeriod").text = f"{totals['ni_emp']:.2f}"
        ET.SubElement(figures, "EmployerNICsInPeriod").text = f"{totals['ni_er']:.2f}"
        ET.SubElement(figures, "NetPay").text = f"{totals['net']:.2f}"

        # Pay frequency
        ET.SubElement(employment, "PayFreq").text = "M1"  # Monthly
        ET.SubElement(employment, "PmtDate").text = f"{year}-{int(month):02d}-25"  # Default last working day
        ET.SubElement(employment, "TaxYearEnd").text = str(tax_year_end)

    # Totals
    totals_root = ET.SubElement(fps, "Totals")
    total_gross = sum(t["gross"] for t in employee_totals.values())
    total_tax = sum(t["tax"] for t in employee_totals.values())
    total_ni = sum(t["ni_emp"] + t["ni_er"] for t in employee_totals.values())
    ET.SubElement(totals_root, "TotalTaxablePay").text = f"{total_gross:.2f}"
    ET.SubElement(totals_root, "TotalTaxDeducted").text = f"{total_tax:.2f}"
    ET.SubElement(totals_root, "TotalNICsLiable").text = f"{total_ni:.2f}"

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + _xml_pretty(root).split("\n", 1)[1]
    filename = f"RTI_FPS_{employer_paye.replace('/', '')}_{period_str}.xml"
    return Response(
        content=xml_content.encode("utf-8"),
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== FRANCE: DSN (Déclaration Sociale Nominative) =====================
# Monthly mandatory declaration replacing 30+ older declarations
# Submitted via net-entreprises.fr to URSSAF + various organisms
# https://www.dsn-info.fr/

@router.get("/fr/dsn")
async def generate_fr_dsn(period: str, current_user: dict = Depends(get_current_user)):
    """Generate France DSN (Déclaration Sociale Nominative) XML.

    Format: XML per DSN-Info specification (simplified).
    Period: YYYY-MM.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "FR", "DSN")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    entries, emps, period_info = await _collect_period_data(company_id, period)
    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    siret = (company.get("siret") or company.get("rnc") or company.get("tax_id") or "00000000000000")[:14]
    siren = siret[:9]
    nic = siret[9:14] if len(siret) >= 14 else "00000"
    company_name = (company.get("company_name") or company.get("name") or "ENTREPRISE")[:50]
    naf = company.get("naf_code") or "6201Z"  # Default IT activity
    period_str = period.replace("-", "")[:6]
    year, month = period.split("-")
    period_dsn = f"01{int(month):02d}{year}"  # Format DSN: DDMMYYYY (1st of month)

    root = ET.Element("DSN")
    root.set("xmlns", "http://dsn-info.fr/schema/v1")
    root.set("version", "P24V01")  # DSN phase 3 schema version

    # === DÉCLARATION ===
    declaration = ET.SubElement(root, "Declaration")
    ET.SubElement(declaration, "Nature").text = "01"  # 01=DSN mensuelle normale
    ET.SubElement(declaration, "Type").text = "01"   # 01=Mensuelle
    ET.SubElement(declaration, "Fraction").text = "11"  # 11=DSN du mois
    ET.SubElement(declaration, "MoisPrincipal").text = f"{int(month):02d}/{year}"
    ET.SubElement(declaration, "DateConstitution").text = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    ET.SubElement(declaration, "Devise").text = "EUR"

    # === ÉMETTEUR ===
    emetteur = ET.SubElement(root, "Emetteur")
    ET.SubElement(emetteur, "SIREN").text = siren
    ET.SubElement(emetteur, "NIC").text = nic
    ET.SubElement(emetteur, "RaisonSociale").text = company_name

    # === ENTREPRISE ===
    entreprise = ET.SubElement(root, "Entreprise")
    ET.SubElement(entreprise, "SIREN").text = siren
    ET.SubElement(entreprise, "APE").text = naf
    if company.get("address"):
        adresse = ET.SubElement(entreprise, "Adresse")
        ET.SubElement(adresse, "Voie").text = (company["address"] or "")[:50]
        ET.SubElement(adresse, "CodePostal").text = (company.get("postal_code") or "75001")[:5]
        ET.SubElement(adresse, "Ville").text = (company.get("city") or "PARIS")[:50]
        ET.SubElement(adresse, "Pays").text = "FR"

    # === ÉTABLISSEMENT ===
    etab = ET.SubElement(root, "Etablissement")
    ET.SubElement(etab, "SIRET").text = siret
    ET.SubElement(etab, "APE").text = naf
    ET.SubElement(etab, "EffectifMoyen").text = str(len({e["employee_id"] for e in entries}))

    # === SALARIÉS ===
    employee_totals = {}
    for entry in entries:
        eid = entry["employee_id"]
        if eid not in employee_totals:
            employee_totals[eid] = {"gross": 0.0, "isr": 0.0, "ss_emp": 0.0, "ss_er": 0.0, "net": 0.0}
        employee_totals[eid]["gross"] += entry.get("gross_salary", 0)
        employee_totals[eid]["isr"] += entry.get("isr", 0)
        # FR slots: SS_EMP (~22% combined), SS_ER (~42% combined). Maps to sfs_employee/employer + afp slots
        employee_totals[eid]["ss_emp"] += entry.get("sfs_employee", 0) + entry.get("afp_employee", 0)
        employee_totals[eid]["ss_er"] += (entry.get("sfs_employer", 0) + entry.get("afp_employer", 0) +
                                          entry.get("srl_employer", 0) + entry.get("infotep_employer", 0))
        employee_totals[eid]["net"] += entry.get("net_salary", 0)

    for eid, totals in employee_totals.items():
        emp = emps.get(eid, {})
        salarie = ET.SubElement(root, "Salarie")
        # NIR (numéro de sécurité sociale) - 13 + 2 chars
        nir = (emp.get("nir") or emp.get("document_number") or "1000000000000")[:13]
        ET.SubElement(salarie, "NIR").text = nir
        ET.SubElement(salarie, "Nom").text = (emp.get("last_name") or "").upper()[:40]
        ET.SubElement(salarie, "NomFamille").text = (emp.get("last_name") or "").upper()[:40]
        ET.SubElement(salarie, "Prenoms").text = (emp.get("first_name") or "")[:40]
        ET.SubElement(salarie, "Sexe").text = "01"  # 01=M, 02=F (default M)
        ET.SubElement(salarie, "DateNaissance").text = (emp.get("birth_date") or "01/01/1980")
        ET.SubElement(salarie, "PaysNaissance").text = "FR"
        ET.SubElement(salarie, "MatriculeSalarie").text = (emp.get("employee_id") or "")[:30]

        # Contrat
        contrat = ET.SubElement(salarie, "Contrat")
        ET.SubElement(contrat, "DateDebut").text = (emp.get("hire_date") or "01/01/2024")
        ET.SubElement(contrat, "Statut").text = "04"  # 04=non-cadre par défaut
        ET.SubElement(contrat, "NatureContrat").text = "01"  # 01=CDI
        ET.SubElement(contrat, "DispositifPolitiquePublique").text = "99"
        ET.SubElement(contrat, "MotifRecours").text = "01"

        # Rémunération
        remu = ET.SubElement(salarie, "Remuneration")
        ET.SubElement(remu, "DateDebutPaie").text = f"01/{int(month):02d}/{year}"
        ET.SubElement(remu, "DateFinPaie").text = f"30/{int(month):02d}/{year}"
        ET.SubElement(remu, "MontantBrut").text = f"{totals['gross']:.2f}"
        ET.SubElement(remu, "TypeRemuneration").text = "001"  # Salaire de base

        # Cotisations
        for code, libelle, montant_emp, montant_er in [
            ("100", "Maladie maternité invalidité décès", totals["ss_emp"] * 0.3, totals["ss_er"] * 0.4),
            ("200", "Vieillesse plafonnée + déplafonnée", totals["ss_emp"] * 0.5, totals["ss_er"] * 0.4),
            ("400", "AT/MP", 0.0, totals["ss_er"] * 0.05),
            ("900", "Allocations familiales", 0.0, totals["ss_er"] * 0.15),
        ]:
            cot = ET.SubElement(salarie, "Cotisation")
            ET.SubElement(cot, "Code").text = code
            ET.SubElement(cot, "Libelle").text = libelle
            ET.SubElement(cot, "Assiette").text = f"{totals['gross']:.2f}"
            ET.SubElement(cot, "MontantSalarial").text = f"{montant_emp:.2f}"
            ET.SubElement(cot, "MontantPatronal").text = f"{montant_er:.2f}"

        # Versement individuel
        versement = ET.SubElement(salarie, "VersementIndividuel")
        ET.SubElement(versement, "DateVersement").text = f"30/{int(month):02d}/{year}"
        ET.SubElement(versement, "Montant").text = f"{totals['net']:.2f}"
        ET.SubElement(versement, "PrelevementSource").text = f"{totals['isr']:.2f}"

    # === BORDEREAU DE COTISATION (résumé) ===
    bordereau = ET.SubElement(root, "BordereauCotisation")
    ET.SubElement(bordereau, "Periode").text = f"{int(month):02d}/{year}"
    ET.SubElement(bordereau, "OrganismeProtectionSociale").text = "URSSAF"
    total_assiette = sum(t["gross"] for t in employee_totals.values())
    total_emp = sum(t["ss_emp"] for t in employee_totals.values())
    total_er = sum(t["ss_er"] for t in employee_totals.values())
    ET.SubElement(bordereau, "AssietteTotal").text = f"{total_assiette:.2f}"
    ET.SubElement(bordereau, "MontantSalarialTotal").text = f"{total_emp:.2f}"
    ET.SubElement(bordereau, "MontantPatronalTotal").text = f"{total_er:.2f}"
    ET.SubElement(bordereau, "MontantTotal").text = f"{(total_emp + total_er):.2f}"

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + _xml_pretty(root).split("\n", 1)[1]
    filename = f"DSN_{siret}_{period_str}.xml"
    return Response(
        content=xml_content.encode("utf-8"),
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== FISCAL CALENDAR (DEADLINES) =====================
# Each format has typical deadlines per country. Used for the Global Compliance Calendar.

FORMAT_DEADLINES = {
    # Format: (day_of_filing_month, offset_months_after_period)
    # day=N means: due by Nth day of (period_month + offset)
    # period_offset: 0 = same month, 1 = next month, 3 = next quarter
    "TSS_AUTODET": {"day": 3, "offset_months": 1, "description": "Día 3 del mes siguiente"},
    "TSS_NOVEDADES": {"day": 3, "offset_months": 1, "description": "Día 3 del mes siguiente"},
    "IR3": {"day": 10, "offset_months": 1, "description": "Día 10 del mes siguiente"},
    "IR17": {"day": 15, "offset_months": 3, "description": "15 de marzo del año siguiente"},
    "PILA": {"day": 8, "offset_months": 1, "description": "Días 8-13 según último dígito NIT"},
    "IMSS_SUA": {"day": 17, "offset_months": 1, "description": "Día 17 del mes siguiente"},
    "INFONAVIT": {"day": 17, "offset_months": 2, "description": "Día 17 cada bimestre"},
    "FORM_941": {"day": 30, "offset_months": 1, "description": "Último día del mes siguiente al trimestre"},
    "MODELO_111": {"day": 20, "offset_months": 1, "description": "Día 20 del mes siguiente al trimestre"},
    "TC1": {"day": 30, "offset_months": 1, "description": "Último día del mes siguiente"},
    "RTI_FPS": {"day": 19, "offset_months": 1, "description": "Día 19 del mes siguiente al pago (HMRC)"},
    "DSN": {"day": 15, "offset_months": 1, "description": "Día 15 del mes siguiente (régimen général)"},
    "T4": {"day": 28, "offset_months": 2, "description": "Último día de febrero del año siguiente"},
    "ESOCIAL": {"day": 15, "offset_months": 1, "description": "Día 15 del mes siguiente"},
    "F931": {"day": 13, "offset_months": 1, "description": "Días 7-13 según último dígito CUIT"},
}


@router.get("/calendar")
async def get_fiscal_calendar(current_user: dict = Depends(get_current_user)):
    """Return upcoming fiscal deadlines for all countries with implemented native formats.
    Used by the Global Compliance Calendar dashboard.
    """
    today = datetime.now(timezone.utc).date()
    company_id = current_user.get("company_id")
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    company_country = (company or {}).get("country", "DO")

    upcoming = []
    by_country = {}
    for country_code, formats in NATIVE_FORMATS.items():
        profile = COUNTRY_PROFILES.get(country_code, {})
        for fmt in formats:
            if not fmt.get("implemented"):
                continue
            deadline_cfg = FORMAT_DEADLINES.get(fmt["code"])
            if not deadline_cfg:
                continue
            # Calculate next due date based on most recent applicable period
            offset = deadline_cfg["offset_months"]
            day = deadline_cfg["day"]
            # Period to file: current month minus offset (if today >= offset)
            # Next due: take current month's filing for previous period
            from calendar import monthrange
            # Current period covered: month before today by 'offset' months
            # Filing deadline: this month, day=N
            # Next deadline calculation:
            # If today is before deadline_day of this month -> deadline this month
            # else -> next month
            current_month = today.month
            current_year = today.year
            # Try this month first
            try_day = min(day, monthrange(current_year, current_month)[1])
            try_date = datetime(current_year, current_month, try_day, tzinfo=timezone.utc).date()
            if try_date < today:
                # Move to next month
                if current_month == 12:
                    next_year = current_year + 1
                    next_month = 1
                else:
                    next_year = current_year
                    next_month = current_month + 1
                try_day = min(day, monthrange(next_year, next_month)[1])
                try_date = datetime(next_year, next_month, try_day, tzinfo=timezone.utc).date()
            days_until = (try_date - today).days
            # Period being filed: depends on offset_months
            filing_month = try_date.month - offset
            filing_year = try_date.year
            while filing_month <= 0:
                filing_month += 12
                filing_year -= 1
            period_str = f"{filing_year}-{filing_month:02d}"

            item = {
                "country_code": country_code,
                "country_name": profile.get("name", country_code),
                "flag": profile.get("flag", ""),
                "format_code": fmt["code"],
                "format_name": fmt["name"],
                "agency": fmt["agency"],
                "frequency": fmt["frequency"],
                "due_date": try_date.isoformat(),
                "days_until_due": days_until,
                "period_to_file": period_str,
                "description": deadline_cfg["description"],
                "endpoint": fmt.get("endpoint"),
                "is_company_country": country_code == company_country,
                "urgency": "overdue" if days_until < 0 else ("critical" if days_until <= 3 else ("warning" if days_until <= 7 else "ok")),
            }
            upcoming.append(item)
            by_country.setdefault(country_code, []).append(item)

    upcoming.sort(key=lambda x: x["days_until_due"])

    return {
        "today": today.isoformat(),
        "company_country": company_country,
        "total_upcoming": len(upcoming),
        "next_due": upcoming[0] if upcoming else None,
        "deadlines": upcoming,
        "by_country": by_country,
        "summary": {
            "overdue": sum(1 for x in upcoming if x["urgency"] == "overdue"),
            "critical": sum(1 for x in upcoming if x["urgency"] == "critical"),
            "warning": sum(1 for x in upcoming if x["urgency"] == "warning"),
            "ok": sum(1 for x in upcoming if x["urgency"] == "ok"),
        }
    }


# ===================== CANADA: T4 STATEMENT OF REMUNERATION =====================
# Annual T4 slip per employee - filed with CRA
# https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/payroll/completing-filing-information-returns/t4-information-employers.html

@router.get("/ca/t4")
async def generate_ca_t4(year: int, current_user: dict = Depends(get_current_user)):
    """Generate Canada T4 Statement of Remuneration Paid (annual summary PDF).

    One PDF per employee + summary, all in one document.
    Filed annually with CRA by last day of February.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "CA", "T4 CRA")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    # Aggregate all periods of the year
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": year},
        {"_id": 0}
    ).to_list(50)
    period_ids = [p["period_id"] for p in periods]
    if not period_ids:
        raise HTTPException(status_code=404, detail=f"No hay nóminas para {year}")
    entries = await db.payroll_entries.find(
        {"company_id": company_id, "period_id": {"$in": period_ids}},
        {"_id": 0}
    ).to_list(10000)

    employee_ids = list({e["employee_id"] for e in entries})
    employees_data = await db.employees.find(
        {"company_id": company_id, "employee_id": {"$in": employee_ids}},
        {"_id": 0}
    ).to_list(5000)
    emp_map = {e["employee_id"]: e for e in employees_data}

    # Aggregate per employee
    employee_t4s = {}
    for entry in entries:
        eid = entry["employee_id"]
        if eid not in employee_t4s:
            employee_t4s[eid] = {
                "box_14_employment_income": 0.0,
                "box_16_cpp_contributions": 0.0,
                "box_18_ei_premiums": 0.0,
                "box_22_income_tax": 0.0,
            }
        employee_t4s[eid]["box_14_employment_income"] += entry.get("gross_salary", 0)
        # CA slots: CPP_EMP (~5.95%) → sfs_employee, EI (~1.66%) → afp_employee
        employee_t4s[eid]["box_16_cpp_contributions"] += entry.get("sfs_employee", 0)
        employee_t4s[eid]["box_18_ei_premiums"] += entry.get("afp_employee", 0)
        employee_t4s[eid]["box_22_income_tax"] += entry.get("isr", 0)

    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"T4 {year}"
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=14, alignment=1,
                        textColor=colors.HexColor("#dc2626"), spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Normal"], fontSize=10, alignment=1,
                        textColor=colors.HexColor("#475569"), spaceAfter=8)
    section = ParagraphStyle("sec", parent=styles["Heading3"], fontSize=11,
                             textColor=colors.HexColor("#0f172a"), spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9, spaceAfter=4)
    story = []

    company_name = company.get("company_name") or company.get("name") or "Employer"
    bn = (company.get("rnc") or company.get("business_number") or "123456789RP0001")[:15]

    story.append(Paragraph(f"T4 STATEMENT OF REMUNERATION PAID — {year}", h1))
    story.append(Paragraph(f"Canada Revenue Agency · Agence du revenu du Canada", h2))

    # Summary
    story.append(Paragraph("T4 Summary (T4-Sum)", section))
    summary_totals = {
        "box_14": sum(t["box_14_employment_income"] for t in employee_t4s.values()),
        "box_16": sum(t["box_16_cpp_contributions"] for t in employee_t4s.values()),
        "box_18": sum(t["box_18_ei_premiums"] for t in employee_t4s.values()),
        "box_22": sum(t["box_22_income_tax"] for t in employee_t4s.values()),
    }
    sum_data = [
        ["Field", "Description", "Total"],
        ["BN", "Business Number", bn],
        ["—", "Employer name", company_name],
        ["—", "Number of T4 slips filed", str(len(employee_t4s))],
        ["Total Box 14", "Employment income", f"${summary_totals['box_14']:,.2f}"],
        ["Total Box 16", "Employee's CPP contributions", f"${summary_totals['box_16']:,.2f}"],
        ["Total Box 18", "Employee's EI premiums", f"${summary_totals['box_18']:,.2f}"],
        ["Total Box 22", "Income tax deducted", f"${summary_totals['box_22']:,.2f}"],
    ]
    t = Table(sum_data, colWidths=[40 * mm, 95 * mm, 45 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dc2626")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t)

    # Per-employee T4 slips
    story.append(Spacer(1, 8))
    story.append(Paragraph("Individual T4 Slips", section))
    slip_data = [["#", "SIN", "Employee", "Box 14", "Box 16", "Box 18", "Box 22"]]
    for idx, (eid, totals) in enumerate(employee_t4s.items(), 1):
        emp = emp_map.get(eid, {})
        sin = (emp.get("sin") or emp.get("document_number") or "000000000")[:11]
        name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        slip_data.append([
            str(idx),
            sin,
            name,
            f"${totals['box_14_employment_income']:,.2f}",
            f"${totals['box_16_cpp_contributions']:,.2f}",
            f"${totals['box_18_ei_premiums']:,.2f}",
            f"${totals['box_22_income_tax']:,.2f}",
        ])
    t2 = Table(slip_data, colWidths=[10 * mm, 28 * mm, 50 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm], repeatRows=1)
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dc2626")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<i>Generated by FortexaRH on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
        f"Filing deadline: last day of February {year + 1} (CRA). "
        f"Each employee must receive their T4 slip by the same deadline.</i>",
        body
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    filename = f"T4_{bn.replace('-', '')}_{year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== BRAZIL: eSocial S-1200 =====================
# Monthly remuneration submission to Receita Federal eSocial
# https://www.gov.br/esocial/

@router.get("/br/esocial")
async def generate_br_esocial(period: str, current_user: dict = Depends(get_current_user)):
    """Generate Brazil eSocial event S-1200 (monthly remuneration) XML.

    Format: XML per eSocial S-1200 layout simplified.
    Period: YYYY-MM.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "BR", "eSocial S-1200")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    entries, emps, _ = await _collect_period_data(company_id, period)
    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    cnpj = "".join(c for c in (company.get("rnc") or company.get("tax_id") or "00000000000000") if c.isdigit())[:14]
    period_str = period.replace("-", "")[:6]
    ano_mes = f"{period[:4]}-{period[5:7]}"

    root = ET.Element("eSocial")
    root.set("xmlns", "http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_02_00")
    evt = ET.SubElement(root, "evtRemun")
    evt.set("Id", f"ID1{cnpj}{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{period_str}")

    # ideEvento
    ide_evento = ET.SubElement(evt, "ideEvento")
    ET.SubElement(ide_evento, "indRetif").text = "1"  # 1=Original, 2=Retificação
    ET.SubElement(ide_evento, "indApuracao").text = "1"  # 1=Mensal
    ET.SubElement(ide_evento, "perApur").text = ano_mes
    ET.SubElement(ide_evento, "tpAmb").text = "2"  # 1=Produção, 2=Produção restrita (testes)
    ET.SubElement(ide_evento, "procEmi").text = "1"  # 1=Aplicativo do empregador
    ET.SubElement(ide_evento, "verProc").text = "FortexaRH-1.0"

    # ideEmpregador
    ide_emp = ET.SubElement(evt, "ideEmpregador")
    ET.SubElement(ide_emp, "tpInsc").text = "1"  # 1=CNPJ
    ET.SubElement(ide_emp, "nrInsc").text = cnpj[:8]  # CNPJ raiz (8 dígitos)

    # Per-employee remuneration
    for entry in entries:
        emp = emps.get(entry.get("employee_id"), {})
        cpf = "".join(c for c in (emp.get("cpf") or emp.get("document_number") or "00000000000") if c.isdigit())[:11]
        nis = (emp.get("nis") or emp.get("pis") or "00000000000")[:11]

        ide_trab = ET.SubElement(evt, "ideTrabalhador")
        ET.SubElement(ide_trab, "cpfTrab").text = cpf
        ET.SubElement(ide_trab, "nisTrab").text = nis

        # dmDev (demonstrativo de valores devidos)
        dm_dev = ET.SubElement(ide_trab, "dmDev")
        ET.SubElement(dm_dev, "ideDmDev").text = f"DM{period_str}"
        ET.SubElement(dm_dev, "codCateg").text = "101"  # 101=Empregado geral

        info_perApur = ET.SubElement(dm_dev, "infoPerApur")
        ide_estab = ET.SubElement(info_perApur, "ideEstabLot")
        ET.SubElement(ide_estab, "tpInsc").text = "1"
        ET.SubElement(ide_estab, "nrInsc").text = cnpj
        ET.SubElement(ide_estab, "codLotacao").text = "0001"

        # Rubricas (rúbricas de pago)
        gross = float(entry.get("gross_salary", 0) or 0)
        inss_emp = float(entry.get("sfs_employee", 0) or 0)  # BR INSS = sfs slot
        irrf = float(entry.get("isr", 0) or 0)

        # Salário base
        rem_per = ET.SubElement(ide_estab, "remunPerApur")
        item1 = ET.SubElement(rem_per, "itensRemun")
        ET.SubElement(item1, "codRubr").text = "1000"  # Código rubric salário
        ET.SubElement(item1, "ideTabRubr").text = "FortexaRH"
        ET.SubElement(item1, "qtdRubr").text = "1.00"
        ET.SubElement(item1, "fatorRubr").text = "1"
        ET.SubElement(item1, "vrUnit").text = f"{gross:.2f}"
        ET.SubElement(item1, "vrRubr").text = f"{gross:.2f}"

        # INSS empregado
        if inss_emp > 0:
            item2 = ET.SubElement(rem_per, "itensRemun")
            ET.SubElement(item2, "codRubr").text = "2000"  # INSS
            ET.SubElement(item2, "ideTabRubr").text = "FortexaRH"
            ET.SubElement(item2, "vrRubr").text = f"-{inss_emp:.2f}"  # Negativo (desconto)

        # IRRF
        if irrf > 0:
            item3 = ET.SubElement(rem_per, "itensRemun")
            ET.SubElement(item3, "codRubr").text = "3000"  # IRRF
            ET.SubElement(item3, "ideTabRubr").text = "FortexaRH"
            ET.SubElement(item3, "vrRubr").text = f"-{irrf:.2f}"

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + _xml_pretty(root).split("\n", 1)[1]
    filename = f"eSocial_S1200_{cnpj}_{period_str}.xml"
    return Response(
        content=xml_content.encode("utf-8"),
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== ARGENTINA: F.931 AFIP =====================
# Monthly Declaración Jurada de aportes y contribuciones de la Seguridad Social
# Sistema SiCOSS - filed via AFIP

@router.get("/ar/f931")
async def generate_ar_f931(period: str, current_user: dict = Depends(get_current_user)):
    """Generate Argentina F.931 (SICOSS) monthly Social Security DDJJ flat file.

    Format: TXT plain file per AFIP SICOSS spec, fixed-width records.
    Period: YYYY-MM.
    """
    company_id = current_user.get("company_id")
    await _require_country(company_id, "AR", "F.931 AFIP")

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    entries, emps, _ = await _collect_period_data(company_id, period)
    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    cuit = "".join(c for c in (company.get("rnc") or company.get("tax_id") or "30000000003") if c.isdigit())[:11]
    period_str = period.replace("-", "")[:6]

    lines = []
    for entry in entries:
        emp = emps.get(entry.get("employee_id"), {})
        cuil = "".join(c for c in (emp.get("cuil") or emp.get("document_number") or "20000000000") if c.isdigit())[:11]
        first_name = (emp.get("first_name") or "").upper()[:30]
        last_name = (emp.get("last_name") or "").upper()[:30]
        gross = float(entry.get("gross_salary", 0) or 0)
        # AR slots: APORTE_JUB (~11%), OBRA_SOCIAL (~3%) → emp; CONTRIB_PATRON (~17%), OS_PATRON (~6%) → er
        aporte_jub = float(entry.get("sfs_employee", 0) or 0)
        obra_social_emp = float(entry.get("afp_employee", 0) or 0)
        contrib_patron = float(entry.get("sfs_employer", 0) or 0)
        os_patron = float(entry.get("afp_employer", 0) or 0)
        art = float(entry.get("srl_employer", 0) or 0)
        # SICOSS record format (simplified, ~280 bytes)
        rec = []
        rec.append(_pad_str(cuil, 11))                            # CUIL
        rec.append(_pad_str(last_name + ", " + first_name, 30))   # Apellido y nombre
        rec.append(_pad_str("00", 2))                             # Conyuge
        rec.append(_pad_num(0, 2))                                # Cant. hijos
        rec.append(_pad_str("01", 2))                             # Cód. situación (01=Activo)
        rec.append(_pad_str("08", 2))                             # Cód. condición (08=Servicio común)
        rec.append(_pad_str("100", 3))                            # Cód. actividad
        rec.append(_pad_str("00", 2))                             # Cód. localidad
        rec.append(_pad_str("01", 2))                             # Cód. tabla art (01)
        rec.append(_pad_num(30, 2))                               # Cant. días trabajados
        rec.append(_pad_num(40, 2))                               # Horas trabajadas
        rec.append(_pad_num(gross * 100, 12))                     # Remuneración total (centavos)
        rec.append(_pad_num(gross * 100, 12))                     # Remuneración SIPA (jubilación)
        rec.append(_pad_num(gross * 100, 12))                     # Remuneración INSSJP
        rec.append(_pad_num(gross * 100, 12))                     # Remuneración OS
        rec.append(_pad_num(0, 12))                               # Asig. familiares
        rec.append(_pad_num(0, 12))                               # Adicionales no remunerativos
        rec.append(_pad_num(aporte_jub * 100, 12))                # Aporte SIPA
        rec.append(_pad_num(obra_social_emp * 100, 12))           # Aporte OS
        rec.append(_pad_num(contrib_patron * 100, 12))            # Contrib. SIPA patronal
        rec.append(_pad_num(os_patron * 100, 12))                 # Contrib. OS patronal
        rec.append(_pad_num(art * 100, 12))                       # ART
        rec.append(_pad_num((aporte_jub + obra_social_emp + contrib_patron + os_patron + art) * 100, 14))  # Total
        rec.append(_pad_str(period_str, 6))                       # Período
        rec.append(_pad_str(" ", 50))                             # Reservado
        lines.append("".join(rec))

    content = "\n".join(lines) + "\n"
    filename = f"F931_SICOSS_{cuit}_{period_str}.txt"
    return Response(
        content=content.encode("latin-1", errors="replace"),
        media_type="text/plain; charset=iso-8859-1",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ===================== FILING TRACKING + NOTIFICATIONS =====================
# Track which fiscal filings have been submitted, and send proactive reminders.

from pydantic import BaseModel as _BaseModel


class MarkFiledRequest(_BaseModel):
    country_code: str
    format_code: str
    period: str  # YYYY-MM, YYYY-Tn, YYYY-Qn or year
    filed_at: Optional[str] = None  # ISO date; defaults to today
    receipt_number: Optional[str] = None  # confirmation number from agency
    notes: Optional[str] = None


@router.post("/filings/mark-filed")
async def mark_filing_as_filed(payload: MarkFiledRequest, current_user: dict = Depends(get_current_user)):
    """Mark a fiscal filing as submitted, recording it in the compliance history."""
    company_id = current_user.get("company_id")
    user_email = current_user.get("email")
    filed_at = payload.filed_at or datetime.now(timezone.utc).date().isoformat()

    record = {
        "filing_id": f"filing_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{payload.country_code}_{payload.format_code}",
        "company_id": company_id,
        "country_code": payload.country_code.upper(),
        "format_code": payload.format_code.upper(),
        "period": payload.period,
        "filed_at": filed_at,
        "filed_by": user_email,
        "receipt_number": payload.receipt_number,
        "notes": payload.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Upsert by company+country+format+period
    await db.fiscal_filings.update_one(
        {"company_id": company_id, "country_code": record["country_code"],
         "format_code": record["format_code"], "period": payload.period},
        {"$set": record},
        upsert=True
    )
    return {"success": True, "filing": record}


@router.delete("/filings/mark-filed")
async def unmark_filing(country_code: str, format_code: str, period: str,
                       current_user: dict = Depends(get_current_user)):
    """Remove a filing record (mark as not filed)."""
    company_id = current_user.get("company_id")
    res = await db.fiscal_filings.delete_one({
        "company_id": company_id,
        "country_code": country_code.upper(),
        "format_code": format_code.upper(),
        "period": period,
    })
    return {"success": True, "deleted": res.deleted_count}


@router.get("/filings/history")
async def get_filings_history(
    country_code: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """Get filing history for the company."""
    company_id = current_user.get("company_id")
    query = {"company_id": company_id}
    if country_code:
        query["country_code"] = country_code.upper()
    items = await db.fiscal_filings.find(query, {"_id": 0}).sort("filed_at", -1).limit(limit).to_list(limit)
    return {"total": len(items), "filings": items}


@router.post("/calendar/run-reminders")
async def run_calendar_reminders(current_user: dict = Depends(get_current_user)):
    """Manually trigger fiscal deadline reminders for the current company.
    In production, this should be run as a daily cron job (background task).
    Generates in-app notifications for deadlines at 7, 3, and 1 day before due date.
    Skips formats already marked as filed for the relevant period.
    """
    from routes.notifications_system import create_notification

    company_id = current_user.get("company_id")
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    company_country = (company or {}).get("country", "DO")

    today = datetime.now(timezone.utc).date()
    notifications_sent = 0
    skipped_filed = 0
    from calendar import monthrange

    for country_code, formats in NATIVE_FORMATS.items():
        # Only remind for the company's country (not all 28)
        if country_code != company_country:
            continue
        profile = COUNTRY_PROFILES.get(country_code, {})
        for fmt in formats:
            if not fmt.get("implemented"):
                continue
            deadline_cfg = FORMAT_DEADLINES.get(fmt["code"])
            if not deadline_cfg:
                continue
            day = deadline_cfg["day"]
            offset = deadline_cfg["offset_months"]
            current_month = today.month
            current_year = today.year
            try_day = min(day, monthrange(current_year, current_month)[1])
            try_date = datetime(current_year, current_month, try_day, tzinfo=timezone.utc).date()
            if try_date < today:
                if current_month == 12:
                    next_year = current_year + 1
                    next_month = 1
                else:
                    next_year = current_year
                    next_month = current_month + 1
                try_day = min(day, monthrange(next_year, next_month)[1])
                try_date = datetime(next_year, next_month, try_day, tzinfo=timezone.utc).date()
            days_until = (try_date - today).days
            # Calculate the period being filed
            filing_month = try_date.month - offset
            filing_year = try_date.year
            while filing_month <= 0:
                filing_month += 12
                filing_year -= 1
            period_str = f"{filing_year}-{filing_month:02d}"

            # Check if already filed for this period
            already_filed = await db.fiscal_filings.find_one({
                "company_id": company_id,
                "country_code": country_code,
                "format_code": fmt["code"],
                "period": period_str,
            })
            if already_filed:
                skipped_filed += 1
                continue

            # Trigger only for 7, 3, 1 day windows
            if days_until not in (7, 3, 1, 0, -1):
                continue

            urgency = "critical" if days_until <= 1 else ("warning" if days_until <= 3 else "normal")
            title = f"{profile.get('flag', '')} {fmt['name']} — vence en {days_until} día{'s' if days_until != 1 else ''}"
            if days_until <= 0:
                title = f"⚠️ {profile.get('flag', '')} {fmt['name']} — VENCIDO"
            message = (f"Tu empresa debe presentar {fmt['name']} ante {fmt['agency']} "
                      f"el {try_date.isoformat()}. Período a declarar: {period_str}.")

            await create_notification(
                company_id=company_id,
                title=title,
                message=message,
                notification_type="fiscal_deadline",
                priority=urgency if urgency in ("critical", "warning") else "normal",
                link="/global-compliance",
                target_role="admin",
                metadata={
                    "country_code": country_code,
                    "format_code": fmt["code"],
                    "period": period_str,
                    "due_date": try_date.isoformat(),
                    "days_until_due": days_until,
                    "endpoint": fmt.get("endpoint"),
                }
            )
            notifications_sent += 1

    return {
        "success": True,
        "company_country": company_country,
        "notifications_sent": notifications_sent,
        "skipped_already_filed": skipped_filed,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
