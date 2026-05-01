"""
Backend regression for the new universal Multi-Country Fiscal Reports module.
File under test: /app/backend/routes/multi_country_reports.py
Routes:
  GET /api/multi-country-reports/available-reports
  GET /api/multi-country-reports/fiscal-summary?period=...&format=csv|pdf

User: test_refactor@fortexa.com / test123
Period: 2026-03 (period_42a51c051530)

CRITICAL: At end of suite, restore company country to DO.
"""
import os
import io
import csv
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
EMAIL = "test_refactor@fortexa.com"
PASSWORD = "test123"
PERIOD = "2026-03"
PERIOD_ID = "period_42a51c051530"


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


def _set_country(client, code):
    r = client.put(
        f"{BASE_URL}/api/country-config/company/country",
        params={"country_code": code},
        timeout=30,
    )
    assert r.status_code == 200, f"Failed to switch country to {code}: {r.status_code} {r.text}"


@pytest.fixture(scope="module", autouse=True)
def restore_country_at_end(client):
    yield
    # CRITICAL: restore DO at the very end
    try:
        _set_country(client, "DO")
    except Exception as e:
        print(f"WARN: failed to restore DO country: {e}")


# -------------------- Helpers --------------------

def _parse_csv(content_bytes):
    text = content_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    return list(reader)


def _find_header_row(rows):
    """Locate the data header row (the one starting with '#')."""
    for r in rows:
        if r and r[0].strip() == "#":
            return r
    return None


# -------------------- /available-reports --------------------

class TestAvailableReports:
    def test_available_reports_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/multi-country-reports/available-reports", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["country_code"] == "DO"
        assert d["currency"] == "DOP"
        assert d["currency_symbol"]
        assert d["agency"]  # DGII
        assert d["social_security_system"]  # TSS
        assert isinstance(d["country_specific_reports"], list)
        ur = d["universal_reports"]
        ids = [u["id"] for u in ur]
        assert "fiscal_summary_csv" in ids
        assert "fiscal_summary_pdf" in ids


# -------------------- CSV — DR --------------------

class TestFiscalSummaryDR:
    def test_csv_period_yyyy_mm(self, client):
        _set_country(client, "DO")
        r = client.get(
            f"{BASE_URL}/api/multi-country-reports/fiscal-summary",
            params={"period": PERIOD, "format": "csv"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "text/csv" in ct
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert f'FiscalSummary_DO_{PERIOD}.csv' in cd

        rows = _parse_csv(r.content)
        # Title row
        assert any("REPORTE FISCAL" in (row[0] if row else "") for row in rows[:5])
        # Empresa, ID Fiscal, Período, Moneda, Agencia, SS, Generado
        flat = "\n".join(",".join(row) for row in rows[:8])
        assert "Empresa" in flat
        assert "Período" in flat
        assert "Moneda" in flat
        assert "DOP" in flat
        assert "DGII" in flat  # DR agency
        # Header data row
        header = _find_header_row(rows)
        assert header is not None, "No data header row '#' found"
        # DR codes: SFS, AFP for employee; SRL, INFOTEP for employer
        flat_header = " | ".join(header)
        assert "SFS" in flat_header
        assert "AFP" in flat_header
        assert "INFOTEP" in flat_header

    def test_csv_period_id(self, client):
        _set_country(client, "DO")
        r = client.get(
            f"{BASE_URL}/api/multi-country-reports/fiscal-summary",
            params={"period": PERIOD_ID, "format": "csv"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        cd = r.headers.get("content-disposition", "")
        assert f'FiscalSummary_DO_{PERIOD_ID}.csv' in cd
        rows = _parse_csv(r.content)
        header = _find_header_row(rows)
        assert header is not None

    def test_pdf_DR(self, client):
        _set_country(client, "DO")
        r = client.get(
            f"{BASE_URL}/api/multi-country-reports/fiscal-summary",
            params={"period": PERIOD, "format": "pdf"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        assert "application/pdf" in r.headers.get("content-type", "")
        cd = r.headers.get("content-disposition", "")
        assert f'FiscalSummary_DO_{PERIOD}.pdf' in cd
        # Valid PDF
        assert r.content[:5] == b"%PDF-", f"Not a valid PDF: {r.content[:20]}"
        assert len(r.content) > 2000, f"PDF too small: {len(r.content)} bytes"


# -------------------- Multi-country adaptation --------------------

class TestMultiCountryAdaptation:
    def _csv_header(self, client, period=PERIOD):
        r = client.get(
            f"{BASE_URL}/api/multi-country-reports/fiscal-summary",
            params={"period": period, "format": "csv"},
            timeout=60,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        rows = _parse_csv(r.content)
        header = _find_header_row(rows)
        assert header is not None, "Missing data header in CSV"
        flat_meta = " ".join(",".join(row) for row in rows[:6])
        return header, flat_meta, r

    def test_CO(self, client):
        _set_country(client, "CO")
        header, meta, r = self._csv_header(client)
        flat = " | ".join(header)
        # CO codes
        for code in ["SALUD", "PENSION", "ARL", "CCF", "ICBF", "SENA"]:
            assert code in flat, f"Missing CO code {code} in header: {flat}"
        assert "DIAN" in meta, f"DIAN not found in metadata: {meta}"
        assert "FiscalSummary_CO_" in r.headers.get("content-disposition", "")

    def test_US(self, client):
        _set_country(client, "US")
        header, meta, r = self._csv_header(client)
        flat = " | ".join(header)
        for code in ["SS", "MEDICARE", "FUTA"]:
            assert code in flat, f"Missing US code {code} in header: {flat}"
        assert "IRS" in meta, f"IRS not found in metadata: {meta}"
        assert "FiscalSummary_US_" in r.headers.get("content-disposition", "")

    def test_ES(self, client):
        _set_country(client, "ES")
        header, meta, r = self._csv_header(client)
        flat = " | ".join(header)
        # Spain uses CC (Contingencias Comunes), DESEMPLEO, FP, FOGASA
        for code in ["CC", "DESEMPLEO", "FP", "FOGASA"]:
            assert code in flat, f"Missing ES code {code} in header: {flat}"
        assert "AEAT" in meta, f"AEAT not found: {meta}"
        assert "FiscalSummary_ES_" in r.headers.get("content-disposition", "")

    def test_MX(self, client):
        _set_country(client, "MX")
        header, meta, r = self._csv_header(client)
        flat = " | ".join(header)
        assert "IMSS" in flat, f"IMSS not found in header: {flat}"
        assert "SAT" in meta, f"SAT not found: {meta}"
        assert "FiscalSummary_MX_" in r.headers.get("content-disposition", "")


# -------------------- Error handling --------------------

class TestErrors:
    def test_invalid_format(self, client):
        _set_country(client, "DO")
        r = client.get(
            f"{BASE_URL}/api/multi-country-reports/fiscal-summary",
            params={"period": PERIOD, "format": "xml"},
            timeout=30,
        )
        assert r.status_code == 400
        d = r.json()
        msg = d.get("detail") or d.get("message") or ""
        assert "format" in msg.lower() or "formato" in msg.lower()

    def test_missing_period(self, client):
        _set_country(client, "DO")
        r = client.get(
            f"{BASE_URL}/api/multi-country-reports/fiscal-summary",
            params={"period": "2099-12", "format": "csv"},
            timeout=30,
        )
        assert r.status_code == 404
        d = r.json()
        msg = d.get("detail") or d.get("message") or ""
        assert "no hay datos" in msg.lower() or "nómina" in msg.lower() or "nomina" in msg.lower()


# -------------------- DR Regression after switches --------------------

class TestDrRegression:
    def test_restore_to_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/country-config/company", timeout=30)
        assert r.status_code == 200
        assert r.json().get("country_code") == "DO"

    def test_tss_autodeterminacion(self, client):
        _set_country(client, "DO")
        r = client.get(
            f"{BASE_URL}/api/dgii-reports/tss/autodeterminacion",
            params={"period": PERIOD},
            timeout=30,
        )
        # Note iter231 reported pre-existing 500 if any employee has document_number=None.
        # Accept 200 (passes) or document the failure. Test passes if 200.
        assert r.status_code == 200, f"DGII autodeterminacion: {r.status_code} {r.text[:300]}"

    def test_tss_report(self, client):
        _set_country(client, "DO")
        r = client.get(
            f"{BASE_URL}/api/payroll/periods/{PERIOD_ID}/tss-report",
            timeout=30,
        )
        assert r.status_code == 200, f"tss-report: {r.status_code} {r.text[:300]}"

    def test_tss_preview(self, client):
        _set_country(client, "DO")
        r = client.get(
            f"{BASE_URL}/api/payroll/periods/{PERIOD_ID}/tss-preview",
            timeout=30,
        )
        assert r.status_code == 200, f"tss-preview: {r.status_code} {r.text[:300]}"
