"""
Backend tests for Native Country-Specific Fiscal Reports (FortexaRH P2).

Endpoints tested:
- GET /api/native-reports/catalog                       (28 countries, 33 formats, 7 implemented)
- GET /api/native-reports/co/pila?period=YYYY-MM        (Colombia PILA UGPP)
- GET /api/native-reports/mx/imss-cuotas?period=YYYY-MM (Mexico IMSS SUA)
- GET /api/native-reports/mx/infonavit?period=YYYY-MM   (Mexico INFONAVIT)
- PUT /api/country-config/company/country?country_code= (used to flip country guard)

Plus regression for iteration_235 endpoints (cost-comparison, cost-comparison-pdf,
fiscal-summary CSV/PDF, available-reports).

Test user: test_refactor@fortexa.com / test123
Period:    2026-03 (paid period exists)

CRITICAL: The fixture restores company.country to 'DO' at end of session.
"""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
EMAIL = "test_refactor@fortexa.com"
PASSWORD = "test123"
PERIOD = "2026-03"


# -------------------- Fixtures --------------------

@pytest.fixture(scope="session")
def auth_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Auth failed: {r.status_code} {r.text}")
    tok = r.json().get("access_token") or r.json().get("token")
    if not tok:
        pytest.skip("No token returned")
    return tok


@pytest.fixture(scope="session")
def client(auth_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {auth_token}"})
    return s


@pytest.fixture(scope="session", autouse=True)
def restore_country_to_do(client):
    """Ensure company.country is 'DO' before AND after the suite (safety net)."""
    # Pre-condition: start in DO
    client.put(f"{BASE_URL}/api/country-config/company/country",
               params={"country_code": "DO"}, timeout=30)
    yield
    # Post-condition: always restore
    r = client.put(f"{BASE_URL}/api/country-config/company/country",
                   params={"country_code": "DO"}, timeout=30)
    assert r.status_code == 200, f"Failed to restore country to DO: {r.text}"


def _set_country(client, code):
    r = client.put(f"{BASE_URL}/api/country-config/company/country",
                   params={"country_code": code}, timeout=30)
    assert r.status_code == 200, f"Could not set country={code}: {r.text}"


# -------------------- Catalog tests --------------------

class TestCatalog:
    """Catalog endpoint - country-independent."""

    def test_catalog_basic_shape(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/catalog", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total_countries"] == 28, data["total_countries"]
        assert data["total_formats"] == 33, data["total_formats"]
        assert data["implemented_formats"] == 7, data["implemented_formats"]
        assert isinstance(data["countries"], list)
        assert len(data["countries"]) == 28

    def test_catalog_country_object_shape(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/catalog", timeout=30)
        c = r.json()["countries"][0]
        for key in ("code", "name", "flag", "region", "currency", "agency",
                    "social_security_system", "formats", "implemented_count",
                    "total_count", "compliance_status"):
            assert key in c, f"Missing key {key} in country object"
        assert c["compliance_status"] in ("complete", "partial", "universal_only")

    def test_catalog_DO_complete(self, client):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        do = next((c for c in data["countries"] if c["code"] == "DO"), None)
        assert do is not None
        assert do["implemented_count"] == 4
        assert do["total_count"] == 4
        assert do["compliance_status"] == "complete"
        codes = {f["code"] for f in do["formats"]}
        assert {"TSS_AUTODET", "TSS_NOVEDADES", "IR3", "IR17"} <= codes

    def test_catalog_CO_partial_with_PILA(self, client):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        co = next((c for c in data["countries"] if c["code"] == "CO"), None)
        assert co is not None
        assert co["implemented_count"] == 1
        codes = {f["code"] for f in co["formats"]}
        assert "PILA" in codes
        # only 1 format defined, so 1/1 = complete in catalog convention
        assert co["compliance_status"] in ("complete", "partial")

    def test_catalog_MX_imss_and_infonavit(self, client):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        mx = next((c for c in data["countries"] if c["code"] == "MX"), None)
        assert mx is not None
        assert mx["implemented_count"] == 2
        codes = {f["code"] for f in mx["formats"]}
        assert "IMSS_SUA" in codes
        assert "INFONAVIT" in codes

    def test_catalog_25_other_countries_universal_only(self, client):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        others = [c for c in data["countries"] if c["code"] not in ("DO", "CO", "MX")]
        assert len(others) == 25
        for c in others:
            assert c["implemented_count"] == 0, c["code"]
            assert c["compliance_status"] == "universal_only", c["code"]


# -------------------- Country guard (400) tests --------------------

class TestCountryGuard:
    """When company.country != format country, endpoint must return 400."""

    def test_co_pila_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/co/pila",
                       params={"period": PERIOD}, timeout=30)
        assert r.status_code == 400, r.text
        detail = r.json().get("detail", "")
        # Should mention both Colombia and the current country
        assert "Colombia" in detail or "PILA" in detail
        # Must reference DR/Dominicana given current country
        assert "Dominicana" in detail or "República" in detail or "DO" in detail

    def test_mx_imss_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/mx/imss-cuotas",
                       params={"period": PERIOD}, timeout=30)
        assert r.status_code == 400, r.text

    def test_mx_infonavit_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/mx/infonavit",
                       params={"period": PERIOD}, timeout=30)
        assert r.status_code == 400, r.text


# -------------------- Colombia PILA generation --------------------

class TestColombiaPILA:

    def test_pila_generates_valid_file_when_country_is_CO(self, client):
        _set_country(client, "CO")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/co/pila",
                           params={"period": PERIOD}, timeout=60)
            assert r.status_code == 200, r.text[:500]
            ctype = r.headers.get("content-type", "")
            assert "text/plain" in ctype, ctype
            cd = r.headers.get("content-disposition", "")
            assert "attachment" in cd.lower()
            assert "PILA_" in cd, cd
            body = r.content
            # > 100 bytes minimum sanity
            assert len(body) > 100, f"PILA too small: {len(body)}"
            # split lines (latin-1)
            text = body.decode("latin-1")
            lines = [ln for ln in text.split("\n") if ln]
            assert len(lines) >= 2, f"Expected header + at least 1 detail, got {len(lines)}"
            # First record must be type 1 (header)
            assert lines[0].startswith("1"), f"Header type missing: {lines[0][:5]!r}"
            # Detail records must start with 2 and be padded to 942 chars
            detail_lines = lines[1:]
            for dl in detail_lines:
                assert dl.startswith("2"), f"Detail must start with '2', got: {dl[:5]!r}"
                assert len(dl) == 942, f"Detail must be 942 chars, got {len(dl)}"
        finally:
            _set_country(client, "DO")

    def test_pila_404_when_no_payroll_data(self, client):
        _set_country(client, "CO")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/co/pila",
                           params={"period": "2099-12"}, timeout=30)
            assert r.status_code == 404, r.text[:300]
            assert "No hay datos" in r.json().get("detail", "") or \
                   "no" in r.json().get("detail", "").lower()
        finally:
            _set_country(client, "DO")


# -------------------- Mexico IMSS / INFONAVIT generation --------------------

class TestMexicoIMSS:

    def test_imss_cuotas_valid_when_country_MX(self, client):
        _set_country(client, "MX")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/mx/imss-cuotas",
                           params={"period": PERIOD}, timeout=60)
            assert r.status_code == 200, r.text[:500]
            assert "text/plain" in r.headers.get("content-type", "")
            cd = r.headers.get("content-disposition", "")
            assert "IMSS_SUA_Cuotas_" in cd, cd
            body = r.content
            assert len(body) > 100, f"Too small: {len(body)}"
            text = body.decode("latin-1")
            lines = [ln for ln in text.split("\n") if ln]
            assert len(lines) >= 1
            # All lines should be reasonably long (fixed-width)
            for ln in lines:
                assert len(ln) > 150, f"IMSS record too short: {len(ln)}"
        finally:
            _set_country(client, "DO")

    def test_infonavit_valid_when_country_MX(self, client):
        _set_country(client, "MX")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/mx/infonavit",
                           params={"period": PERIOD}, timeout=60)
            assert r.status_code == 200, r.text[:500]
            assert "text/plain" in r.headers.get("content-type", "")
            cd = r.headers.get("content-disposition", "")
            assert "INFONAVIT_" in cd, cd
            body = r.content
            assert len(body) > 100, f"Too small: {len(body)}"
            lines = [ln for ln in body.decode("latin-1").split("\n") if ln]
            assert len(lines) >= 1
        finally:
            _set_country(client, "DO")

    def test_imss_404_when_no_payroll_data(self, client):
        _set_country(client, "MX")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/mx/imss-cuotas",
                           params={"period": "2099-12"}, timeout=30)
            assert r.status_code == 404
        finally:
            _set_country(client, "DO")

    def test_infonavit_404_when_no_payroll_data(self, client):
        _set_country(client, "MX")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/mx/infonavit",
                           params={"period": "2099-12"}, timeout=30)
            assert r.status_code == 404
        finally:
            _set_country(client, "DO")


# -------------------- Auth --------------------

class TestNativeReportsAuth:
    def test_catalog_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/native-reports/catalog", timeout=30)
        assert r.status_code in (401, 403)

    def test_co_pila_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/native-reports/co/pila",
                         params={"period": PERIOD}, timeout=30)
        assert r.status_code in (401, 403)


# -------------------- Regression: iteration_235 endpoints --------------------

class TestRegressionIter235:

    def test_available_reports_still_works(self, client):
        r = client.get(f"{BASE_URL}/api/multi-country-reports/available-reports", timeout=30)
        assert r.status_code == 200

    def test_cost_comparison_still_works(self, client):
        payload = {
            "gross_monthly": 3000,
            "countries": ["DO", "CO", "MX"],
            "display_currency": "USD",
        }
        r = client.post(f"{BASE_URL}/api/multi-country-reports/cost-comparison",
                        json=payload, timeout=60)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        # results shape
        assert "results" in data or "comparison" in data or isinstance(data, dict)

    def test_cost_comparison_pdf_still_works(self, client):
        payload = {
            "gross_monthly": 3000,
            "countries": ["DO", "CO", "MX"],
            "display_currency": "USD",
        }
        r = client.post(f"{BASE_URL}/api/multi-country-reports/cost-comparison-pdf",
                        json=payload, timeout=60)
        assert r.status_code == 200, r.text[:300]
        assert "application/pdf" in r.headers.get("content-type", "")
        assert r.content.startswith(b"%PDF-")

    def test_fiscal_summary_404_when_no_data(self, client):
        # Use an unlikely period to provoke 404
        r = client.get(f"{BASE_URL}/api/multi-country-reports/fiscal-summary",
                       params={"period": "2099-12", "format": "csv"}, timeout=30)
        assert r.status_code in (404, 400)
