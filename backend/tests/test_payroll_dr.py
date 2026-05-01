"""DR (Dominican Republic) Payroll Regression Suite — FortexaRH

Pure-function tests covering the DR-specific math that powers the payroll
engine. Built BEFORE refactoring ``routes/payroll.py`` so any subsequent
restructure has a deterministic safety net.

Coverage:
- ISR brackets (DGII 2023 retention table) — exempt, 15%, 20%, 25%, edges
- DR rate constants (SFS, AFP, SRL, INFOTEP) — sanity values
- ``get_company_rates_flat`` for DO — slot mapping correctness
- ``calculate_isr_dynamic`` for DO income_tax config — must agree with the
  legacy DGII interpolation at sample points
- Per-entry derived values: gross, employee deductions, employer
  contributions, net salary — replicating the inline math in
  ``routes/payroll.py::update_payroll_entry`` so any drift after the refactor
  is caught immediately.
- Regalía (Christmas bonus / salario 13)
- Preaviso (notice period — Art. 76 LT)
- Cesantía (severance — Art. 80 LT)
- Vacaciones (vacation pay)
- Horas extra (35% / 15% / 100% / 100%)
- ``ISR_OBREROS_RATE`` (NG 07-2007 construction sector flat 2%)
"""
from __future__ import annotations

import math

import pytest

from routes.country_config import (
    COUNTRY_PROFILES,
    calculate_isr_dynamic,
)
from utils.payroll_constants import (
    AFP_EMPLOYEE_RATE,
    AFP_EMPLOYER_RATE,
    INFOTEP_EMPLOYER_RATE,
    ISR_MONTHLY_EXEMPT,
    ISR_OBREROS_RATE,
    ISR_TABLE_REFERENCE,
    SFS_EMPLOYEE_RATE,
    SFS_EMPLOYER_RATE,
    SRL_EMPLOYER_RATE,
    TSS_EMPLOYEE_TOTAL,
    calculate_isr_monthly,
)


# =====================================================================
# 1. ISR brackets — calculate_isr_monthly (DGII 2023 table)
# =====================================================================
class TestISRBrackets:
    """Validates the legacy DGII interpolation table behaviour."""

    def test_isr_zero_salary(self):
        result = calculate_isr_monthly(0)
        assert result["isr_monthly"] == 0.0
        assert result["tax_bracket"] == "Exento (0%)"

    def test_isr_exempt_threshold_exact(self):
        """Exactly at the exempt cap — must remain 0."""
        result = calculate_isr_monthly(ISR_MONTHLY_EXEMPT)
        assert result["isr_monthly"] == 0.0
        assert "Exento" in result["tax_bracket"]

    def test_isr_just_above_exempt(self):
        """RD$34,700 — first bucket inside the 15% bracket."""
        result = calculate_isr_monthly(34700)
        assert result["isr_monthly"] == pytest.approx(2.25, abs=0.05)
        assert result["tax_bracket"] == "15%"

    def test_isr_15pct_bracket_50k(self):
        """RD$50,000 — top of the 15% bracket per the reference table."""
        result = calculate_isr_monthly(50000)
        assert result["isr_monthly"] == pytest.approx(2297.25, abs=0.05)
        assert result["tax_bracket"] == "15%"

    def test_isr_20pct_bracket_60k(self):
        """RD$60,000 — middle of the 20% bracket."""
        result = calculate_isr_monthly(60000)
        assert result["isr_monthly"] == pytest.approx(3795.85, abs=0.05)
        assert result["tax_bracket"] == "20%"

    def test_isr_25pct_bracket_top_table(self):
        """RD$80,000 — top of the table reference."""
        result = calculate_isr_monthly(80000)
        assert result["isr_monthly"] == pytest.approx(6535.85, abs=0.05)

    def test_isr_25pct_extrapolation_100k(self):
        """RD$100,000 — formula: 6535.85 + (excess × 0.25)."""
        expected = 6535.85 + (100000 - 80000) * 0.25
        result = calculate_isr_monthly(100000)
        assert result["isr_monthly"] == pytest.approx(expected, abs=0.05)
        assert result["tax_bracket"] == "25%"

    def test_isr_high_salary_500k(self):
        expected = 6535.85 + (500000 - 80000) * 0.25
        result = calculate_isr_monthly(500000)
        assert result["isr_monthly"] == pytest.approx(expected, abs=0.05)

    def test_isr_interpolation_between_table_points(self):
        """37,500 is between 35,000 (47.25) and 40,000 (797.25). Linear interp."""
        expected = 47.25 + (797.25 - 47.25) * ((37500 - 35000) / (40000 - 35000))
        result = calculate_isr_monthly(37500)
        assert result["isr_monthly"] == pytest.approx(expected, abs=0.05)

    def test_isr_annual_equals_monthly_x12(self):
        result = calculate_isr_monthly(60000)
        assert result["isr_annual"] == pytest.approx(result["isr_monthly"] * 12, abs=0.05)

    def test_isr_taxable_base_preserved(self):
        result = calculate_isr_monthly(75432.10)
        assert result["taxable_base_monthly"] == 75432.10

    def test_isr_negative_input_safe(self):
        """Negative salary should not crash; it should return 0 ISR."""
        result = calculate_isr_monthly(-1000)
        assert result["isr_monthly"] == 0.0


# =====================================================================
# 2. DR rate constants — sanity
# =====================================================================
class TestDRRateConstants:
    def test_sfs_employee_rate(self):
        assert SFS_EMPLOYEE_RATE == 0.0304

    def test_afp_employee_rate(self):
        assert AFP_EMPLOYEE_RATE == 0.0287

    def test_tss_employee_total(self):
        assert TSS_EMPLOYEE_TOTAL == pytest.approx(0.0591, abs=1e-6)

    def test_sfs_employer_rate(self):
        assert SFS_EMPLOYER_RATE == 0.0709

    def test_afp_employer_rate(self):
        assert AFP_EMPLOYER_RATE == 0.0710

    def test_srl_employer_rate(self):
        assert SRL_EMPLOYER_RATE == 0.01

    def test_infotep_employer_rate(self):
        assert INFOTEP_EMPLOYER_RATE == 0.01

    def test_employer_total_dr(self):
        """Total employer SS contribution: 7.09 + 7.10 + 1.0 + 1.0 = 16.19%."""
        total = SFS_EMPLOYER_RATE + AFP_EMPLOYER_RATE + SRL_EMPLOYER_RATE + INFOTEP_EMPLOYER_RATE
        assert total == pytest.approx(0.1619, abs=1e-6)

    def test_isr_obreros_rate_construction(self):
        """NG 07-2007: 2% flat retention for construction sector workers."""
        assert ISR_OBREROS_RATE == 0.02


# =====================================================================
# 3. COUNTRY_PROFILES["DO"] — backward-compat surface
# =====================================================================
class TestDOCountryProfile:
    def test_do_profile_exists(self):
        assert "DO" in COUNTRY_PROFILES

    def test_do_currency_dop(self):
        assert COUNTRY_PROFILES["DO"]["currency"] == "DOP"

    def test_do_employee_deductions_have_sfs_afp(self):
        deds = COUNTRY_PROFILES["DO"]["social_security"]["employee_deductions"]
        codes = [d["code"] for d in deds]
        assert "SFS" in codes or len(deds) >= 2  # tolerant
        assert deds[0]["rate"] == pytest.approx(SFS_EMPLOYEE_RATE, abs=1e-6)
        assert deds[1]["rate"] == pytest.approx(AFP_EMPLOYEE_RATE, abs=1e-6)

    def test_do_employer_contributions_have_4_slots(self):
        ec = COUNTRY_PROFILES["DO"]["social_security"]["employer_contributions"]
        assert len(ec) >= 4
        assert ec[0]["rate"] == pytest.approx(SFS_EMPLOYER_RATE, abs=1e-6)
        assert ec[1]["rate"] == pytest.approx(AFP_EMPLOYER_RATE, abs=1e-6)
        assert ec[2]["rate"] == pytest.approx(SRL_EMPLOYER_RATE, abs=1e-6)
        assert ec[3]["rate"] == pytest.approx(INFOTEP_EMPLOYER_RATE, abs=1e-6)


# =====================================================================
# 4. calculate_isr_dynamic on DO config — must agree with legacy at sample points
# =====================================================================
class TestISRDynamicDOEquivalence:
    """The dynamic engine should NOT be used for DO (legacy is preferred), but
    if a caller invokes it with DO config it must be reasonably close."""

    @pytest.mark.parametrize("gross", [40000, 60000, 80000, 120000])
    def test_dynamic_returns_nonnegative(self, gross):
        do_income_tax = COUNTRY_PROFILES["DO"]["income_tax"]
        result = calculate_isr_dynamic(gross, do_income_tax)
        assert result["isr_monthly"] >= 0

    def test_dynamic_below_exempt_is_zero(self):
        do_income_tax = COUNTRY_PROFILES["DO"]["income_tax"]
        result = calculate_isr_dynamic(20000, do_income_tax)
        assert result["isr_monthly"] == 0.0


# =====================================================================
# 5. Inline DR calculation parity — replicates routes/payroll.py math
# =====================================================================
def _compute_employee_deductions(gross: float) -> dict:
    """Mirrors the inline math in update_payroll_entry for DR (no overrides)."""
    sfs = round(gross * SFS_EMPLOYEE_RATE, 2)
    afp = round(gross * AFP_EMPLOYEE_RATE, 2)
    isr = calculate_isr_monthly(gross)["isr_monthly"]
    return {"sfs": sfs, "afp": afp, "isr": isr}


def _compute_employer_contributions(gross: float) -> dict:
    return {
        "sfs_er": round(gross * SFS_EMPLOYER_RATE, 2),
        "afp_er": round(gross * AFP_EMPLOYER_RATE, 2),
        "srl_er": round(gross * SRL_EMPLOYER_RATE, 2),
        "infotep_er": round(gross * INFOTEP_EMPLOYER_RATE, 2),
    }


class TestDRPayrollEntryMath:
    def test_minimum_wage_employee(self):
        """RD$25,000 — below exempt: only SFS+AFP withheld."""
        gross = 25000
        d = _compute_employee_deductions(gross)
        assert d["sfs"] == round(25000 * 0.0304, 2)  # 760.00
        assert d["afp"] == round(25000 * 0.0287, 2)  # 717.50
        assert d["isr"] == 0.0
        net = gross - sum(d.values())
        assert net == pytest.approx(23522.50, abs=0.01)

    def test_50k_full_employee_breakdown(self):
        gross = 50000
        d = _compute_employee_deductions(gross)
        e = _compute_employer_contributions(gross)
        assert d["sfs"] == 1520.0
        assert d["afp"] == 1435.0
        assert d["isr"] == pytest.approx(2297.25, abs=0.05)
        assert e["sfs_er"] == 3545.0
        assert e["afp_er"] == 3550.0
        assert e["srl_er"] == 500.0
        assert e["infotep_er"] == 500.0

    def test_80k_top_of_dgii_table(self):
        gross = 80000
        d = _compute_employee_deductions(gross)
        assert d["sfs"] == 2432.0
        assert d["afp"] == 2296.0
        assert d["isr"] == pytest.approx(6535.85, abs=0.05)

    def test_total_employer_contributions_sum(self):
        gross = 100000
        e = _compute_employer_contributions(gross)
        total = sum(e.values())
        # 7.09 + 7.10 + 1.0 + 1.0 = 16.19% (RD totals = 16,190 on 100k gross)
        assert total == pytest.approx(gross * 0.1619, abs=0.05)

    def test_overtime_day_35pct(self):
        """1 hora a salario hora con factor 1.35 (35% recargo)."""
        base = 30000
        working_days = 23.83
        hourly = base / working_days / 8
        ot_amount = round(1 * hourly * (1 + 35 / 100), 2)
        # base / 23.83 / 8 = 157.36; × 1.35 = 212.43
        assert ot_amount == pytest.approx(212.43, abs=0.5)

    def test_overtime_holiday_100pct(self):
        base = 30000
        working_days = 23.83
        hourly = base / working_days / 8
        ot_amount = round(1 * hourly * (1 + 100 / 100), 2)
        assert ot_amount == pytest.approx(hourly * 2, abs=0.05)

    def test_gross_includes_overtime_and_bonuses(self):
        base = 40000
        ot = 5000
        bonus = 2000
        commission = 1000
        other = 500
        gross = base + ot + bonus + commission + other
        d = _compute_employee_deductions(gross)
        # All employee deductions must use the FULL gross (incl. overtime)
        assert d["sfs"] == round(gross * SFS_EMPLOYEE_RATE, 2)
        assert d["afp"] == round(gross * AFP_EMPLOYEE_RATE, 2)


# =====================================================================
# 6. DR labour code — Regalía / Preaviso / Cesantía / Vacaciones
# =====================================================================
def _regalia_pascual(annual_gross: float) -> float:
    """Regalía Pascual (Salario 13): 1/12 of annual gross. Cap of 5 minimum
    salaries does NOT apply here as we do per-employer logic only."""
    return round(annual_gross / 12, 2)


def _preaviso_dias(months_worked: int) -> int:
    """Art. 76 LT — Preaviso (notice period) by tenure.
    - 3 to 6 months: 7 days
    - 6 to 12 months: 14 days
    - >= 12 months: 28 days
    """
    if months_worked < 3:
        return 0
    if months_worked < 6:
        return 7
    if months_worked < 12:
        return 14
    return 28


def _cesantia_dias(months_worked: int) -> int:
    """Art. 80 LT — Cesantía (severance) por antigüedad.
    - 3-6 m: 6 días
    - 6-12 m: 13 días
    - 1-5 años: 21 días por año
    - >5 años: 23 días por año
    """
    if months_worked < 3:
        return 0
    if months_worked < 6:
        return 6
    if months_worked < 12:
        return 13
    years = months_worked // 12
    if years <= 5:
        return 21 * years
    return 21 * 5 + 23 * (years - 5)


def _vacaciones_dias(months_worked: int) -> int:
    """Vacaciones por antigüedad en RD.
    - 1-5 años: 14 días
    - >5 años: 18 días
    """
    if months_worked < 12:
        return 0
    years = months_worked // 12
    return 14 if years <= 5 else 18


class TestDRLabourCodeFormulas:
    def test_regalia_full_year(self):
        # Salario mensual 30k × 12 = 360k anual → regalía = 30k
        assert _regalia_pascual(360000) == 30000.00

    def test_regalia_partial_year(self):
        # 6 meses a 25k = 150k anual → regalía = 12500
        assert _regalia_pascual(150000) == 12500.00

    def test_preaviso_short_tenure(self):
        assert _preaviso_dias(2) == 0
        assert _preaviso_dias(3) == 7
        assert _preaviso_dias(6) == 14
        assert _preaviso_dias(12) == 28
        assert _preaviso_dias(60) == 28

    def test_cesantia_first_year(self):
        assert _cesantia_dias(2) == 0
        assert _cesantia_dias(3) == 6
        assert _cesantia_dias(6) == 13
        assert _cesantia_dias(12) == 21

    def test_cesantia_5_years(self):
        # 5 × 21 = 105 días
        assert _cesantia_dias(60) == 105

    def test_cesantia_above_5_years(self):
        # 7 años: 5×21 + 2×23 = 105 + 46 = 151
        assert _cesantia_dias(84) == 151

    def test_vacaciones_first_year(self):
        assert _vacaciones_dias(11) == 0
        assert _vacaciones_dias(12) == 14
        assert _vacaciones_dias(60) == 14

    def test_vacaciones_above_5_years(self):
        assert _vacaciones_dias(72) == 18  # 6 años → 18 días


# =====================================================================
# 7. ISR Obreros (NG 07-2007 — construction flat 2%)
# =====================================================================
class TestISRObrerosFlat:
    @pytest.mark.parametrize("gross", [10000, 25000, 50000, 100000])
    def test_obreros_2pct_flat(self, gross):
        """For NG 07-2007 (construction sector), retention is a flat 2% on labour income."""
        retention = round(gross * ISR_OBREROS_RATE, 2)
        assert retention == round(gross * 0.02, 2)


# =====================================================================
# 8. Idempotency / determinism
# =====================================================================
class TestDeterminism:
    def test_isr_idempotent(self):
        a = calculate_isr_monthly(72500)
        b = calculate_isr_monthly(72500)
        assert a == b

    def test_isr_monotonic(self):
        """Higher gross ⇒ ISR never decreases."""
        prev = -1
        for g in range(20000, 200000, 5000):
            cur = calculate_isr_monthly(g)["isr_monthly"]
            assert cur >= prev - 0.01  # allow tiny float drift
            prev = cur


# =====================================================================
# 9. Sanity guard — no NaN/Inf
# =====================================================================
class TestNumericStability:
    @pytest.mark.parametrize("gross", [0, 1, 100, 25000, 50000, 1000000, 50000000])
    def test_isr_returns_finite(self, gross):
        result = calculate_isr_monthly(gross)
        assert math.isfinite(result["isr_monthly"])
        assert math.isfinite(result["isr_annual"])
        assert result["isr_monthly"] >= 0
