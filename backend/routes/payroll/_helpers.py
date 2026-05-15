"""Shared payroll helpers — pure utilities, no route registration here."""
from __future__ import annotations

from datetime import datetime, timezone

from config import db
from routes.country_config import get_company_rates_flat, calculate_isr_dynamic
from services.journal_entry_service import generate_payroll_journal_entry
from utils.payroll_constants import calculate_isr_monthly, now_iso


async def _compute_isr(
    company_id: str,
    gross_salary: float,
    rates: dict,
    period_type: str | None = None,
) -> dict:
    """
    Compute ISR for a given company+gross.

    DGII standard practice (and most LATAM equivalents): the ISR bracket
    table is **monthly**. For quincenal (biweekly) periods, the bracket
    threshold is applied to the MONTHLY-equivalent gross (``gross × 2``)
    and the resulting ISR is then split across the 2 quincenas of the
    month — so each quincena withholds half of the monthly ISR.

    Args:
        period_type: "mensual" (default), "quincenal_1", "quincenal_2",
                     or any other engine-specific code. Anything that
                     ``startswith("quincenal")`` triggers the doubling.

    Returns the standard ``{"isr_monthly": <amount-to-withhold-this-period>, ...}``
    dict. The ``isr_monthly`` key is kept for backwards-compat even though
    for quincenal periods it represents the **quincenal** withholding.

    - DR keeps using its legacy DGII interpolation table (more precise).
    - Other countries use bracket-based calculation from country profile.
    """
    is_quincenal = (period_type or "").startswith("quincenal")
    monthly_gross = gross_salary * 2 if is_quincenal else gross_salary

    if rates.get("country_code") == "DO":
        monthly_result = calculate_isr_monthly(monthly_gross)
    else:
        monthly_result = calculate_isr_dynamic(monthly_gross, rates.get("income_tax") or {})

    if is_quincenal:
        result = dict(monthly_result)
        # Split monthly ISR across 2 quincenas — what's withheld this period
        result["monthly_isr_total"] = monthly_result.get("isr_monthly", 0)
        result["isr_monthly"] = round(monthly_result.get("isr_monthly", 0) / 2, 2)
        result["period_type"] = period_type
        return result
    return monthly_result


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
