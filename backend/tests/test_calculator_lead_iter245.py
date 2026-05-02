"""iter245 — public payroll calculator lead capture + PDF endpoint tests."""
import os
import requests
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://company-config-debug.preview.emergentagent.com").rstrip("/")
LEAD_URL = f"{BASE_URL}/api/payroll/calculator/lead"
PDF_URL = f"{BASE_URL}/api/payroll/calculator/pdf"


def _payload(email=None, country="DO", gross=50000.0):
    return {
        "email": email or f"test_iter245_{uuid.uuid4().hex[:8]}@fortexa.com",
        "full_name": "Test User",
        "country": country,
        "gross_monthly": gross,
        "consent_marketing": True,
    }


def test_lead_public_no_auth_success():
    r = requests.post(LEAD_URL, json=_payload(), timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    assert "lead_id" in data and isinstance(data["lead_id"], str)
    assert "calculations_count" in data and data["calculations_count"] >= 1
    assert "net_monthly" in data
    # DR known answer for 50000 gross
    assert abs(data["net_monthly"] - 44747.75) < 0.01, f"expected 44747.75 got {data['net_monthly']}"
    assert "message" in data


def test_lead_idempotent_increments_count():
    email = f"test_iter245_dup_{uuid.uuid4().hex[:8]}@fortexa.com"
    r1 = requests.post(LEAD_URL, json=_payload(email=email), timeout=20)
    assert r1.status_code == 200
    c1 = r1.json()["calculations_count"]
    lead_id1 = r1.json()["lead_id"]
    r2 = requests.post(LEAD_URL, json=_payload(email=email), timeout=20)
    assert r2.status_code == 200
    c2 = r2.json()["calculations_count"]
    lead_id2 = r2.json()["lead_id"]
    assert c2 == c1 + 1, f"counter did not increment {c1}->{c2}"
    assert lead_id1 == lead_id2, "lead_id should remain stable on upsert"


def test_lead_invalid_email_returns_422():
    r = requests.post(LEAD_URL, json={**_payload(), "email": "not-an-email"}, timeout=20)
    assert r.status_code == 422, r.text


def test_lead_invalid_country_returns_400():
    r = requests.post(LEAD_URL, json=_payload(country="ZZ"), timeout=20)
    assert r.status_code == 400, r.text


def test_pdf_zero_gross_returns_422():
    r = requests.post(PDF_URL, json=_payload(gross=0), timeout=20)
    assert r.status_code == 422, r.text


def test_pdf_returns_binary():
    r = requests.post(PDF_URL, json=_payload(), timeout=30)
    assert r.status_code == 200, r.text[:300]
    assert r.headers.get("content-type", "").startswith("application/pdf")
    cd = r.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "FortexaRH_Nomina_DO_" in cd
    assert len(r.content) > 2048, f"PDF too small: {len(r.content)} bytes"
    assert r.content[:5] == b"%PDF-", "Response is not a valid PDF"


def test_payroll_calculator_countries_still_public():
    r = requests.get(f"{BASE_URL}/api/payroll/calculator/countries", timeout=20)
    assert r.status_code == 200
    data = r.json()
    # countries either returned as list or as dict with 'countries' key
    countries = data if isinstance(data, list) else data.get("countries", [])
    assert len(countries) >= 1
