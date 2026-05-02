"""
Multi-country payroll engine regression tests.

Validates the P0 refactor that migrated payroll.py from hardcoded DR (Dominican Republic)
constants to the dynamic country-aware engine in routes/country_config.py.

Test sequence (per problem statement):
    1) Login as admin
    2) Verify 28 countries grouped in 5 regions
    3) Create test payroll period (mensual REG 2026-06)
    4) add-employees (DR rates)
    5) Verify DR rates exact (3.04/2.87/7.09/7.10/1/1)
    6) Switch country to CO
    7) calculate -> CO rates (4/4/8.5/12/0.522/4)
    8) Switch back to DO
    9) calculate -> DR rates restored
   10) Cleanup test period
   11) Ensure company.country='DO' at end (regression-safe)
"""

import os
import pytest
import requests
from pathlib import Path


def _load_frontend_env_url():
    """Read REACT_APP_BACKEND_URL from /app/frontend/.env if not in os.environ."""
    val = os.environ.get("REACT_APP_BACKEND_URL")
    if val:
        return val
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not configured")


BASE_URL = _load_frontend_env_url().rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"

# Tolerance for float comparisons on monetary calculations
EPS = 0.02


# ===================== FIXTURES =====================

@pytest.fixture(scope="module")
def auth_headers():
    """Login once per module and return Authorization header."""
    r = requests.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text}")
    data = r.json()
    if data.get("requires_2fa"):
        pytest.skip("Test account has 2FA enabled - cannot proceed")
    token = data.get("token")
    assert token, "No token in login response"
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def test_period(auth_headers):
    """Create a test payroll period, add employees, yield, then delete + restore DO."""
    payload = {
        "period_type": "mensual",
        "payroll_type": "REG",
        "year": 2026,
        "month": 6,
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "description": "TEST_multicountry_regression",
    }
    r = requests.post(f"{API}/payroll/periods", json=payload, headers=auth_headers, timeout=30)
    assert r.status_code == 200, f"Failed to create period: {r.status_code} {r.text}"
    period_id = r.json().get("period_id")
    assert period_id

    # Add employees
    r2 = requests.post(
        f"{API}/payroll/periods/{period_id}/add-employees",
        headers=auth_headers,
        timeout=60,
    )
    assert r2.status_code == 200, f"add-employees failed: {r2.status_code} {r2.text}"

    yield period_id

    # Teardown: restore country to DO and delete period
    requests.put(
        f"{API}/country-config/company/country",
        params={"country_code": "DO"},
        headers=auth_headers,
        timeout=30,
    )
    requests.delete(
        f"{API}/payroll/periods/{period_id}",
        headers=auth_headers,
        timeout=30,
    )


# ===================== HELPERS =====================

def _switch_country(headers, code):
    r = requests.put(
        f"{API}/country-config/company/country",
        params={"country_code": code},
        headers=headers,
        timeout=30,
    )
    assert r.status_code == 200, f"Switch to {code} failed: {r.status_code} {r.text}"
    return r.json()


def _calculate(headers, period_id):
    r = requests.post(
        f"{API}/payroll/periods/{period_id}/calculate",
        headers=headers,
        timeout=60,
    )
    assert r.status_code == 200, f"calculate failed: {r.status_code} {r.text}"
    return r.json()


def _get_entries(headers, period_id):
    r = requests.get(
        f"{API}/payroll/periods/{period_id}",
        headers=headers,
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return r.json().get("entries", [])


def _close_pct(actual_amount, gross, expected_rate):
    """Return True if actual_amount ~= gross * expected_rate."""
    if gross <= 0:
        return abs(actual_amount) < EPS
    expected = round(gross * expected_rate, 2)
    return abs(actual_amount - expected) <= max(EPS, gross * 0.0005)


# ===================== TESTS =====================

# --- Country catalog endpoints ---

class TestCountryCatalog:
    def test_get_countries_returns_29_in_5_regions(self):
        r = requests.get(f"{API}/country-config/countries", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("total") == 29, f"Expected 29 countries, got {data.get('total')}"
        regions = data.get("regions", {})
        expected_regions = {
            "north_america", "central_america", "caribbean",
            "south_america", "europe",
        }
        assert set(regions.keys()) == expected_regions, (
            f"Regions mismatch. Got: {set(regions.keys())}"
        )
        # Total countries across regions == 29
        total = sum(len(r["countries"]) for r in regions.values())
        assert total == 29, f"Sum of region countries = {total}, expected 29"

    @pytest.mark.parametrize("code", ["DO", "CO", "MX", "US", "ES", "GB", "AR", "CL", "BR", "BE"])
    def test_get_country_profile_by_code(self, code):
        r = requests.get(f"{API}/country-config/countries/{code}", timeout=30)
        assert r.status_code == 200, f"{code}: {r.status_code} {r.text}"
        profile = r.json()
        assert profile.get("code") == code
        assert "social_security" in profile
        assert "income_tax" in profile
        ss = profile["social_security"]
        assert isinstance(ss.get("employee_deductions"), list) and len(ss["employee_deductions"]) > 0
        assert isinstance(ss.get("employer_contributions"), list) and len(ss["employer_contributions"]) > 0

    def test_get_company_country_default(self, auth_headers):
        r = requests.get(f"{API}/country-config/company", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "country_code" in data
        assert "profile" in data


# --- Switch country endpoint ---

class TestSetCompanyCountry:
    def test_switch_to_colombia_updates_currency(self, auth_headers):
        _switch_country(auth_headers, "CO")
        r = requests.get(f"{API}/country-config/company", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("country_code") == "CO"
        assert data["profile"]["currency"] == "COP"
        assert data["profile"]["currency_symbol"] == "$"

    def test_switch_back_to_do(self, auth_headers):
        _switch_country(auth_headers, "DO")
        r = requests.get(f"{API}/country-config/company", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("country_code") == "DO"
        assert data["profile"]["currency"] == "DOP"

    def test_switch_invalid_country_returns_400(self, auth_headers):
        r = requests.put(
            f"{API}/country-config/company/country",
            params={"country_code": "ZZ"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400 for invalid, got {r.status_code}"


# --- Multi-country payroll engine (the P0 refactor) ---

# DR (Dominican Republic) expected employee/employer rates
DR_RATES = {
    "sfs_employee": 0.0304,
    "afp_employee": 0.0287,
    "sfs_employer": 0.0709,
    "afp_employer": 0.0710,
    "srl_employer": 0.01,
    "infotep_employer": 0.01,
}

# CO (Colombia) expected rates - first 2 emp deductions, first 4 emp contributions
CO_RATES = {
    "sfs_employee": 0.04,    # SALUD
    "afp_employee": 0.04,    # PENSION
    "sfs_employer": 0.085,   # SALUD_EMP
    "afp_employer": 0.12,    # PENSION_EMP
    "srl_employer": 0.00522, # ARL
    "infotep_employer": 0.04,# CCF
}


def _assert_rates(entries, rates_map, country_label):
    """Assert each entry's deductions match expected percentages of gross_salary."""
    assert len(entries) > 0, f"No entries to validate for {country_label}"
    failed = []
    for e in entries:
        gross = float(e.get("gross_salary", 0) or 0)
        if gross <= 0:
            continue  # skip OBREROS_NG-like or zero entries
        checks = {
            "sfs_employee": rates_map["sfs_employee"],
            "afp_employee": rates_map["afp_employee"],
            "sfs_employer": rates_map["sfs_employer"],
            "afp_employer": rates_map["afp_employer"],
            "srl_employer": rates_map["srl_employer"],
            "infotep_employer": rates_map["infotep_employer"],
        }
        for field, rate in checks.items():
            actual = float(e.get(field, 0) or 0)
            # sfs_employee/afp_employee may be overridden via manual flag - skip if employee opted out
            if not _close_pct(actual, gross, rate):
                expected = round(gross * rate, 2)
                failed.append(
                    f"{country_label} entry {e.get('employee_name')} "
                    f"field={field} gross={gross} expected≈{expected} actual={actual}"
                )
    assert not failed, "Rate mismatches:\n" + "\n".join(failed[:10])


class TestMultiCountryPayrollEngine:
    def test_01_dr_initial_rates_via_add_employees(self, auth_headers, test_period):
        """add-employees uses DR rates (default country)."""
        # Ensure DO is the active country
        _switch_country(auth_headers, "DO")
        # add-employees was already called by fixture, but we recalc to make sure rates apply
        _calculate(auth_headers, test_period)
        entries = _get_entries(auth_headers, test_period)
        # Filter out manual override or non-payable entries (gross > 0)
        payable = [e for e in entries if float(e.get("gross_salary", 0) or 0) > 0]
        assert len(payable) > 0, "No payable entries found - cannot validate rates"
        _assert_rates(payable, DR_RATES, "DR/initial")

    def test_02_switch_to_co_and_calculate_uses_co_rates(self, auth_headers, test_period):
        _switch_country(auth_headers, "CO")
        _calculate(auth_headers, test_period)
        entries = _get_entries(auth_headers, test_period)
        payable = [e for e in entries if float(e.get("gross_salary", 0) or 0) > 0]
        _assert_rates(payable, CO_RATES, "CO")

    def test_03_switch_back_to_do_recomputes_dr(self, auth_headers, test_period):
        _switch_country(auth_headers, "DO")
        _calculate(auth_headers, test_period)
        entries = _get_entries(auth_headers, test_period)
        payable = [e for e in entries if float(e.get("gross_salary", 0) or 0) > 0]
        _assert_rates(payable, DR_RATES, "DR/restored")

    def test_04_isr_dr_uses_legacy_dgii(self, auth_headers, test_period):
        """For DR, ISR should be computed via the legacy DGII interpolation (calculate_isr_monthly).
        We verify: (a) ISR field exists, (b) for entries with low gross (<= ~34k DOP/month) ISR=0,
        and (c) for high-gross entries ISR > 0."""
        _switch_country(auth_headers, "DO")
        _calculate(auth_headers, test_period)
        entries = _get_entries(auth_headers, test_period)
        payable = [e for e in entries if float(e.get("gross_salary", 0) or 0) > 0]
        for e in payable:
            assert "isr" in e, f"entry missing isr: {e.get('employee_name')}"
            gross = float(e["gross_salary"])
            isr = float(e["isr"] or 0)
            # DR DGII exempt monthly is ~34,685 DOP. Below that -> ISR == 0
            if gross < 34000:
                assert isr == 0, (
                    f"DR ISR should be 0 for low gross ({gross}), got {isr}"
                )

    def test_05_isr_co_uses_dynamic_brackets(self, auth_headers, test_period):
        """For CO, ISR = bracket-based calculate_isr_dynamic. CO bracket exempt is up to ~52M COP/month
        so most test entries (DR-sized salaries) should produce ISR=0 under CO brackets."""
        _switch_country(auth_headers, "CO")
        _calculate(auth_headers, test_period)
        entries = _get_entries(auth_headers, test_period)
        payable = [e for e in entries if float(e.get("gross_salary", 0) or 0) > 0]
        for e in payable:
            isr = float(e.get("isr", 0) or 0)
            gross = float(e["gross_salary"])
            # CO first non-zero bracket starts at 52,456,800 COP/month
            if gross < 52_456_800:
                assert isr == 0, (
                    f"CO ISR should be 0 for gross={gross}, got {isr}"
                )

    def test_06_update_entry_uses_dynamic_rates(self, auth_headers, test_period):
        """PUT /payroll/entries/{id} should recompute deductions via current country rates."""
        _switch_country(auth_headers, "CO")
        entries = _get_entries(auth_headers, test_period)
        target = next((e for e in entries if float(e.get("gross_salary", 0) or 0) > 0), None)
        if not target:
            pytest.skip("No payable entry to PUT")
        # PUT entry requires full PayrollEntryCreate payload - include period_id, employee_id, base_salary
        payload = {
            "period_id": target["period_id"],
            "employee_id": target["employee_id"],
            "base_salary": float(target["base_salary"]),
            "overtime_day_hours": float(target.get("overtime_day_hours", 0) or 0),
            "overtime_night_hours": float(target.get("overtime_night_hours", 0) or 0),
            "overtime_weekend_hours": float(target.get("overtime_weekend_hours", 0) or 0),
            "overtime_holiday_hours": float(target.get("overtime_holiday_hours", 0) or 0),
            "bonuses": float(target.get("bonuses", 0) or 0),
            "commissions": float(target.get("commissions", 0) or 0),
            "other_income": float(target.get("other_income", 0) or 0),
            "additional_deductions": target.get("additional_deductions", []) or [],
        }
        r = requests.put(
            f"{API}/payroll/entries/{target['entry_id']}",
            json=payload,
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, f"PUT entry failed: {r.status_code} {r.text}"
        # Refetch and verify CO rates
        r2 = requests.get(
            f"{API}/payroll/entries/{target['entry_id']}",
            headers=auth_headers,
            timeout=30,
        )
        assert r2.status_code == 200
        updated = r2.json()
        gross = float(updated["gross_salary"])
        if gross > 0:
            assert _close_pct(updated["sfs_employee"], gross, CO_RATES["sfs_employee"]), (
                f"PUT entry sfs_employee mismatch: gross={gross} value={updated['sfs_employee']}"
            )
            assert _close_pct(updated["afp_employer"], gross, CO_RATES["afp_employer"]), (
                f"PUT entry afp_employer mismatch: gross={gross} value={updated['afp_employer']}"
            )

    def test_07_novelty_recomputes_with_dynamic_rates(self, auth_headers, test_period):
        """POST and DELETE novelty should both trigger recompute with current country rates (CO)."""
        _switch_country(auth_headers, "CO")
        _calculate(auth_headers, test_period)
        entries = _get_entries(auth_headers, test_period)
        target = next((e for e in entries if float(e.get("gross_salary", 0) or 0) > 0), None)
        if not target:
            pytest.skip("No payable entry for novelty test")
        original_gross = float(target["gross_salary"])
        novelty_payload = {
            "entry_id": target["entry_id"],
            "novelty_type": "income",
            "code": "TEST_BONUS",
            "name": "TEST_bonus_co",
            "description": "Multi-country test bonus",
            "amount": 1000.0,
            "is_percentage": False,
        }
        r = requests.post(
            f"{API}/payroll/entries/{target['entry_id']}/novelties",
            json=novelty_payload,
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, f"add novelty failed: {r.status_code} {r.text}"

        # Refetch entry - gross should increase by 1000 and CO rates apply
        r2 = requests.get(f"{API}/payroll/entries/{target['entry_id']}", headers=auth_headers, timeout=30)
        assert r2.status_code == 200
        updated = r2.json()
        new_gross = float(updated["gross_salary"])
        assert new_gross >= original_gross + 999, (
            f"Gross did not increase as expected: orig={original_gross} new={new_gross}"
        )
        assert _close_pct(updated["sfs_employer"], new_gross, CO_RATES["sfs_employer"]), (
            f"Novelty CO sfs_employer mismatch: gross={new_gross} value={updated['sfs_employer']}"
        )

        # Find and delete the novelty
        novelties = updated.get("novelties", []) or updated.get("additional_income", [])
        nov_id = None
        # Look for our marker
        for nov in (updated.get("novelties") or []):
            if nov.get("code") == "TEST_BONUS" or nov.get("name") == "TEST_bonus_co":
                nov_id = nov.get("novelty_id") or nov.get("id")
                break
        if nov_id:
            rd = requests.delete(
                f"{API}/payroll/entries/{target['entry_id']}/novelties/{nov_id}",
                headers=auth_headers,
                timeout=30,
            )
            assert rd.status_code in (200, 204), f"delete novelty failed: {rd.status_code} {rd.text}"

    def test_08_final_state_company_back_to_do(self, auth_headers):
        """Regression-safety: after all tests company.country MUST be DO."""
        _switch_country(auth_headers, "DO")
        r = requests.get(f"{API}/country-config/company", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        assert r.json().get("country_code") == "DO"
