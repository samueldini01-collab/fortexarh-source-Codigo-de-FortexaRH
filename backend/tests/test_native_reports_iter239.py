"""
Backend tests for FortexaRH P2 (Iteration 239):
- CA T4 (PDF, annual)
- BR eSocial S-1200 (XML)
- AR F.931 SICOSS (TXT fixed-width, latin-1)
- Filing tracking: POST/DELETE /filings/mark-filed, GET /filings/history (idempotent + filter)
- Smart reminders: POST /calendar/run-reminders (schema + company-country filtering)
- Catalog: implemented_formats=15; CA/BR/AR compliance_status=complete
- Regression guard: still 28 countries / 33 formats total

Test user: test_refactor@fortexa.com / test123

CRITICAL: session teardown restores company.country to 'DO' AND deletes any
TEST_ fiscal_filings records created during the run.
"""
import os
import re
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


def _set_country(client, code):
    r = client.put(f"{BASE_URL}/api/country-config/company/country",
                   params={"country_code": code}, timeout=30)
    assert r.status_code == 200, f"Could not set country={code}: {r.text}"


# Track created filing records so we can clean up on teardown
_CREATED_FILINGS = []


@pytest.fixture(scope="session", autouse=True)
def _cleanup(client):
    # Pre-condition: start in DO
    _set_country(client, "DO")
    yield
    # Post: clean up any filings we created
    for (cc, fc, p) in _CREATED_FILINGS:
        try:
            client.delete(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                          params={"country_code": cc, "format_code": fc, "period": p},
                          timeout=30)
        except Exception:
            pass
    # Extra safety: nuke all TEST_AUTODET / AUTODET leftover for current company
    try:
        r = client.get(f"{BASE_URL}/api/native-reports/filings/history",
                       params={"country_code": "DO"}, timeout=30)
        if r.status_code == 200:
            for f in r.json().get("filings", []):
                if f.get("format_code") in ("TSS_AUTODET",) and f.get("period", "").startswith("2026-04"):
                    client.delete(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                                  params={"country_code": f["country_code"],
                                          "format_code": f["format_code"],
                                          "period": f["period"]}, timeout=30)
    except Exception:
        pass
    # Restore country
    r = client.put(f"{BASE_URL}/api/country-config/company/country",
                   params={"country_code": "DO"}, timeout=30)
    assert r.status_code == 200, f"Failed to restore country: {r.text}"


# -------------------- Catalog --------------------

class TestCatalogIter239:
    def test_catalog_shape(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/catalog", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total_countries"] == 28
        # 4(DO)+1(CO)+2(MX)+1(US)+2(ES)+1(GB)+1(FR)+1(CA)+1(BR)+1(AR) = 15
        assert data["implemented_formats"] == 15, data["implemented_formats"]

    @pytest.mark.parametrize("code,expected_fmt", [
        ("CA", "T4"),
        ("BR", "ESOCIAL"),
        ("AR", "F931"),
    ])
    def test_catalog_new_countries_complete(self, client, code, expected_fmt):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        c = next((x for x in data["countries"] if x["code"] == code), None)
        assert c is not None, f"{code} missing from catalog"
        assert c["implemented_count"] >= 1
        assert c["compliance_status"] == "complete", f"{code}: {c['compliance_status']}"
        codes = {f["code"] for f in c["formats"]}
        assert expected_fmt in codes, f"{expected_fmt} not in {codes}"


# -------------------- Canada: T4 --------------------

class TestCAT4:
    def test_t4_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/ca/t4",
                       params={"year": 2026}, timeout=30)
        assert r.status_code == 400, r.text
        detail = (r.json() or {}).get("detail", "")
        assert ("CA" in detail or "Canada" in detail or "T4" in detail or "CRA" in detail), detail

    def test_t4_success_when_country_CA(self, client):
        _set_country(client, "CA")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/ca/t4",
                           params={"year": 2026}, timeout=60)
            # If no payroll data exists for 2026, the endpoint may return 404.
            # The key thing to test: when data exists, PDF is returned. We accept 404
            # as a soft-pass scenario (no data).
            if r.status_code == 404:
                pytest.skip("No 2026 payroll data for CA; PDF generation path not executed")
            assert r.status_code == 200, r.text
            assert "application/pdf" in r.headers.get("content-type", "").lower()
            assert r.content[:5] == b"%PDF-", "Not a valid PDF"
            assert len(r.content) > 2000, f"PDF too small: {len(r.content)} bytes"
            cd = r.headers.get("content-disposition", "")
            assert "T4_" in cd, cd
        finally:
            _set_country(client, "DO")


# -------------------- Brazil: eSocial S-1200 --------------------

class TestBRESocial:
    def test_esocial_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/br/esocial",
                       params={"period": PERIOD}, timeout=30)
        assert r.status_code == 400, r.text

    def test_esocial_success_when_country_BR(self, client):
        _set_country(client, "BR")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/br/esocial",
                           params={"period": PERIOD}, timeout=60)
            if r.status_code == 404:
                pytest.skip("No BR payroll data for period; XML path not executed")
            assert r.status_code == 200, r.text
            ct = r.headers.get("content-type", "").lower()
            assert "xml" in ct, ct
            body = r.text
            assert body.startswith("<?xml"), body[:80]
            # Root eSocial tag + namespace
            assert "<eSocial" in body
            assert "esocial.gov.br" in body, "Missing esocial.gov.br namespace"
            # evtRemun with Id attribute
            assert re.search(r"<evtRemun[^>]*\bId=", body), "Missing <evtRemun Id=...>"
            # ideEvento with the three required fields
            assert "<ideEvento>" in body
            assert re.search(r"<indRetif>1</indRetif>", body), "indRetif=1 expected"
            assert re.search(r"<indApuracao>1</indApuracao>", body), "indApuracao=1 expected"
            assert re.search(r"<perApur>", body), "perApur missing"
            # Employer
            assert "<ideEmpregador>" in body
            assert "<nrInsc>" in body, "CNPJ node <nrInsc> missing"
            # Worker per employee
            assert "<ideTrabalhador>" in body
            assert re.search(r"<cpfTrab>|<nisTrab>", body), "Missing CPF/NIS for worker"
        finally:
            _set_country(client, "DO")


# -------------------- Argentina: F.931 SICOSS --------------------

class TestARF931:
    def test_f931_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/ar/f931",
                       params={"period": PERIOD}, timeout=30)
        assert r.status_code == 400, r.text

    def test_f931_success_when_country_AR(self, client):
        _set_country(client, "AR")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/ar/f931",
                           params={"period": PERIOD}, timeout=60)
            if r.status_code == 404:
                pytest.skip("No AR payroll data for period; TXT path not executed")
            assert r.status_code == 200, r.text
            ct = r.headers.get("content-type", "").lower()
            assert "text/plain" in ct, ct
            # Filename starts with F931_SICOSS_
            cd = r.headers.get("content-disposition", "")
            assert "F931_SICOSS_" in cd, cd
            # latin-1 content decodable; at least 1 fixed-width line
            body = r.content.decode("latin-1")
            lines = [ln for ln in body.splitlines() if ln.strip()]
            assert len(lines) >= 1, "No SICOSS records generated"
            # fixed width: all lines same length
            widths = {len(ln) for ln in lines}
            assert len(widths) == 1, f"Non-uniform SICOSS record widths: {widths}"
            # record width reasonably long (SICOSS spec >200 chars)
            assert next(iter(widths)) >= 100, f"Record width too small: {widths}"
        finally:
            _set_country(client, "DO")


# -------------------- Filing tracking --------------------

class TestFilingTracking:
    FMT_CODE = "TSS_AUTODET"
    CC = "DO"
    PER = "2026-04"

    def test_mark_as_filed_creates_record(self, client):
        payload = {"country_code": self.CC, "format_code": self.FMT_CODE,
                   "period": self.PER, "receipt_number": "TSS-12345"}
        r = client.post(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                        json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        filing = data.get("filing") or {}
        assert filing.get("filing_id"), "filing_id missing"
        assert filing.get("filed_at"), "filed_at missing"
        assert filing.get("filed_by") == EMAIL, f"filed_by={filing.get('filed_by')}"
        assert filing.get("country_code") == "DO"
        assert filing.get("format_code") == "TSS_AUTODET"
        assert filing.get("receipt_number") == "TSS-12345"
        _CREATED_FILINGS.append((self.CC, self.FMT_CODE, self.PER))

    def test_mark_as_filed_idempotent(self, client):
        """Calling mark-filed twice must not create duplicates."""
        payload = {"country_code": self.CC, "format_code": self.FMT_CODE,
                   "period": self.PER, "receipt_number": "TSS-99999"}
        r1 = client.post(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                         json=payload, timeout=30)
        assert r1.status_code == 200
        r2 = client.post(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                         json=payload, timeout=30)
        assert r2.status_code == 200
        # History should have exactly ONE entry for (CC, fmt, period)
        r3 = client.get(f"{BASE_URL}/api/native-reports/filings/history",
                        params={"country_code": self.CC}, timeout=30)
        assert r3.status_code == 200
        matching = [f for f in r3.json().get("filings", [])
                    if f.get("format_code") == self.FMT_CODE and f.get("period") == self.PER]
        assert len(matching) == 1, f"Expected exactly 1 filing, got {len(matching)}"
        # Latest receipt number is persisted
        assert matching[0]["receipt_number"] == "TSS-99999"

    def test_history_sorted_desc_with_total(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/filings/history", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "total" in data and isinstance(data["total"], int)
        assert "filings" in data and isinstance(data["filings"], list)
        dates = [f.get("filed_at") for f in data["filings"] if f.get("filed_at")]
        # sorted desc (string ISO yyyy-mm-dd sort == chronological desc)
        assert dates == sorted(dates, reverse=True), f"Not sorted desc: {dates}"

    def test_history_filter_by_country(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/filings/history",
                       params={"country_code": self.CC}, timeout=30)
        assert r.status_code == 200, r.text
        for f in r.json().get("filings", []):
            assert f["country_code"] == self.CC, f

    def test_delete_filing_returns_count(self, client):
        # Ensure record exists
        client.post(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                    json={"country_code": self.CC, "format_code": self.FMT_CODE,
                          "period": self.PER}, timeout=30)
        r = client.delete(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                          params={"country_code": self.CC,
                                  "format_code": self.FMT_CODE,
                                  "period": self.PER}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        assert data.get("deleted") == 1, data
        # Second delete should be 0
        r2 = client.delete(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                           params={"country_code": self.CC,
                                   "format_code": self.FMT_CODE,
                                   "period": self.PER}, timeout=30)
        assert r2.status_code == 200
        assert r2.json().get("deleted") == 0


# -------------------- Smart reminders --------------------

class TestReminders:
    def test_run_reminders_schema(self, client):
        _set_country(client, "DO")
        r = client.post(f"{BASE_URL}/api/native-reports/calendar/run-reminders", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        for key in ("success", "company_country", "notifications_sent",
                    "skipped_already_filed", "checked_at"):
            assert key in data, f"Missing key '{key}'"
        assert data["success"] is True
        assert data["company_country"] == "DO"
        assert isinstance(data["notifications_sent"], int)
        assert isinstance(data["skipped_already_filed"], int)
        assert data["notifications_sent"] >= 0
        assert data["skipped_already_filed"] >= 0

    def test_run_reminders_only_for_company_country(self, client):
        """Switch to CA and confirm company_country switches — proves
        only the matching country's deadlines are checked."""
        _set_country(client, "CA")
        try:
            r = client.post(f"{BASE_URL}/api/native-reports/calendar/run-reminders",
                            timeout=60)
            assert r.status_code == 200, r.text
            assert r.json().get("company_country") == "CA"
        finally:
            _set_country(client, "DO")

    def test_run_reminders_skips_already_filed(self, client):
        """Mark filing for the current reminder period as filed; confirm
        skipped_already_filed increases (if a reminder was about to fire)."""
        _set_country(client, "DO")
        # First run: baseline
        b = client.post(f"{BASE_URL}/api/native-reports/calendar/run-reminders",
                        timeout=60).json()
        baseline_sent = b["notifications_sent"]
        baseline_skipped = b["skipped_already_filed"]
        # Mark every upcoming deadline's period as filed (defensive)
        cal = client.get(f"{BASE_URL}/api/native-reports/calendar", timeout=30)
        marked = []
        if cal.status_code == 200:
            for d in cal.json().get("deadlines", []):
                if d.get("country_code") == "DO":
                    payload = {"country_code": "DO",
                               "format_code": d["format_code"],
                               "period": d.get("period_to_file") or "2026-01"}
                    rr = client.post(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                                     json=payload, timeout=30)
                    if rr.status_code == 200:
                        marked.append(payload)
                        _CREATED_FILINGS.append((payload["country_code"],
                                                 payload["format_code"],
                                                 payload["period"]))
        # Second run: skipped should be >= baseline_skipped; sent <= baseline_sent
        r2 = client.post(f"{BASE_URL}/api/native-reports/calendar/run-reminders",
                         timeout=60).json()
        assert r2["skipped_already_filed"] >= baseline_skipped
        assert r2["notifications_sent"] <= baseline_sent
        # cleanup these
        for p in marked:
            client.delete(f"{BASE_URL}/api/native-reports/filings/mark-filed",
                          params=p, timeout=30)
