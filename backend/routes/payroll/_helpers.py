"""Shared payroll helpers — pure utilities, no route registration here."""
from __future__ import annotations

from datetime import datetime, timezone

from config import db
from routes.country_config import get_company_rates_flat, calculate_isr_dynamic
from services.journal_entry_service import generate_payroll_journal_entry
from utils.payroll_constants import calculate_isr_monthly, now_iso


async def _compute_isr(company_id: str, gross_salary: float, rates: dict) -> dict:
    """
    Compute ISR for a given company+gross.
    - DR keeps using its legacy DGII interpolation table (more precise).
    - Other countries use bracket-based calculation from country profile.
    """
    if rates.get("country_code") == "DO":
        return calculate_isr_monthly(gross_salary)
    return calculate_isr_dynamic(gross_salary, rates.get("income_tax") or {})


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
