"""
P1 + P2 Backend Regression Tests - FortexaRH

Validates:
(P1) New endpoint GET /api/country-config/rates-flat
     - Returns country_code, country_name, currency, currency_symbol,
       labels (full names), codes (short codes), rates, working_days_month
     - Switching DO<->CO changes labels/codes/rates correctly

(P2) Multi-country adaptability:
     - /api/dgii-reports/summary: adapts to company country
       * DR: SFS/AFP/SRL/INFOTEP slots, 4 employer contributions
       * CO: mapped to slots + 6 employer contributions in detail
     - DR-specific endpoints gated with 400 when country != DO:
       * /api/dgii-reports/tss/autodeterminacion
       * /api/dgii-reports/tss/novedades
       * /api/dgii-reports/ir3
       * /api/dgii-reports/ir17
       * /api/payroll/periods/{id}/tss-preview
       * /api/payroll/periods/{id}/tss-report
     - DR regression: endpoints still work when country=DO

Teardown: company country restored to 'DO' at end.
"""

import os
import pytest
import requests
from pathlib import Path


def _load_frontend_env_url():
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

EPS = 1e-6

# Default period for tests that need a DR period (from review request)
EXISTING_DR_PERIOD_ID = "period_42a51c051530"


# ===================== FIXTURES =====================

@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text}")
    data = r.json()
    if data.get("requires_2fa"):
        pytest.skip("2FA enabled on test account")
    token = data.get("token")
    assert token
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _set_country(headers, code):
    r = requests.put(
        f"{API}/country-config/company/country",
        params={"country_code": code},
        headers=headers,
        timeout=30,
    )
    assert r.status_code == 200, f"Failed switching country {code}: {r.status_code} {r.text}"


@pytest.fixture(scope="module", autouse=True)
def restore_do_country(auth_headers):
    """Always restore country to DO at end regardless of test outcome."""
    yield
    try:
        _set_country(auth_headers, "DO")
    except Exception as e:
        print(f"WARN: could not restore country to DO: {e}")


# ===================== P1: /rates-flat endpoint =====================

class TestRatesFlatDR:
    """When company country = DO, /rates-flat returns DR slots."""

    def test_rates_flat_do(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(f"{API}/country-config/rates-flat", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()

        # Top-level fields
        assert data["country_code"] == "DO"
        assert data["country_name"] == "República Dominicana"
        assert data["currency"] == "DOP"
        assert data["currency_symbol"] == "RD$"
        assert data["working_days_month"] == 23.83

        # Rates (DR)
        assert abs(data["sfs_employee_rate"] - 0.0304) < EPS
        assert abs(data["afp_employee_rate"] - 0.0287) < EPS
        assert abs(data["sfs_employer_rate"] - 0.0709) < EPS
        assert abs(data["afp_employer_rate"] - 0.0710) < EPS
        assert abs(data["srl_employer_rate"] - 0.01) < EPS
        assert abs(data["infotep_employer_rate"] - 0.01) < EPS

        # Codes (short DR)
        codes = data["codes"]
        assert codes["sfs_employee"] == "SFS"
        assert codes["afp_employee"] == "AFP"
        assert codes["sfs_employer"] == "SFS_EMP"
        assert codes["afp_employer"] == "AFP_EMP"
        assert codes["srl_employer"] == "SRL"
        assert codes["infotep_employer"] == "INFOTEP"

        # Labels (full names)
        labels = data["labels"]
        assert "SFS" in labels["sfs_employee"] or "Salud" in labels["sfs_employee"]
        assert "AFP" in labels["afp_employee"] or "Pensión" in labels["afp_employee"] or "Pension" in labels["afp_employee"]
        for key in ("sfs_employee", "afp_employee", "sfs_employer", "afp_employer", "srl_employer", "infotep_employer"):
            assert labels[key], f"Label {key} should be non-empty"


class TestRatesFlatCO:
    """When company country = CO, /rates-flat returns CO slots/codes/labels."""

    def test_rates_flat_co(self, auth_headers):
        _set_country(auth_headers, "CO")
        try:
            r = requests.get(f"{API}/country-config/rates-flat", headers=auth_headers, timeout=30)
            assert r.status_code == 200, r.text
            data = r.json()

            assert data["country_code"] == "CO"
            assert data["country_name"] == "Colombia"
            assert data["currency"] == "COP"

            # CO rates: SALUD 4, PENSION 4, SALUD_EMP 8.5, PENSION_EMP 12, ARL 0.522, CCF 4
            assert abs(data["sfs_employee_rate"] - 0.04) < EPS
            assert abs(data["afp_employee_rate"] - 0.04) < EPS
            assert abs(data["sfs_employer_rate"] - 0.085) < EPS
            assert abs(data["afp_employer_rate"] - 0.12) < EPS
            assert abs(data["srl_employer_rate"] - 0.00522) < EPS
            assert abs(data["infotep_employer_rate"] - 0.04) < EPS

            # CO codes
            codes = data["codes"]
            assert codes["sfs_employee"] == "SALUD"
            assert codes["afp_employee"] == "PENSION"
            assert codes["sfs_employer"] == "SALUD_EMP"
            assert codes["afp_employer"] == "PENSION_EMP"
            assert codes["srl_employer"] == "ARL"
            assert codes["infotep_employer"] == "CCF"

            # CO labels (full Spanish names)
            labels = data["labels"]
            assert "Salud" in labels["sfs_employee"]
            assert "Pensión" in labels["afp_employee"] or "Pension" in labels["afp_employee"]
            assert "Riesgos" in labels["srl_employer"] or "ARL" in labels["srl_employer"]

            # Full 6 CO employer contributions available in detail
            detail = data.get("employer_contributions_detail", [])
            codes_all = [c["code"] for c in detail]
            for expected in ("SALUD_EMP", "PENSION_EMP", "ARL", "CCF", "ICBF", "SENA"):
                assert expected in codes_all, f"Missing {expected} in employer_contributions_detail: {codes_all}"
        finally:
            _set_country(auth_headers, "DO")


# ===================== P2: /dgii-reports/summary multi-country =====================

class TestDgiiSummaryMultiCountry:

    def test_summary_dr(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(
            f"{API}/dgii-reports/summary",
            params={"period": "2026-03"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["country_code"] == "DO"
        assert data["country_name"] == "República Dominicana"
        assert data["currency"] == "DOP"
        assert "tss" in data
        assert "total_tss" in data["tss"]

        # Employer contributions detail should have 4 DR items
        detail = data["tss"].get("employer_contributions_detail", [])
        codes_all = [c["code"] for c in detail]
        assert len(detail) == 4, f"Expected 4 DR employer contributions, got {len(detail)}: {codes_all}"
        for expected in ("SFS_EMP", "AFP_EMP", "SRL", "INFOTEP"):
            assert expected in codes_all, f"Missing DR code {expected}: {codes_all}"

        # labels / codes present
        assert "labels" in data and "codes" in data
        assert "available_reports" in data and isinstance(data["available_reports"], list)

    def test_summary_co(self, auth_headers):
        _set_country(auth_headers, "CO")
        try:
            r = requests.get(
                f"{API}/dgii-reports/summary",
                params={"period": "2026-03"},
                headers=auth_headers,
                timeout=30,
            )
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["country_code"] == "CO"
            assert data["currency"] == "COP"

            # CO rates mapped into legacy DR slots - verify via math on tss slots
            total_sal = data["total_salaries"]
            if total_sal > 0:
                assert abs(data["tss"]["sfs_employee"] - round(total_sal * 0.04, 2)) < 0.5
                assert abs(data["tss"]["afp_employee"] - round(total_sal * 0.04, 2)) < 0.5
                assert abs(data["tss"]["sfs_employer"] - round(total_sal * 0.085, 2)) < 0.5
                assert abs(data["tss"]["afp_employer"] - round(total_sal * 0.12, 2)) < 0.5
                assert abs(data["tss"]["risk_labor"] - round(total_sal * 0.00522, 2)) < 0.5
                assert abs(data["tss"]["infotep"] - round(total_sal * 0.04, 2)) < 0.5

            # All 6 CO employer contributions in detail
            detail = data["tss"].get("employer_contributions_detail", [])
            codes_all = [c["code"] for c in detail]
            assert len(detail) == 6, f"Expected 6 CO employer contributions, got {len(detail)}: {codes_all}"
            for expected in ("SALUD_EMP", "PENSION_EMP", "ARL", "CCF", "ICBF", "SENA"):
                assert expected in codes_all, f"Missing CO code {expected}: {codes_all}"

            # Employee deductions detail (2 CO)
            edetail = data["tss"].get("employee_deductions_detail", [])
            ecodes = [c["code"] for c in edetail]
            assert "SALUD" in ecodes and "PENSION" in ecodes

            # CO-specific labels
            assert data["labels"]["sfs_employee"].lower().startswith("salud")
            assert data["codes"]["sfs_employee"] == "SALUD"
            assert data["codes"]["afp_employee"] == "PENSION"

            # ISR agency should be DIAN for CO
            assert data["isr"].get("agency") == "DIAN"
        finally:
            _set_country(auth_headers, "DO")


# ===================== P2: DR-specific endpoint guards =====================

class TestDrSpecificGuards:
    """Non-DR country must yield 400; DR must yield 200 for same endpoints."""

    @pytest.fixture(scope="class")
    def switch_co(self, auth_headers):
        _set_country(auth_headers, "CO")
        yield
        _set_country(auth_headers, "DO")

    def test_tss_autodeterminacion_co_blocked(self, auth_headers, switch_co):
        r = requests.get(
            f"{API}/dgii-reports/tss/autodeterminacion",
            params={"period": "2026-03"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400 for non-DR, got {r.status_code}: {r.text}"
        body = r.json()
        detail = body.get("detail", "")
        assert "República Dominicana" in detail or "Dominican" in detail or "DR" in detail

    def test_tss_novedades_co_blocked(self, auth_headers, switch_co):
        r = requests.get(
            f"{API}/dgii-reports/tss/novedades",
            params={"period": "2026-03"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"

    def test_ir3_co_blocked(self, auth_headers, switch_co):
        r = requests.get(
            f"{API}/dgii-reports/ir3",
            params={"period": "2026-03"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"

    def test_ir17_co_blocked(self, auth_headers, switch_co):
        r = requests.get(
            f"{API}/dgii-reports/ir17",
            params={"year": 2026},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"

    def test_tss_preview_co_blocked(self, auth_headers, switch_co):
        r = requests.get(
            f"{API}/payroll/periods/{EXISTING_DR_PERIOD_ID}/tss-preview",
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"

    def test_tss_report_co_blocked(self, auth_headers, switch_co):
        r = requests.get(
            f"{API}/payroll/periods/{EXISTING_DR_PERIOD_ID}/tss-report",
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"


class TestDrRegression:
    """When country=DO, all DR-specific endpoints continue to work."""

    def test_tss_autodeterminacion_dr_ok(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(
            f"{API}/dgii-reports/tss/autodeterminacion",
            params={"period": "2026-03"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, f"Expected 200 for DR, got {r.status_code}: {r.text[:200]}"
        # Content-Type should be text/plain
        assert "text/plain" in r.headers.get("content-type", "")
        # Content-Disposition filename should start with TSS_AUTODETERMINACION
        disp = r.headers.get("content-disposition", "")
        assert "TSS_AUTODETERMINACION" in disp

    def test_tss_novedades_dr_ok(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(
            f"{API}/dgii-reports/tss/novedades",
            params={"period": "2026-03"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, r.text[:200]
        assert "text/plain" in r.headers.get("content-type", "")

    def test_ir3_dr_ok(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(
            f"{API}/dgii-reports/ir3",
            params={"period": "2026-03"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, r.text[:200]
        disp = r.headers.get("content-disposition", "")
        assert "IR3" in disp

    def test_ir17_dr_ok(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(
            f"{API}/dgii-reports/ir17",
            params={"year": 2026},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, r.text[:200]
        disp = r.headers.get("content-disposition", "")
        assert "IR17" in disp

    def test_tss_preview_dr_ok(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(
            f"{API}/payroll/periods/{EXISTING_DR_PERIOD_ID}/tss-preview",
            headers=auth_headers,
            timeout=30,
        )
        # Preview may 200 or 404 depending on period. We accept 200/404 but NOT 400.
        assert r.status_code != 400, f"DR should not be blocked: {r.status_code} {r.text[:200]}"
        assert r.status_code in (200, 404), r.text[:200]

    def test_tss_report_dr_ok(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(
            f"{API}/payroll/periods/{EXISTING_DR_PERIOD_ID}/tss-report",
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code != 400, f"DR should not be blocked: {r.status_code} {r.text[:200]}"
        assert r.status_code in (200, 404), r.text[:200]

    def test_summary_dr_regression(self, auth_headers):
        _set_country(auth_headers, "DO")
        r = requests.get(
            f"{API}/dgii-reports/summary",
            params={"period": "2026-03"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        # DR specific fields
        assert data["country_code"] == "DO"
        assert "tss" in data and "total_tss" in data["tss"]
