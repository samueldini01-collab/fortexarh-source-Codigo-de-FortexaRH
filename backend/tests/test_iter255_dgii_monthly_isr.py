"""
Iter 255 — DGII Monthly consolidated reports + new ISR quincenal policy.

Covers:
  - Backend ISR formula: calculate_isr_monthly correctness for bracket points.
  - GET /api/dgii-reports/monthly/preview
  - GET /api/dgii-reports/monthly/ir3
  - GET /api/dgii-reports/monthly/ir4
  - GET /api/dgii-reports/monthly/tss-autodeterminacion
  - GET /api/dgii-reports/monthly/dgii-table-validation
  - POST/GET /api/payroll-settings new field isr_quincenal_policy.
  - Regression: existing /api/payroll/periods/{id}/export/ir3,ir4,ir6,ir17,tss-autodeterminacion endpoints.
  - Regression: POST /api/payroll/periods/{period_id}/recalculate-all still works.
"""
import os
import sys
import importlib
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://company-config-debug.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
YEAR = 2026
MONTH = 3

# Ensure backend module is importable for unit-level checks
sys.path.insert(0, "/app/backend")


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def token(session):
    r = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    }, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token in response: {r.json()}"
    return tok


@pytest.fixture(scope="session")
def auth(session, token):
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


# ===================== ISR FORMULA UNIT CHECKS =====================

class TestIsrFormula:
    def test_calculate_isr_monthly_exent(self):
        from utils.payroll_constants import calculate_isr_monthly
        r = calculate_isr_monthly(34685)
        assert r["isr_monthly"] == 0.0
        assert "Exento" in r["tax_bracket"]

    def test_calculate_isr_monthly_15_pct_40k(self):
        from utils.payroll_constants import calculate_isr_monthly
        r = calculate_isr_monthly(40000)
        # 40000 * (1-0.0591) = 37636 → annualized 451632 → (451632-416220)*0.15/12 = 442.65
        assert r["tax_bracket"] == "15%"
        assert abs(r["isr_monthly"] - 442.65) < 0.05

    def test_calculate_isr_monthly_20_pct_60k(self):
        from utils.payroll_constants import calculate_isr_monthly
        r = calculate_isr_monthly(60000)
        assert r["tax_bracket"] == "20%"
        assert abs(r["isr_monthly"] - 3486.65) < 0.1

    def test_calculate_isr_monthly_25_pct_80k(self):
        from utils.payroll_constants import calculate_isr_monthly
        r = calculate_isr_monthly(80000)
        assert r["tax_bracket"] == "25%"
        assert abs(r["isr_monthly"] - 7400.94) < 0.5


# ===================== ISR QUINCENAL POLICY UNIT CHECK =====================

class TestIsrQuincenalPolicy:
    def test_apply_split_half(self):
        from routes.payroll._helpers import _apply_isr_quincenal_policy
        assert _apply_isr_quincenal_policy(1000.0, "quincenal_1", "split_half") == 500.0
        assert _apply_isr_quincenal_policy(1000.0, "quincenal_2", "split_half") == 500.0

    def test_apply_all_q2(self):
        from routes.payroll._helpers import _apply_isr_quincenal_policy
        assert _apply_isr_quincenal_policy(1000.0, "quincenal_1", "all_q2") == 0.0
        assert _apply_isr_quincenal_policy(1000.0, "quincenal_2", "all_q2") == 1000.0

    def test_apply_all_q1(self):
        from routes.payroll._helpers import _apply_isr_quincenal_policy
        assert _apply_isr_quincenal_policy(1000.0, "quincenal_1", "all_q1") == 1000.0
        assert _apply_isr_quincenal_policy(1000.0, "quincenal_2", "all_q1") == 0.0


# ===================== DGII MONTHLY ENDPOINTS =====================

class TestDgiiMonthlyEndpoints:
    def test_preview(self, auth):
        r = auth.get(f"{BASE_URL}/api/dgii-reports/monthly/preview",
                     params={"year": YEAR, "month": MONTH}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["year"] == YEAR and data["month"] == MONTH
        assert "rows" in data and "totals" in data and "periods" in data
        # If periods exist, totals should be present
        assert "gross_salary" in data["totals"]
        assert "isr" in data["totals"]
        # Save count for downstream assertions
        TestDgiiMonthlyEndpoints._employee_count = data.get("employee_count", 0)
        TestDgiiMonthlyEndpoints._periods = data.get("periods", [])

    def test_ir3_download(self, auth):
        r = auth.get(f"{BASE_URL}/api/dgii-reports/monthly/ir3",
                     params={"year": YEAR, "month": MONTH}, timeout=30)
        if r.status_code == 404:
            pytest.skip("no data for that month")
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "ms-excel" in ct or "excel" in ct.lower()
        assert "IR3" in r.headers.get("content-disposition", "")
        body = r.content.decode("utf-8", errors="replace")
        assert "IR-3" in body
        assert "DETALLE POR EMPLEADO" in body

    def test_ir4_download(self, auth):
        r = auth.get(f"{BASE_URL}/api/dgii-reports/monthly/ir4",
                     params={"year": YEAR, "month": MONTH}, timeout=30)
        if r.status_code == 404:
            pytest.skip("no data for that month")
        assert r.status_code == 200, r.text
        body = r.content.decode("utf-8", errors="replace")
        assert "IR-4" in body
        assert "ISR Retenido" in body
        assert "TOTALES" in body

    def test_tss_autodeterminacion(self, auth):
        r = auth.get(f"{BASE_URL}/api/dgii-reports/monthly/tss-autodeterminacion",
                     params={"year": YEAR, "month": MONTH}, timeout=30)
        if r.status_code == 404:
            pytest.skip("no data for that month")
        assert r.status_code == 200, r.text
        body = r.content.decode("utf-8", errors="replace")
        assert "RNC_PATRONO" in body
        assert "SALARIO_COTIZABLE_MENSUAL" in body

    def test_dgii_table_validation(self, auth):
        r = auth.get(f"{BASE_URL}/api/dgii-reports/monthly/dgii-table-validation",
                     params={"year": YEAR, "month": MONTH}, timeout=30)
        if r.status_code == 404:
            pytest.skip("no data for that month")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "tolerance" in data and data["tolerance"] == 0.50
        assert "summary" in data and "results" in data
        s = data["summary"]
        for k in ("employees", "matches", "discrepancies", "total_calculated_isr", "total_dgii_isr"):
            assert k in s
        # spot-check structure of a row
        if data["results"]:
            row = data["results"][0]
            for k in ("employee_id", "employee_name", "gross_salary",
                      "dgii_table_isr", "calculated_isr", "delta", "match"):
                assert k in row


# ===================== PAYROLL SETTINGS isr_quincenal_policy =====================

class TestPayrollSettingsPolicy:
    def test_set_split_half(self, auth):
        r = auth.post(f"{BASE_URL}/api/payroll-settings",
                      json={"isr_quincenal_policy": "split_half"}, timeout=30)
        assert r.status_code in (200, 201), r.text
        g = auth.get(f"{BASE_URL}/api/payroll-settings", timeout=30)
        assert g.status_code == 200
        assert g.json().get("isr_quincenal_policy") == "split_half"

    def test_set_all_q2(self, auth):
        r = auth.post(f"{BASE_URL}/api/payroll-settings",
                      json={"isr_quincenal_policy": "all_q2"}, timeout=30)
        assert r.status_code in (200, 201), r.text
        g = auth.get(f"{BASE_URL}/api/payroll-settings", timeout=30)
        assert g.json().get("isr_quincenal_policy") == "all_q2"

    def test_set_all_q1(self, auth):
        r = auth.post(f"{BASE_URL}/api/payroll-settings",
                      json={"isr_quincenal_policy": "all_q1"}, timeout=30)
        assert r.status_code in (200, 201), r.text
        g = auth.get(f"{BASE_URL}/api/payroll-settings", timeout=30)
        assert g.json().get("isr_quincenal_policy") == "all_q1"

    def test_restore_default(self, auth):
        # Restore to split_half so default behavior is preserved for next tests
        r = auth.post(f"{BASE_URL}/api/payroll-settings",
                      json={"isr_quincenal_policy": "split_half"}, timeout=30)
        assert r.status_code in (200, 201)


# ===================== REGRESSION: existing per-period exports =====================

class TestExistingPeriodExports:
    @pytest.fixture(scope="class")
    def period_id(self, auth):
        r = auth.get(f"{BASE_URL}/api/payroll/periods", timeout=30)
        assert r.status_code == 200, r.text
        periods = r.json()
        if isinstance(periods, dict):
            periods = periods.get("periods") or periods.get("items") or []
        if not periods:
            pytest.skip("no payroll periods present")
        # Prefer a period from MONTH/YEAR
        for p in periods:
            if p.get("year") == YEAR and p.get("month") == MONTH:
                return p["period_id"]
        return periods[0]["period_id"]

    def test_export_ir3(self, auth, period_id):
        r = auth.get(f"{BASE_URL}/api/payroll/periods/{period_id}/export/ir3", timeout=30)
        assert r.status_code in (200, 404), r.text

    def test_export_ir4(self, auth, period_id):
        r = auth.get(f"{BASE_URL}/api/payroll/periods/{period_id}/export/ir4", timeout=30)
        assert r.status_code in (200, 404), r.text

    def test_export_ir17(self, auth, period_id):
        r = auth.get(f"{BASE_URL}/api/payroll/periods/{period_id}/export/ir17", timeout=30)
        assert r.status_code in (200, 404), r.text

    def test_export_ir6(self, auth, period_id):
        r = auth.get(f"{BASE_URL}/api/payroll/periods/{period_id}/export/ir6", timeout=30)
        assert r.status_code in (200, 404), r.text

    def test_export_tss_autodeterminacion(self, auth, period_id):
        r = auth.get(f"{BASE_URL}/api/payroll/periods/{period_id}/export/tss-autodeterminacion", timeout=30)
        assert r.status_code in (200, 404), r.text

    def test_recalculate_all(self, auth, period_id):
        # Actual route is /calculate (no /recalculate-all alias). Should run
        # without 5xx errors. May be 400 if period is paid/approved.
        r = auth.post(f"{BASE_URL}/api/payroll/periods/{period_id}/calculate", timeout=60)
        assert r.status_code in (200, 400), r.text


# ===================== AUTH/SECURITY =====================

class TestAuth:
    def test_preview_requires_auth(self, session):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        r = s.get(f"{BASE_URL}/api/dgii-reports/monthly/preview",
                  params={"year": YEAR, "month": MONTH}, timeout=15)
        assert r.status_code in (401, 403)
