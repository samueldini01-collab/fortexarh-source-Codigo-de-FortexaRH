"""Public payroll calculator — country-agnostic salary breakdown.

Marketing tool: lets contadores and candidates simulate their net salary from
the FortexaRH landing page WITHOUT registering. Reuses the same proven math
that powers the production payroll engine (58 DR pure-function tests +
13 HTTP integration tests cover the underlying calculations).

Public endpoint (no auth required):
    GET /api/payroll/calculator?country=DO&gross=50000

Response:
    {
      "country_code": "DO",
      "country_name": "República Dominicana",
      "currency": "DOP",
      "currency_symbol": "RD$",
      "gross_monthly": 50000,
      "employee_deductions": [
        {"code": "SFS", "label": "...", "rate": 0.0304, "amount": 1520.00},
        ...
      ],
      "employer_contributions": [...],
      "isr": {"amount": 2297.25, "bracket": "15%", "annual": 27567.0},
      "totals": {
        "total_employee_deductions": 5252.25,
        "total_employer_contributions": 8095.0,
        "net_monthly": 44747.75,
        "fiscal_cost_to_employer": 58095.0
      },
      "calculator_version": "iter244",
      "disclaimer": "Reference calculation. Validate with a certified accountant."
    }
"""
from __future__ import annotations

from fastapi import HTTPException, Query

from routes.country_config import COUNTRY_PROFILES, calculate_isr_dynamic
from utils.payroll_constants import calculate_isr_monthly

from . import router


CALCULATOR_VERSION = "iter244"
CALCULATOR_DISCLAIMER = (
    "Cálculo de referencia basado en tasas oficiales publicadas. "
    "Valide con un contador certificado antes de tomar decisiones financieras."
)


def _isr_for_country(country_code: str, gross_monthly: float) -> dict:
    """Pick the right ISR engine: DR uses the precise DGII table, the rest use
    the dynamic bracket calculator from COUNTRY_PROFILES."""
    if country_code == "DO":
        return calculate_isr_monthly(gross_monthly)
    profile = COUNTRY_PROFILES.get(country_code, {})
    return calculate_isr_dynamic(gross_monthly, profile.get("income_tax") or {})


@router.get("/calculator", include_in_schema=True)
async def public_payroll_calculator(
    country: str = Query("DO", min_length=2, max_length=3, description="ISO 3166-1 alpha-2 country code"),
    gross: float = Query(..., gt=0, description="Monthly gross salary in the country's currency"),
):
    """Public payroll calculator — no authentication required.

    Returns a country-aware breakdown of employee deductions, employer
    contributions, ISR, net salary, and total fiscal cost to the employer.
    """
    country_code = country.upper().strip()
    if country_code not in COUNTRY_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"País '{country_code}' no soportado. Países disponibles: "
                f"{', '.join(sorted(COUNTRY_PROFILES.keys()))}"
            ),
        )

    profile = COUNTRY_PROFILES[country_code]
    ss = profile.get("social_security") or {}
    employee_deductions_cfg = ss.get("employee_deductions", []) or []
    employer_contributions_cfg = ss.get("employer_contributions", []) or []

    # ===== EMPLOYEE DEDUCTIONS =====
    employee_breakdown = []
    total_employee_deductions = 0.0
    for ded in employee_deductions_cfg:
        rate = float(ded.get("rate", 0) or 0)
        # Some countries cap the contribution base at a salary ceiling.
        cap = ded.get("cap")
        base = min(gross, float(cap)) if cap else gross
        amount = round(base * rate, 2)
        employee_breakdown.append({
            "code": ded.get("code", "SS"),
            "label": ded.get("label") or ded.get("name") or ded.get("code", "SS"),
            "rate": rate,
            "base": round(base, 2),
            "amount": amount,
        })
        total_employee_deductions += amount

    # ===== EMPLOYER CONTRIBUTIONS =====
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
            "base": round(base, 2),
            "amount": amount,
        })
        total_employer_contributions += amount

    # ===== ISR =====
    isr_result = _isr_for_country(country_code, gross)
    isr_amount = float(isr_result.get("isr_monthly", 0) or 0)

    # ===== TOTALS =====
    total_employee_deductions += isr_amount
    net_monthly = round(gross - total_employee_deductions, 2)
    fiscal_cost = round(gross + total_employer_contributions, 2)

    return {
        "country_code": country_code,
        "country_name": profile.get("name", country_code),
        "country_flag": profile.get("flag", ""),
        "currency": profile.get("currency", ""),
        "currency_symbol": profile.get("currency_symbol", ""),
        "region": profile.get("region", ""),
        "gross_monthly": round(gross, 2),
        "gross_annual": round(gross * 12, 2),
        "employee_deductions": employee_breakdown,
        "employer_contributions": employer_breakdown,
        "isr": {
            "amount": round(isr_amount, 2),
            "annual": round(isr_amount * 12, 2),
            "bracket": isr_result.get("tax_bracket", ""),
            "agency": (profile.get("income_tax") or {}).get("agency", ""),
        },
        "totals": {
            "total_employee_deductions": round(total_employee_deductions, 2),
            "total_employer_contributions": round(total_employer_contributions, 2),
            "net_monthly": net_monthly,
            "net_annual": round(net_monthly * 12, 2),
            "fiscal_cost_to_employer_monthly": fiscal_cost,
            "fiscal_cost_to_employer_annual": round(fiscal_cost * 12, 2),
        },
        "calculator_version": CALCULATOR_VERSION,
        "disclaimer": CALCULATOR_DISCLAIMER,
    }


@router.get("/calculator/countries", include_in_schema=True)
async def public_calculator_countries():
    """Return the list of countries supported by the public calculator
    (used by the landing-page UI to populate the country dropdown)."""
    countries = []
    for code, profile in sorted(COUNTRY_PROFILES.items()):
        countries.append({
            "code": code,
            "name": profile.get("name", code),
            "flag": profile.get("flag", ""),
            "currency": profile.get("currency", ""),
            "currency_symbol": profile.get("currency_symbol", ""),
            "region": profile.get("region", ""),
        })
    return {"total": len(countries), "countries": countries}
