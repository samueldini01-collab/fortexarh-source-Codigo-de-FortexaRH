"""Payroll models"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PayrollEntryCreate(BaseModel):
    """Entrada de nómina individual por empleado"""
    period_id: str
    employee_id: str
    base_salary: float
    overtime_day_hours: float = 0
    overtime_day_rate: float = 35
    overtime_night_hours: float = 0
    overtime_night_rate: float = 15
    overtime_weekend_hours: float = 0
    overtime_weekend_rate: float = 100
    overtime_holiday_hours: float = 0
    overtime_holiday_rate: float = 100
    bonuses: float = 0
    commissions: float = 0
    other_income: float = 0
    additional_deductions: Optional[List[Dict[str, Any]]] = []
    isr_override: Optional[float] = None
    sfs_override: Optional[float] = None
    afp_override: Optional[float] = None
    overtime_override: Optional[float] = None


class ApprovalRequest(BaseModel):
    """Solicitud de aprobación de nómina"""
    comments: Optional[str] = None


class PaymentRequest(BaseModel):
    payment_bank: str = ""
    payment_date: str = ""
    reference: str = ""


class PayrollCreate(BaseModel):
    """Legacy basic payroll creation"""
    employee_id: str
    period_start: str
    period_end: str
    base_salary: float
    bonuses: float = 0
    deductions: float = 0


class PayrollSettingsModel(BaseModel):
    overtime_day: float = 35
    overtime_night: float = 15
    overtime_weekend: float = 100
    overtime_holiday: float = 100
    afp_employee: float = 2.87
    sfs_employee: float = 3.04
    afp_employer: float = 7.10
    sfs_employer: float = 7.09
    srl_employer: float = 1
    infotep_employer: float = 1
    isr_min_salary: float = 416220.01
    isr_mid_salary: float = 624329.04
    isr_max_salary: float = 867123.01
    isr_min_rate: float = 15
    isr_mid_rate: float = 20
    isr_max_rate: float = 25
    isr_mid_fixed: float = 31216.00
    isr_max_fixed: float = 79776.00
    # ISR Quincenal Distribution Policy:
    #   "split_half" (default) — Mitad del ISR mensual en cada quincena.
    #   "all_q1"               — Todo el ISR mensual se cobra en la 1ra quincena.
    #   "all_q2"               — Todo el ISR mensual se cobra en la 2da quincena.
    isr_quincenal_policy: str = "split_half"


class PayrollConfigCreate(BaseModel):
    name: str
    config_type: str
    calculation_type: str
    value: float
    is_taxable: bool = True
    is_active: bool = True
    description: Optional[str] = None


class PayrollCalculatorInput(BaseModel):
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    base_salary: float
    days_worked: int = 30
    hours_extra: float = 0
    hour_rate: float = 0
    bonuses: float = 0
    commissions: float = 0
    loan_deduction: float = 0
    other_deductions: float = 0


class PayrollCalculatorResult(BaseModel):
    employee_name: Optional[str] = None
    base_salary: float
    days_worked: int
    hours_extra: float
    hour_rate: float
    bonuses: float
    commissions: float
    proportional_salary: float
    extra_hours_pay: float
    total_earnings: float
    sfs_employee: float
    afp_employee: float
    total_tss_employee: float
    isr_taxable_base: float
    isr_annual_taxable: float
    isr_annual: float
    isr_monthly: float
    isr_bracket: str
    total_employee_deductions: float
    loan_deduction: float
    other_deductions: float
    net_salary: float
    sfs_employer: float
    afp_employer: float
    srl_employer: float
    infotep_employer: float
    total_tss_employer: float
    total_cost_employer: float
    total_other_deductions: float = 0
    total_deductions: float = 0
    total_employer_contributions: float = 0
    breakdown: Optional[Dict[str, Any]] = None
