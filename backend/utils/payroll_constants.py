# Constants and shared utilities for payroll calculations
# These are used across multiple modules

from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

# ===================== TSS CONSTANTS (Dominican Republic) =====================

# Employee contributions
SFS_EMPLOYEE_RATE = 0.0304  # Seguro Familiar de Salud 3.04%
AFP_EMPLOYEE_RATE = 0.0287  # Administradora de Fondo de Pensiones 2.87%
TSS_EMPLOYEE_TOTAL = SFS_EMPLOYEE_RATE + AFP_EMPLOYEE_RATE  # 5.91%

# Employer contributions
SFS_EMPLOYER_RATE = 0.0709  # Seguro Familiar de Salud 7.09%
AFP_EMPLOYER_RATE = 0.0710  # Fondo de Pensiones 7.10%
SRL_EMPLOYER_RATE = 0.01    # Seguro de Riesgos Laborales 1%
INFOTEP_EMPLOYER_RATE = 0.01 # INFOTEP 1%

# ISR Monthly exempt threshold
ISR_MONTHLY_EXEMPT = 34685.00

# Reference table values from DGII 2023
ISR_TABLE_REFERENCE = {
    34685: 0.00,
    34700: 2.25,
    35000: 47.25,
    40000: 797.25,
    45000: 1547.25,
    50000: 2297.25,
    55000: 3055.85,
    60000: 3795.85,
    65000: 4555.85,
    70000: 5215.85,
    75000: 5857.94,
    80000: 6535.85,
}

# ===================== PAYROLL TYPES =====================

PAYROLL_TYPES = [
    {"code": "REG", "name": "Regular", "description": "Nómina regular quincenal/mensual"},
    {"code": "TEMP", "name": "Temporal", "description": "Nómina para empleados temporales"},
    {"code": "BONO", "name": "Bono/Extraordinaria", "description": "Nómina de bonificaciones extraordinarias"},
    {"code": "REG13", "name": "Regalía Pascual", "description": "Nómina de salario 13"},
    {"code": "VAC", "name": "Vacaciones", "description": "Nómina de pago de vacaciones"},
    {"code": "LIQ", "name": "Liquidación", "description": "Nómina de liquidación de empleados"},
    {"code": "OBREROS_NG", "name": "Obreros NG 07/2007", "description": "Nómina sector construcción - Solo ISR 2% mano de obra (Norma General 07-2007)"},
]

# ISR rate for construction workers (Obreros NG 07/2027)
ISR_OBREROS_RATE = 0.02  # 2% retention on labor income

# ===================== NOVELTY TYPES =====================

PAYROLL_NOVELTY_TYPES = {
    "income": [
        {"code": "COM", "name": "Comisiones", "description": "Comisiones de ventas"},
        {"code": "VIA", "name": "Viáticos", "description": "Gastos de transporte y alimentación"},
        {"code": "INC", "name": "Incentivos", "description": "Bonificaciones por rendimiento"},
        {"code": "HED", "name": "Horas Extras Diurnas", "description": "Horas extras 35%"},
        {"code": "HEN", "name": "Horas Extras Nocturnas", "description": "Horas extras 15%"},
        {"code": "HEFS", "name": "Horas Extras Fin de Semana", "description": "Horas extras 100%"},
        {"code": "HEFER", "name": "Horas Extras Feriados", "description": "Horas extras 100%"},
        {"code": "BON", "name": "Bonificación", "description": "Bonificación general"},
        {"code": "REG", "name": "Regalía Pascual", "description": "Salario 13"},
        {"code": "VAC", "name": "Vacaciones", "description": "Pago de vacaciones"},
        {"code": "OTROING", "name": "Otros Ingresos", "description": "Otros ingresos no especificados"},
    ],
    "deduction": [
        {"code": "PREST", "name": "Préstamo Empresa", "description": "Cuota de préstamo de la empresa"},
        {"code": "ANTIC", "name": "Anticipo", "description": "Anticipo de salario"},
        {"code": "COOP", "name": "Cooperativa", "description": "Descuento de cooperativa"},
        {"code": "SEG", "name": "Seguro Adicional", "description": "Seguro de vida o médico adicional"},
        {"code": "PENS", "name": "Pensión Alimenticia", "description": "Retención por pensión alimenticia"},
        {"code": "EMB", "name": "Embargo", "description": "Embargo judicial"},
        {"code": "TARD", "name": "Tardanzas", "description": "Descuento por tardanzas"},
        {"code": "AUS", "name": "Ausencias", "description": "Descuento por ausencias"},
        {"code": "OTROSD", "name": "Otros Descuentos", "description": "Otros descuentos no especificados"},
    ]
}

# ===================== PYDANTIC MODELS =====================

class PayrollPeriodCreateV2(BaseModel):
    """Período de nómina con opciones avanzadas"""
    period_type: str  # "quincenal_1", "quincenal_2", "mensual"
    payroll_type: str = "REG"
    year: int
    month: int
    start_date: str
    end_date: str
    description: Optional[str] = None
    department_filter: Optional[str] = None
    employee_ids: Optional[List[str]] = None
    currency: str = "DOP"
    exchange_rate: Optional[float] = None
    project_id: Optional[str] = None
    template_id: Optional[str] = None

class PayrollNoveltyCreate(BaseModel):
    """Novedad individual para agregar a la nómina"""
    entry_id: str
    novelty_type: str  # "income" o "deduction"
    code: str
    name: str
    description: Optional[str] = ""
    amount: float
    is_percentage: bool = False

class PayrollPaymentRequest(BaseModel):
    """Solicitud de pago de nómina"""
    bank_account_code: Optional[str] = "1101"

# ===================== UTILITY FUNCTIONS =====================

def calculate_isr_monthly(gross_monthly: float) -> dict:
    """
    Calculate Dominican Republic ISR (Income Tax) monthly withholding.

    Implements the official DGII formula (Ley 11-92 modificada por Ley 253-12,
    Art. 296) using the **annualized progressive bracket** approach:

        1. Compute statutory TSS (SFS 3.04% + AFP 2.87%) from gross monthly.
        2. Taxable monthly = gross - SFS - AFP.
        3. Annualize: taxable × 12.
        4. Apply the annual bracket table:
             - 0       — 416,220       → Exento (0%)
             - 416,220 — 624,329       → 15% del excedente de 416,220
             - 624,329 — 867,123       → 31,216 + 20% del excedente de 624,329
             - 867,123 — ∞             → 79,776 + 25% del excedente de 867,123
        5. Monthly ISR = annual / 12.

    This matches the on-screen "Auto" ISR shown in the Employee profile
    (`EmployeeFormDialog.calculateISRMonthly`) and the values produced by
    every DGII retention table for salaried workers.

    Reference threshold: gross monthly of RD$34,685.00 is the practical
    exemption point (annualized = 416,220, the bracket-1 ceiling).
    """
    g = float(gross_monthly or 0)
    if g <= 0:
        return {
            "taxable_base_monthly": 0.0,
            "annual_taxable": 0.0,
            "isr_annual": 0.0,
            "isr_monthly": 0.0,
            "tax_bracket": "Exento (0%)",
        }

    sfs = g * SFS_EMPLOYEE_RATE
    afp = g * AFP_EMPLOYEE_RATE
    taxable_monthly = g - sfs - afp
    annual_taxable = taxable_monthly * 12

    if annual_taxable <= 416220:
        isr_annual = 0.0
        bracket = "Exento (0%)"
    elif annual_taxable <= 624329:
        isr_annual = (annual_taxable - 416220) * 0.15
        bracket = "15%"
    elif annual_taxable <= 867123:
        isr_annual = 31216 + (annual_taxable - 624329) * 0.20
        bracket = "20%"
    else:
        isr_annual = 79776 + (annual_taxable - 867123) * 0.25
        bracket = "25%"

    isr_monthly = round(max(0.0, isr_annual / 12), 2)
    return {
        "taxable_base_monthly": round(taxable_monthly, 2),
        "annual_taxable": round(annual_taxable, 2),
        "isr_annual": round(isr_annual, 2),
        "isr_monthly": isr_monthly,
        "tax_bracket": bracket,
    }

def generate_id(prefix: str = "id") -> str:
    """Generate a unique ID with prefix"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def now_iso() -> str:
    """Return current UTC time in ISO format"""
    return datetime.now(timezone.utc).isoformat()
