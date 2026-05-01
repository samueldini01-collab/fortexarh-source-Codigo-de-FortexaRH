"""
Backend regression tests for the new FortexaRH Fiscal Comparison Calculator.
File under test: /app/backend/routes/multi_country_reports.py (cost-comparison endpoint)

Endpoint: POST /api/multi-country-reports/cost-comparison
Body: { gross_monthly: float, countries: [str], include_employee?: bool, include_employer?: bool }

User: test_refactor@fortexa.com / test123

The endpoint is stateless (no DB writes / no period required) — pure compute.
"""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
EMAIL = "test_refactor@fortexa.com"
PASSWORD = "test123"

ENDPOINT = f"{BASE_URL}/api/multi-country-reports/cost-comparison"

# Tolerance per request (rounding)
TOL = 1.0


# -------------------- Fixtures --------------------

@pytest.fixture(scope="module")
def auth_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": EMAIL, "password": PASSWORD},
                      timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Auth failed: {r.status_code} {r.text}")
    tok = r.json().get("access_token") or r.json().get("token")
    if not tok:
        pytest.skip("No token returned")
    return tok


@pytest.fixture(scope="module")
def client(auth_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {auth_token}"})
    return s


def _post(client, payload):
    return client.post(ENDPOINT, json=payload, timeout=60)


# -------------------- Core: 5 countries multi-comparison --------------------

class TestMultiCountryComparison:
    """Validates the headline scenario: 5 countries comparison, sorted ascending."""

    def test_5_countries_response_shape(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["DO", "CO", "MX", "US", "ES"]})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["gross_monthly"] == 3000
        assert body["countries_compared"] == 5
        assert body["unsupported_countries"] == []
        assert isinstance(body["results"], list)
        assert len(body["results"]) == 5

    def test_results_sorted_by_total_cost_ascending(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["DO", "CO", "MX", "US", "ES"]})
        assert r.status_code == 200
        results = r.json()["results"]
        costs = [c["employer"]["total_cost_to_company"] for c in results]
        assert costs == sorted(costs), f"Not ascending: {costs}"

    def test_each_country_object_keys(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["DO", "CO", "MX", "US", "ES"]})
        assert r.status_code == 200
        results = r.json()["results"]
        required_top = {
            "country_code", "country_name", "flag", "currency", "currency_symbol",
            "region", "agency", "social_security_system", "gross_salary",
            "employee", "employer",
        }
        emp_keys = {"breakdown", "total_ss", "isr", "total_deductions",
                    "net_salary", "effective_tax_rate_pct"}
        er_keys = {"breakdown", "total_contributions", "total_cost_to_company",
                   "cost_overhead_pct"}
        for c in results:
            assert required_top.issubset(c.keys()), f"missing: {required_top - c.keys()} in {c.get('country_code')}"
            assert emp_keys.issubset(c["employee"].keys())
            assert er_keys.issubset(c["employer"].keys())
            # breakdown items shape
            for item in c["employee"]["breakdown"] + c["employer"]["breakdown"]:
                assert {"code", "name", "rate", "rate_pct", "amount"}.issubset(item.keys())


# -------------------- Country-specific numerical assertions --------------------

class TestCountryNumbers:
    """Per-country expected values for gross=3000."""

    @pytest.fixture(scope="class")
    def big5(self, client):
        r = _post(client, {"gross_monthly": 3000,
                            "countries": ["DO", "CO", "MX", "US", "ES"]})
        assert r.status_code == 200, r.text
        return {c["country_code"]: c for c in r.json()["results"]}

    def test_US_3000(self, big5):
        us = big5["US"]
        assert us["currency"] == "USD"
        # Employee SS: 6.2% + 1.45% = 229.5
        assert abs(us["employee"]["total_ss"] - 229.5) <= TOL
        # ISR ~ 340.67 (federal IRS bracket)
        assert abs(us["employee"]["isr"] - 340.67) <= 5.0  # bracket-based, ±5 tolerance
        # Net ~ 2429.83 (give wider tolerance because of ISR)
        assert abs(us["employee"]["net_salary"] - 2429.83) <= 5.0
        # Employer 6.2% + 1.45% + 0.6%(FUTA cap) ~ 247.50 (or 229.5 if no FUTA / capped)
        # Per request: ~247.50 employer, 8.25% overhead
        assert abs(us["employer"]["total_contributions"] - 247.5) <= 25.0
        assert abs(us["employer"]["cost_overhead_pct"] - 8.25) <= 1.0

    def test_DR_3000(self, big5):
        do = big5["DO"]
        assert do["currency"] == "DOP"
        # SFS 3.04% = 91.20, AFP 2.87% = 86.10 -> total 177.30
        assert abs(do["employee"]["total_ss"] - 177.30) <= TOL
        # ISR = 0 (3000 DOP/m way below exempt 34685/m)
        assert do["employee"]["isr"] == 0
        # Net = 2822.70
        assert abs(do["employee"]["net_salary"] - 2822.70) <= TOL
        # Employer ~ 485.70 (7.09% SFS + 7.10% AFP + 1.10% SRL + 1% INFOTEP = ~16.19%)
        assert abs(do["employer"]["total_contributions"] - 485.70) <= 5.0
        assert abs(do["employer"]["cost_overhead_pct"] - 16.19) <= 0.5

    def test_CO_3000(self, big5):
        co = big5["CO"]
        assert co["currency"] == "COP"
        # Employee 4% SALUD + 4% PENSION = 240
        assert abs(co["employee"]["total_ss"] - 240.0) <= TOL
        # ISR = 0 (3000 COP is way below CO's exempt threshold which is in millions)
        assert co["employee"]["isr"] == 0
        # Net 2760
        assert abs(co["employee"]["net_salary"] - 2760.0) <= TOL
        # Employer 30.02% of 3000 = 900.6 (SALUD 8.5 + PENSION 12 + ARL 0.522 + CCF 4 + ICBF 3 + SENA 2)
        assert abs(co["employer"]["total_contributions"] - 900.66) <= 5.0
        assert abs(co["employer"]["cost_overhead_pct"] - 30.02) <= 0.5

    def test_MX_present_and_consistent(self, big5):
        mx = big5["MX"]
        assert mx["country_code"] == "MX"
        assert mx["currency"] == "MXN"
        # gross + employer == total cost
        assert abs(mx["employer"]["total_cost_to_company"]
                   - (mx["gross_salary"] + mx["employer"]["total_contributions"])) <= 0.5
        # net = gross - total_deductions
        assert abs(mx["employee"]["net_salary"]
                   - (mx["gross_salary"] - mx["employee"]["total_deductions"])) <= 0.5

    def test_ES_present_and_consistent(self, big5):
        es = big5["ES"]
        assert es["country_code"] == "ES"
        assert es["currency"] == "EUR"
        assert abs(es["employer"]["total_cost_to_company"]
                   - (es["gross_salary"] + es["employer"]["total_contributions"])) <= 0.5
        assert abs(es["employee"]["net_salary"]
                   - (es["gross_salary"] - es["employee"]["total_deductions"])) <= 0.5


# -------------------- Validation tests --------------------

class TestValidation:
    def test_gross_zero_returns_400(self, client):
        r = _post(client, {"gross_monthly": 0, "countries": ["DO"]})
        assert r.status_code == 400, r.text

    def test_gross_negative_returns_400(self, client):
        r = _post(client, {"gross_monthly": -100, "countries": ["DO"]})
        assert r.status_code == 400, r.text

    def test_empty_countries_returns_400(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": []})
        # Could be 400 or 422 depending on validator; spec says 400
        assert r.status_code in (400, 422), r.text

    def test_more_than_10_countries_returns_400(self, client):
        many = ["DO", "CO", "MX", "US", "ES", "AR", "PE", "BR", "CL", "EC", "GT"]
        assert len(many) == 11
        r = _post(client, {"gross_monthly": 3000, "countries": many})
        assert r.status_code == 400, r.text

    def test_invalid_country_goes_to_unsupported_not_500(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["ZZZZ", "DO"]})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "ZZZZ" in body["unsupported_countries"]
        # DO still computed
        assert any(c["country_code"] == "DO" for c in body["results"])
        assert body["countries_compared"] == 1


# -------------------- Include flags --------------------

class TestIncludeFlags:
    def test_include_employee_false_excludes_employee_object(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["DO", "US"],
                            "include_employee": False, "include_employer": True})
        assert r.status_code == 200
        for c in r.json()["results"]:
            assert "employee" not in c
            assert "employer" in c

    def test_include_employer_false_excludes_employer_object(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["DO", "US"],
                            "include_employee": True, "include_employer": False})
        assert r.status_code == 200
        for c in r.json()["results"]:
            assert "employer" not in c
            assert "employee" in c

    def test_both_flags_true_default(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["DO"]})
        assert r.status_code == 200
        c = r.json()["results"][0]
        assert "employee" in c and "employer" in c


# -------------------- Auth --------------------

class TestAuth:
    def test_no_auth_returns_401(self):
        r = requests.post(ENDPOINT,
                          json={"gross_monthly": 3000, "countries": ["DO"]},
                          timeout=30)
        assert r.status_code in (401, 403), r.text
