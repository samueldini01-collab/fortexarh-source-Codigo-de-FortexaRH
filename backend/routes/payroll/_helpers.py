"""Shared payroll helpers — pure utilities, no route registration here."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from config import db
from routes.country_config import get_company_rates_flat, calculate_isr_dynamic
from services.journal_entry_service import generate_payroll_journal_entry
from utils.payroll_constants import calculate_isr_monthly, now_iso


# ISR Quincenal Policies
ISR_POLICY_SPLIT_HALF = "split_half"  # Mitad en cada quincena (default)
ISR_POLICY_ALL_Q1 = "all_q1"          # Todo el ISR en la 1ra quincena
ISR_POLICY_ALL_Q2 = "all_q2"          # Todo el ISR en la 2da quincena
VALID_ISR_POLICIES = {ISR_POLICY_SPLIT_HALF, ISR_POLICY_ALL_Q1, ISR_POLICY_ALL_Q2}


async def get_isr_quincenal_policy(company_id: str) -> str:
    """Read the company's ISR quincenal policy from payroll_settings.

    Default: ``split_half`` (each quincena withholds 50% of the monthly ISR).
    """
    settings = await db.payroll_settings.find_one(
        {"company_id": company_id}, {"_id": 0, "isr_quincenal_policy": 1}
    )
    policy = (settings or {}).get("isr_quincenal_policy") or ISR_POLICY_SPLIT_HALF
    return policy if policy in VALID_ISR_POLICIES else ISR_POLICY_SPLIT_HALF


async def _monthly_gross_for_isr(
    company_id: str,
    period: dict | None,
    employee_id: str | None,
    current_entry_gross: float,
) -> float:
    """For a quincenal period, return the TRUE monthly gross accumulation
    (current quincena gross + sister quincena gross of the same month).

    Falls back to ``current_entry_gross × 2`` if the sister period or its
    entry doesn't exist yet (typical when seeding the first quincena of a
    new month).
    """
    if not period or not (period.get("period_type") or "").startswith("quincenal"):
        return current_entry_gross

    current_type = period.get("period_type")
    sister_type = "quincenal_2" if current_type == "quincenal_1" else "quincenal_1"

    sister_period = await db.payroll_periods.find_one(
        {
            "company_id": company_id,
            "year": period.get("year"),
            "month": period.get("month"),
            "period_type": sister_type,
        },
        {"_id": 0, "period_id": 1},
    )
    if not sister_period or not employee_id:
        return current_entry_gross * 2

    sister_entry = await db.payroll_entries.find_one(
        {
            "period_id": sister_period["period_id"],
            "company_id": company_id,
            "employee_id": employee_id,
        },
        {"_id": 0, "gross_salary": 1},
    )
    if not sister_entry:
        return current_entry_gross * 2

    sister_gross = float(sister_entry.get("gross_salary") or 0)
    return current_entry_gross + sister_gross


def _apply_isr_quincenal_policy(
    monthly_isr: float, period_type: str | None, policy: str
) -> float:
    """Return the ISR amount to withhold THIS quincena given the company's
    ISR quincenal policy.
    """
    is_q1 = period_type == "quincenal_1"
    is_q2 = period_type == "quincenal_2"

    if policy == ISR_POLICY_ALL_Q1:
        return round(monthly_isr, 2) if is_q1 else 0.0
    if policy == ISR_POLICY_ALL_Q2:
        return round(monthly_isr, 2) if is_q2 else 0.0
    # Default: split_half
    return round(monthly_isr / 2, 2)


async def _compute_isr(
    company_id: str,
    gross_salary: float,
    rates: dict,
    period_type: str | None = None,
    period: dict | None = None,
    employee_id: str | None = None,
) -> dict:
    """
    Compute ISR for a given company+gross — DGII-compliant.

    DGII rule: the ISR bracket table is **monthly**. For quincenal payrolls
    we must use the ACCUMULATED MONTHLY GROSS (Q1 + Q2) — not
    ``current_quincena × 2`` — because commissions / extras that happen in
    a single quincena would otherwise inflate the taxable base.

    For quincenal periods this function:
      1. Builds the true monthly gross by summing the current entry's gross
         with the sister quincena's entry gross (same year/month).
      2. Computes the monthly ISR off that accumulated base.
      3. Distributes the monthly ISR across the quincenas according to the
         company's ``isr_quincenal_policy`` (split_half / all_q1 / all_q2).

    Args:
        company_id: tenant identifier (used for the policy + sister lookup).
        gross_salary: gross of the CURRENT entry (already includes commissions).
        rates: flat rates dict (must contain ``country_code``).
        period_type: legacy positional arg, kept for compat. If ``period`` is
            passed it takes precedence.
        period: full period dict (preferred — has year/month for sister lookup).
        employee_id: employee whose sister entry we need.

    Returns a dict with ``isr_monthly`` (= amount to withhold THIS period),
    plus ``monthly_isr_total``, ``monthly_gross_used``, ``policy`` for
    transparency / audit.
    """
    effective_period_type = (period.get("period_type") if period else None) or period_type
    is_quincenal = (effective_period_type or "").startswith("quincenal")

    if is_quincenal:
        monthly_gross = await _monthly_gross_for_isr(
            company_id, period, employee_id, gross_salary
        )
    else:
        monthly_gross = gross_salary

    if rates.get("country_code") == "DO":
        monthly_result = calculate_isr_monthly(monthly_gross)
    else:
        monthly_result = calculate_isr_dynamic(monthly_gross, rates.get("income_tax") or {})

    if is_quincenal:
        policy = await get_isr_quincenal_policy(company_id)
        result = dict(monthly_result)
        full_monthly_isr = monthly_result.get("isr_monthly", 0) or 0
        result["monthly_isr_total"] = round(full_monthly_isr, 2)
        result["monthly_gross_used"] = round(monthly_gross, 2)
        result["isr_quincenal_policy"] = policy
        result["isr_monthly"] = _apply_isr_quincenal_policy(
            full_monthly_isr, effective_period_type, policy
        )
        result["period_type"] = effective_period_type
        return result

    # Monthly payroll: ISR_monthly == monthly_isr_total
    monthly_result = dict(monthly_result)
    monthly_result["monthly_isr_total"] = monthly_result.get("isr_monthly", 0)
    monthly_result["monthly_gross_used"] = round(monthly_gross, 2)
    return monthly_result


async def recompute_sister_quincena_isr(
    company_id: str, period: dict, employee_id: str
) -> None:
    """When the gross of one quincena changes, the monthly accumulation
    used for ISR also changes. This helper recomputes the sister quincena
    entry's ISR (if a sister exists for the same employee/month) so both
    halves stay consistent.

    No-op when:
      - The current period isn't quincenal.
      - No sister period or no sister entry exists.
      - The sister entry has an inline ISR override
        (``isr_manual_override_entry``) or the employee has a profile-level
        override (``isr_manual_override``) — those take precedence.
    """
    if not period or not (period.get("period_type") or "").startswith("quincenal"):
        return
    sister_type = "quincenal_2" if period["period_type"] == "quincenal_1" else "quincenal_1"
    sister_period = await db.payroll_periods.find_one(
        {
            "company_id": company_id,
            "year": period.get("year"),
            "month": period.get("month"),
            "period_type": sister_type,
        },
        {"_id": 0},
    )
    if not sister_period:
        return
    if sister_period.get("status") in {"paid", "approved"}:
        # Don't mutate already-finalized periods.
        return

    sister_entry = await db.payroll_entries.find_one(
        {
            "period_id": sister_period["period_id"],
            "company_id": company_id,
            "employee_id": employee_id,
        },
        {"_id": 0},
    )
    if not sister_entry:
        return
    if sister_entry.get("isr_manual_override_entry"):
        return

    emp = await db.employees.find_one(
        {"employee_id": employee_id, "company_id": company_id},
        {"_id": 0, "isr_discount": 1, "isr_manual_override": 1, "isr_manual_amount": 1},
    ) or {}
    if not emp.get("isr_discount", True) or emp.get("isr_manual_override"):
        return

    rates = await get_company_rates_flat(company_id)
    isr_result = await _compute_isr(
        company_id,
        sister_entry.get("gross_salary", 0) or 0,
        rates,
        period_type=sister_period.get("period_type"),
        period=sister_period,
        employee_id=employee_id,
    )
    new_isr = isr_result["isr_monthly"]

    # Recompute totals on the sister entry
    sfs_e = sister_entry.get("sfs_employee", 0) or 0
    afp_e = sister_entry.get("afp_employee", 0) or 0
    total_additional = sister_entry.get("total_additional_deductions", 0) or 0
    total_ded_novelties = sister_entry.get("total_deduction_novelties", 0) or 0
    loan_ded = sister_entry.get("loan_deduction", 0) or 0
    total_deductions = round(
        sfs_e + afp_e + new_isr + total_additional + total_ded_novelties + loan_ded, 2
    )
    net_salary = round((sister_entry.get("gross_salary", 0) or 0) - total_deductions, 2)

    await db.payroll_entries.update_one(
        {
            "period_id": sister_period["period_id"],
            "company_id": company_id,
            "employee_id": employee_id,
        },
        {
            "$set": {
                "isr": new_isr,
                "total_deductions": total_deductions,
                "net_salary": net_salary,
                "updated_at": now_iso(),
            }
        },
    )
    # Refresh sister period totals
    await update_period_totals(sister_period["period_id"], company_id)


def period_scaling_factor(period_type: str | None) -> float:
    """Return the factor to convert a monthly amount into the period amount.

    Manual override amounts (SFS / AFP / ISR / additional deductions) are
    stored on the employee profile as MONTHLY amounts. When applied to a
    quincenal period they must be halved so the withholding for the
    period is correct (and the monthly total ends up matching what HR
    entered).

    - ``"mensual"`` → 1.0
    - ``"quincenal_*"`` → 0.5
    - anything else (incl. ``None``) → 1.0 (backwards-compat)
    """
    return 0.5 if (period_type or "").startswith("quincenal") else 1.0


async def update_period_totals(period_id: str, company_id: str):
    """Update period totals based on entries"""
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    total_gross = sum(e.get("gross_salary", 0) for e in entries)
    total_deductions = sum(e.get("total_deductions", 0) for e in entries)
    total_net = sum(e.get("net_salary", 0) for e in entries)
    
    await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {
            "total_gross": round(total_gross, 2),
            "total_deductions": round(total_deductions, 2),
            "total_net": round(total_net, 2),
            "employee_count": len(entries),
            "updated_at": now_iso()
        }}
    )

    # Auto-update linked journal entry if exists
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0, "journal_entry_id": 1, "status": 1}
    )
    if period and period.get("journal_entry_id") and period.get("status") in ["approved", "paid"]:
        await generate_payroll_journal_entry(period_id, company_id, "system", trigger="update")



def format_currency_pdf(value):
    """Format a value as RD$X,XXX.XX for payslip PDFs (DR locale)."""
    try:
        return f"RD${float(value or 0):,.2f}"
    except (ValueError, TypeError):
        return "RD$0.00"
