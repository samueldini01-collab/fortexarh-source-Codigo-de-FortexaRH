"""
iter246 — Multi-country payroll-calculator + country-config/company tests.

Validates:
- /api/payroll-calculator response now contains breakdown.country_code,
  country_name, currency, currency_symbol, flag, labels{...}, rates_applied{...}.
- DR math unchanged: net_salary == 44747.75 for base=50000 days=30.
- /api/country-config/company returns {country_code, profile, overrides, company_name}.
- DR company rates come from DR profile (sanity check that backend uses
  COUNTRY_PROFILES[country_code], not blindly DR constants).
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASS = "test123"


@pytest.fixture(scope="module")
def admin_token():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token") or r.json().get("token")
    if not tok:
        pytest.skip(f"No token in login response: {r.json()}")
    return tok


@pytest.fixture
def auth_client(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return s


# ======================= /api/country-config/company =======================
class TestCountryConfigCompany:
    def test_company_country_config_shape(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/country-config/company", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        # Required keys for the PayrollConfigPage banner.
        for k in ("country_code", "profile", "overrides", "company_name"):
            assert k in data, f"missing key: {k}"
        assert isinstance(data["country_code"], str) and len(data["country_code"]) == 2
        assert isinstance(data["profile"], dict)
        # Profile must expose currency + name for the banner.
        assert "currency" in data["profile"]
        assert "name" in data["profile"]

    def test_dr_admin_country_is_DO(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/country-config/company", timeout=20)
        assert r.status_code == 200
        assert r.json()["country_code"] == "DO"


# ======================= /api/payroll-calculator =======================
class TestPayrollCalculatorMultiCountry:
    PAYLOAD = {
        "employee_name": "Juan",
        "base_salary": 50000,
        "days_worked": 30,
        "hours_extra": 0,
        "hour_rate": 0,
        "bonuses": 0,
        "commissions": 0,
        "loan_deduction": 0,
        "other_deductions": 0,
    }

    def test_dr_net_salary_unchanged(self, auth_client):
        """REGRESSION GUARD: DR known answer must remain exactly 44747.75."""
        r = auth_client.post(f"{BASE_URL}/api/payroll-calculator", json=self.PAYLOAD, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["net_salary"] == 44747.75, f"DR math broke! net_salary={d['net_salary']}"

    def test_breakdown_country_metadata(self, auth_client):
        r = auth_client.post(f"{BASE_URL}/api/payroll-calculator", json=self.PAYLOAD, timeout=20)
        assert r.status_code == 200
        b = r.json().get("breakdown", {})
        for k in ("country_code", "country_name", "currency", "currency_symbol", "flag", "labels", "rates_applied"):
            assert k in b, f"breakdown missing {k}"
        assert b["country_code"] == "DO"
        assert b["currency"] == "DOP"
        assert b["currency_symbol"] in ("RD$", "DOP")

    def test_breakdown_labels_keys(self, auth_client):
        r = auth_client.post(f"{BASE_URL}/api/payroll-calculator", json=self.PAYLOAD, timeout=20)
        labels = r.json()["breakdown"]["labels"]
        for k in ("sfs_employee", "afp_employee", "sfs_employer", "afp_employer", "srl_employer", "infotep_employer", "isr_agency"):
            assert k in labels, f"labels missing {k}"
            assert isinstance(labels[k], str) and labels[k]

    def test_breakdown_rates_applied_keys(self, auth_client):
        r = auth_client.post(f"{BASE_URL}/api/payroll-calculator", json=self.PAYLOAD, timeout=20)
        rates = r.json()["breakdown"]["rates_applied"]
        for k in ("sfs_employee", "afp_employee", "sfs_employer", "afp_employer", "srl_employer", "infotep_employer"):
            assert k in rates, f"rates_applied missing {k}"
            assert isinstance(rates[k], (int, float))
        # DR canonical rates sanity (rates are stored as decimals, e.g. 0.0304).
        assert 0.02 < rates["sfs_employee"] < 0.05
        assert 0.02 < rates["afp_employee"] < 0.05

    def test_dr_isr_agency_label(self, auth_client):
        r = auth_client.post(f"{BASE_URL}/api/payroll-calculator", json=self.PAYLOAD, timeout=20)
        assert r.json()["breakdown"]["labels"]["isr_agency"] == "DGII"


# ======================= public /api/country-config/countries =======================
class TestCountryListPublic:
    def test_countries_endpoint_open(self):
        r = requests.get(f"{BASE_URL}/api/country-config/countries", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        # Endpoint returns {regions: {region_key: {countries: [...]}}, total: N}.
        # Total must be >= 20 to support the public dropdown SVG-flag rendering.
        assert isinstance(data, dict)
        assert "regions" in data and "total" in data
        assert data["total"] >= 20, f"expected >=20 countries, got {data['total']}"
        # Flatten and verify codes used by CountryFlag/<svg data-testid='flag-XX'/> are present.
        codes = []
        for region in data["regions"].values():
            for c in region.get("countries", []):
                codes.append(c.get("code"))
        assert "DO" in codes and "US" in codes
