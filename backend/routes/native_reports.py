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
    "US": [{"code": "FORM_941", "name": "IRS Form 941", "agency": "IRS", "frequency": "quarterly", "implemented": False}],
    "ES": [
        {"code": "MODELO_111", "name": "Modelo 111 (Retenciones IRPF)", "agency": "AEAT", "frequency": "quarterly", "implemented": False},
        {"code": "TC1", "name": "TC1 (Cotización SS)", "agency": "TGSS", "frequency": "monthly", "implemented": False},
    ],
    "GB": [{"code": "RTI_FPS", "name": "HMRC RTI FPS", "agency": "HMRC", "frequency": "monthly", "implemented": False}],
    "FR": [{"code": "DSN", "name": "DSN (Déclaration Sociale Nominative)", "agency": "URSSAF", "frequency": "monthly", "implemented": False}],
    "CA": [{"code": "T4", "name": "T4 Statement of Remuneration", "agency": "CRA", "frequency": "annual", "implemented": False}],
    "BR": [{"code": "ESOCIAL", "name": "eSocial", "agency": "Receita Federal", "frequency": "monthly", "implemented": False}],
    "AR": [{"code": "F931", "name": "F.931 AFIP", "agency": "AFIP", "frequency": "monthly", "implemented": False}],
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
