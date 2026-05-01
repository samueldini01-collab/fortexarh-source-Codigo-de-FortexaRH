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


# -------------------- FX Conversion (NEW) --------------------

class TestFXConversion:
    """Validates the FX conversion enhancement (display_currency)."""

    def test_no_display_currency_no_converted_field(self, client):
        """Backwards compat: omitting display_currency should keep response identical to legacy."""
        r = _post(client, {"gross_monthly": 3000, "countries": ["DO", "US"]})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("fx") is None
        for c in body["results"]:
            assert "converted" not in c, f"unexpected converted field on {c['country_code']}"

    def test_display_currency_usd_adds_converted_and_fx(self, client):
        r = _post(client, {"gross_monthly": 3000,
                            "countries": ["DO", "CO", "MX", "US", "ES"],
                            "display_currency": "USD"})
        assert r.status_code == 200, r.text
        body = r.json()
        # FX object
        fx = body.get("fx")
        if fx is None:
            pytest.skip("FX rates unavailable in this env (no internet egress to open.er-api.com); converted gracefully None — acceptable per spec.")
        assert fx["display_currency"] == "USD"
        assert fx["base"] == "USD"
        assert fx["rate_source"] == "open.er-api.com"
        assert "cached" in fx and isinstance(fx["cached"], bool)

        # Each result has converted with all required keys
        required_conv = {"display_currency", "gross_salary", "total_deductions",
                         "net_salary", "total_contributions", "total_cost_to_company"}
        for c in body["results"]:
            assert "converted" in c, f"missing converted in {c['country_code']}"
            assert required_conv.issubset(c["converted"].keys()), \
                f"{c['country_code']}: missing {required_conv - c['converted'].keys()}"
            assert c["converted"]["display_currency"] == "USD"

    def test_us_no_conversion_when_local_equals_display(self, client):
        """US local currency is USD — converted values should equal local values exactly."""
        r = _post(client, {"gross_monthly": 3000,
                            "countries": ["US"],
                            "display_currency": "USD"})
        assert r.status_code == 200, r.text
        body = r.json()
        if body.get("fx") is None:
            pytest.skip("FX rates unavailable; skipping cross-currency assertions.")
        us = body["results"][0]
        assert us["country_code"] == "US"
        assert abs(us["converted"]["gross_salary"] - us["gross_salary"]) <= 0.01
        assert abs(us["converted"]["total_cost_to_company"] - us["employer"]["total_cost_to_company"]) <= 0.01
        assert abs(us["converted"]["net_salary"] - us["employee"]["net_salary"]) <= 0.01

    def test_eur_conversion_for_us_uses_eur_rate(self, client):
        """US gross 3000 USD → ~2400-2900 EUR (depending on day's rate, expected ~2560)."""
        r = _post(client, {"gross_monthly": 3000,
                            "countries": ["US"],
                            "display_currency": "EUR"})
        assert r.status_code == 200, r.text
        body = r.json()
        if body.get("fx") is None:
            pytest.skip("FX rates unavailable.")
        us = body["results"][0]
        conv_gross = us["converted"]["gross_salary"]
        if conv_gross is None:
            pytest.skip("EUR rate missing in cache — graceful null.")
        # USD->EUR around 0.85-0.96 historically, so 3000 USD -> 2400-2900 EUR
        assert 2300 <= conv_gross <= 3000, f"US 3000 USD -> EUR was {conv_gross}, expected ~2400-2900"

    def test_dop_to_usd_dramatically_lower(self, client):
        """DR gross 3000 DOP -> ~50 USD (DOP is ~60 per USD)."""
        r = _post(client, {"gross_monthly": 3000,
                            "countries": ["DO"],
                            "display_currency": "USD"})
        assert r.status_code == 200, r.text
        body = r.json()
        if body.get("fx") is None:
            pytest.skip("FX rates unavailable.")
        do = body["results"][0]
        conv_gross = do["converted"]["gross_salary"]
        if conv_gross is None:
            pytest.skip("DOP rate missing.")
        # 3000 DOP / ~60 = ~50 USD (range 40-80 to be safe)
        assert 30 <= conv_gross <= 90, f"DO 3000 DOP -> USD was {conv_gross}, expected ~50"

    def test_sort_by_converted_total_cost_when_fx_active(self, client):
        """When FX active, results sorted by converted.total_cost_to_company ascending."""
        r = _post(client, {"gross_monthly": 3000,
                            "countries": ["DO", "CO", "MX", "US", "ES"],
                            "display_currency": "USD"})
        assert r.status_code == 200, r.text
        body = r.json()
        if body.get("fx") is None:
            pytest.skip("FX rates unavailable.")
        results = body["results"]
        # All converted values present?
        all_conv = all(r["converted"]["total_cost_to_company"] is not None for r in results)
        if not all_conv:
            pytest.skip("Some converted values None — can't check sort by converted.")
        costs = [r["converted"]["total_cost_to_company"] for r in results]
        assert costs == sorted(costs), f"Not ascending by converted: {costs}"
        # And specifically: DO (~$58 USD) should come BEFORE US (~$3247 USD)
        codes_in_order = [r["country_code"] for r in results]
        assert codes_in_order.index("DO") < codes_in_order.index("US"), \
            f"Expected DO before US in sort by converted USD, got: {codes_in_order}"

    def test_invalid_display_currency_returns_null_not_500(self, client):
        """display_currency='XYZ' is unknown — converted fields should be null, not 500."""
        r = _post(client, {"gross_monthly": 3000,
                            "countries": ["DO", "US"],
                            "display_currency": "XYZ"})
        assert r.status_code == 200, r.text
        body = r.json()
        # fx info still returned (with display=XYZ) if rates fetched
        if body.get("fx") is None:
            pytest.skip("FX rates unavailable in env.")
        for c in body["results"]:
            assert "converted" in c
            # Each numeric converted field must be null since target is unknown
            assert c["converted"]["gross_salary"] is None
            assert c["converted"].get("total_cost_to_company") is None

    def test_fx_cache_second_call_cached_true(self, client):
        """Second call within TTL should return cached: true."""
        # First call (warms cache)
        r1 = _post(client, {"gross_monthly": 3000, "countries": ["US"], "display_currency": "USD"})
        assert r1.status_code == 200
        if r1.json().get("fx") is None:
            pytest.skip("FX rates unavailable.")
        # Second call (should be cached)
        r2 = _post(client, {"gross_monthly": 3000, "countries": ["US"], "display_currency": "USD"})
        assert r2.status_code == 200
        fx2 = r2.json().get("fx")
        assert fx2 is not None
        assert fx2["cached"] is True, f"Second call should be cached, got fx={fx2}"

    def test_supported_currencies_eur_gbp_jpy(self, client):
        """open.er-api.com supports major currencies — spot check EUR, GBP, JPY."""
        for curr in ["EUR", "GBP", "JPY"]:
            r = _post(client, {"gross_monthly": 3000,
                                "countries": ["US"],
                                "display_currency": curr})
            assert r.status_code == 200, f"{curr}: {r.text}"
            body = r.json()
            if body.get("fx") is None:
                pytest.skip("FX rates unavailable.")
            us = body["results"][0]
            assert us["converted"]["display_currency"] == curr
            # USD->X conversion should not be None for major currencies
            assert us["converted"]["gross_salary"] is not None, f"{curr}: gross conversion was None"
            assert us["converted"]["gross_salary"] > 0
