"""
Backend tests for the Executive PDF export of the fiscal comparison.
Endpoint: POST /api/multi-country-reports/cost-comparison-pdf

Validates:
- 200 + application/pdf media type for valid inputs
- PDF magic bytes (%PDF-) and reasonable size
- Content-Disposition filename starts with AnalisisFiscalComparativo
- Validation errors (gross<=0, empty countries, >10 countries)
- Graceful handling of unsupported countries (mixed and all-invalid)
- Single country, max 10 countries
- With and without display_currency

Reuses test user: test_refactor@fortexa.com / test123
"""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
EMAIL = "test_refactor@fortexa.com"
PASSWORD = "test123"

ENDPOINT = f"{BASE_URL}/api/multi-country-reports/cost-comparison-pdf"


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


def _assert_valid_pdf(resp, min_size=4000):
    assert resp.status_code == 200, resp.text[:300]
    ctype = resp.headers.get("content-type", "")
    assert "application/pdf" in ctype, f"Expected pdf, got {ctype}"
    content = resp.content
    assert content.startswith(b"%PDF-"), f"PDF magic bytes missing, got {content[:8]!r}"
    assert len(content) > min_size, f"PDF too small: {len(content)} bytes"
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" in cd.lower(), f"Missing attachment in CD: {cd}"
    assert "AnalisisFiscalComparativo" in cd, f"Filename prefix missing: {cd}"
    return content


# -------------------- Happy Path --------------------

class TestPDFGeneration:
    def test_5_countries_with_display_usd(self, client):
        r = _post(client, {
            "gross_monthly": 3000,
            "countries": ["DO", "CO", "MX", "US", "ES"],
            "display_currency": "USD",
        })
        _assert_valid_pdf(r)

    def test_5_countries_no_display_currency(self, client):
        """Without display_currency: no FX conversion, but PDF still produced."""
        r = _post(client, {
            "gross_monthly": 3000,
            "countries": ["DO", "CO", "MX", "US", "ES"],
        })
        _assert_valid_pdf(r)

    def test_single_country(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["DO"]})
        _assert_valid_pdf(r)

    def test_max_10_countries(self, client):
        ten = ["DO", "CO", "MX", "US", "ES", "AR", "PE", "BR", "CL", "EC"]
        assert len(ten) == 10
        r = _post(client, {"gross_monthly": 3000, "countries": ten})
        _assert_valid_pdf(r)


# -------------------- Validation --------------------

class TestPDFValidation:
    def test_gross_zero_returns_400(self, client):
        r = _post(client, {"gross_monthly": 0, "countries": ["DO"]})
        assert r.status_code == 400, r.text
        body = r.json()
        assert "detail" in body

    def test_gross_negative_returns_400(self, client):
        r = _post(client, {"gross_monthly": -500, "countries": ["DO"]})
        assert r.status_code == 400, r.text

    def test_empty_countries_returns_400(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": []})
        assert r.status_code in (400, 422), r.text

    def test_more_than_10_countries_returns_400(self, client):
        eleven = ["DO", "CO", "MX", "US", "ES", "AR", "PE", "BR", "CL", "EC", "GT"]
        assert len(eleven) == 11
        r = _post(client, {"gross_monthly": 3000, "countries": eleven})
        assert r.status_code == 400, r.text


# -------------------- Resilience: invalid countries --------------------

class TestPDFInvalidCountries:
    def test_mixed_invalid_and_valid_still_produces_pdf(self, client):
        """ZZZ is unsupported but DO is valid — PDF should still generate."""
        r = _post(client, {"gross_monthly": 3000, "countries": ["ZZZ", "DO"]})
        _assert_valid_pdf(r)

    def test_all_unsupported_returns_400(self, client):
        r = _post(client, {"gross_monthly": 3000, "countries": ["ZZZ", "AAA"]})
        assert r.status_code == 400, r.text
        body = r.json()
        assert "detail" in body
        assert "Ningún país válido" in body["detail"] or "valido" in body["detail"].lower()


# -------------------- Auth --------------------

class TestPDFAuth:
    def test_no_auth_returns_401_or_403(self):
        r = requests.post(ENDPOINT,
                          json={"gross_monthly": 3000, "countries": ["DO"]},
                          timeout=30)
        assert r.status_code in (401, 403), r.text
