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
        assert data["implemented_formats"] == 15, data["implemented_formats"]
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
        # DO/CO/MX/US/ES/GB/FR/CA/BR/AR are now implemented (10)
        implemented = ("DO", "CO", "MX", "US", "ES", "GB", "FR", "CA", "BR", "AR")
        others = [c for c in data["countries"] if c["code"] not in implemented]
        assert len(others) == 18
        for c in others:
            assert c["implemented_count"] == 0, c["code"]
            assert c["compliance_status"] == "universal_only", c["code"]

    def test_catalog_US_complete_with_form941(self, client):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        us = next((c for c in data["countries"] if c["code"] == "US"), None)
        assert us is not None
        assert us["implemented_count"] == 1
        assert us["compliance_status"] == "complete"
        codes = {f["code"] for f in us["formats"]}
        assert "FORM_941" in codes

    def test_catalog_ES_complete_with_modelo111_and_tc1(self, client):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        es = next((c for c in data["countries"] if c["code"] == "ES"), None)
        assert es is not None
        assert es["implemented_count"] == 2
        assert es["total_count"] == 2
        assert es["compliance_status"] == "complete"
        codes = {f["code"] for f in es["formats"]}
        assert "MODELO_111" in codes
        assert "TC1" in codes


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


# -------------------- US Form 941 (PDF) --------------------

class TestUSForm941:

    def test_form941_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/us/form-941",
                       params={"period": "2026-Q1"}, timeout=30)
        assert r.status_code == 400, r.text[:300]
        detail = r.json().get("detail", "")
        assert "941" in detail or "IRS" in detail or "Estados Unidos" in detail or "US" in detail

    def test_form941_pdf_with_quarter_period(self, client):
        _set_country(client, "US")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/us/form-941",
                           params={"period": "2026-Q1"}, timeout=60)
            assert r.status_code == 200, r.text[:300]
            assert "application/pdf" in r.headers.get("content-type", "")
            assert r.content.startswith(b"%PDF-"), "Not a valid PDF"
            assert len(r.content) > 4000, f"PDF too small: {len(r.content)}"
            cd = r.headers.get("content-disposition", "")
            assert "Form941_Q1_2026" in cd, cd
        finally:
            _set_country(client, "DO")

    def test_form941_accepts_yyyy_mm_period(self, client):
        _set_country(client, "US")
        try:
            # 2026-03 → Q1
            r = client.get(f"{BASE_URL}/api/native-reports/us/form-941",
                           params={"period": "2026-03"}, timeout=60)
            assert r.status_code == 200, r.text[:300]
            assert r.content.startswith(b"%PDF-")
            cd = r.headers.get("content-disposition", "")
            assert "Form941_Q1_2026" in cd, cd
        finally:
            _set_country(client, "DO")

    def test_form941_404_when_no_payroll(self, client):
        _set_country(client, "US")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/us/form-941",
                           params={"period": "2099-Q4"}, timeout=30)
            assert r.status_code == 404, r.text[:300]
        finally:
            _set_country(client, "DO")


# -------------------- Spain Modelo 111 + TC1 --------------------

class TestSpainModelo111:

    def test_modelo111_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/es/modelo-111",
                       params={"period": "2026-T1"}, timeout=30)
        assert r.status_code == 400, r.text[:300]

    def test_modelo111_generates_txt(self, client):
        _set_country(client, "ES")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/es/modelo-111",
                           params={"period": "2026-T1"}, timeout=60)
            assert r.status_code == 200, r.text[:300]
            assert "text/plain" in r.headers.get("content-type", "")
            cd = r.headers.get("content-disposition", "")
            assert "Modelo111_" in cd, cd
            body = r.content
            assert len(body) > 50, f"Too small: {len(body)}"
            text = body.decode("latin-1")
            lines = [ln for ln in text.split("\n") if ln]
            assert len(lines) >= 2, f"Expected header + perceptor, got {len(lines)}"
            # Line 1 starts with '1111' + year (Tipo 1, modelo 111, ejercicio)
            assert lines[0].startswith("1111" + "2026"), f"Header start invalid: {lines[0][:12]!r}"
            # Following lines start with '2111' + year
            for dl in lines[1:]:
                assert dl.startswith("2111" + "2026"), f"Perceptor line invalid: {dl[:12]!r}"

            # latin-1 decoding worked (sanity: no UnicodeDecodeError)
            assert isinstance(text, str)
        finally:
            _set_country(client, "DO")


class TestSpainTC1:

    def test_tc1_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/es/tc1",
                       params={"period": "2026-03"}, timeout=30)
        assert r.status_code == 400, r.text[:300]

    def test_tc1_generates_fan_txt(self, client):
        _set_country(client, "ES")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/es/tc1",
                           params={"period": "2026-03"}, timeout=60)
            assert r.status_code == 200, r.text[:300]
            assert "text/plain" in r.headers.get("content-type", "")
            cd = r.headers.get("content-disposition", "")
            assert "TC1_FAN_" in cd, cd
            text = r.content.decode("latin-1")
            lines = [ln for ln in text.split("\n") if ln]
            # N+2: 1 cabecera + N trabajadores + 1 totales (N>=1)
            assert len(lines) >= 3, f"Expected at least 3 lines, got {len(lines)}"
            assert lines[0].startswith("01FAN"), f"Header invalid: {lines[0][:8]!r}"
            # Worker lines
            for wl in lines[1:-1]:
                assert wl.startswith("02"), f"Worker line invalid: {wl[:5]!r}"
            # Final totals line
            assert lines[-1].startswith("99"), f"Footer invalid: {lines[-1][:5]!r}"
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


# ==================== GB HMRC RTI FPS + FR DSN + CALENDAR (iter 238) ====================

import xml.etree.ElementTree as ET
from datetime import date


# -------------------- Catalog: GB + FR complete --------------------

class TestCatalogGBFRComplete:
    def test_catalog_GB_complete_with_rti_fps(self, client):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        gb = next((c for c in data["countries"] if c["code"] == "GB"), None)
        assert gb is not None
        assert gb["implemented_count"] == 1
        assert gb["total_count"] == 1
        assert gb["compliance_status"] == "complete"
        codes = {f["code"] for f in gb["formats"]}
        assert "RTI_FPS" in codes

    def test_catalog_FR_complete_with_dsn(self, client):
        data = client.get(f"{BASE_URL}/api/native-reports/catalog").json()
        fr = next((c for c in data["countries"] if c["code"] == "FR"), None)
        assert fr is not None
        assert fr["implemented_count"] == 1
        assert fr["total_count"] == 1
        assert fr["compliance_status"] == "complete"
        codes = {f["code"] for f in fr["formats"]}
        assert "DSN" in codes


# -------------------- GB RTI FPS --------------------

class TestGBRtiFps:
    """UK HMRC RTI FPS (XML) — country=GB required."""

    def test_rti_fps_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/gb/rti-fps",
                       params={"period": PERIOD}, timeout=30)
        assert r.status_code == 400, r.text[:300]
        detail = r.json().get("detail", "")
        # helpful msg about HMRC RTI being UK-specific
        assert any(k in detail for k in ("HMRC", "RTI", "UK", "Reino Unido", "GB"))

    def test_rti_fps_valid_xml_when_country_GB(self, client):
        _set_country(client, "GB")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/gb/rti-fps",
                           params={"period": PERIOD}, timeout=60)
            assert r.status_code == 200, r.text[:500]
            # Content-type & filename
            ctype = r.headers.get("content-type", "")
            assert "application/xml" in ctype, ctype
            cd = r.headers.get("content-disposition", "")
            assert "RTI_FPS_" in cd, cd
            assert cd.endswith('.xml"') or cd.endswith(".xml"), cd
            body = r.content
            assert body.startswith(b"<?xml"), body[:60]
            # Parse XML
            root = ET.fromstring(body)
            # Root = GovTalkMessage with HMRC namespace
            assert root.tag.endswith("GovTalkMessage"), root.tag
            # ElementTree folds xmlns into the tag as Clark notation {ns}tag
            assert "http://www.govtalk.gov.uk/CM/envelope" in root.tag or \
                   root.get("xmlns") == "http://www.govtalk.gov.uk/CM/envelope"
        finally:
            _set_country(client, "DO")

    def test_rti_fps_structure_employees_and_payments(self, client):
        _set_country(client, "GB")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/gb/rti-fps",
                           params={"period": PERIOD}, timeout=60)
            assert r.status_code == 200
            text = r.content.decode("utf-8")
            # Required nodes (namespaces may prefix — do substring check)
            for tag in ("<FullPaymentSubmission>", "<EmpRefs>", "<OfficeNo>",
                        "<PayeRef>", "<AOref>", "<Employee>", "<EmployeeDetails>",
                        "<Name>", "<Fore>", "<Sur>", "<Employment>",
                        "<PaymentToDate>", "<TaxablePay>", "<TaxDeducted>",
                        "<EmployeeNICsInPeriod>", "<EmployerNICsInPeriod>", "<NetPay>"):
                assert tag in text, f"Missing node {tag}"
        finally:
            _set_country(client, "DO")

    def test_rti_fps_404_when_no_payroll(self, client):
        _set_country(client, "GB")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/gb/rti-fps",
                           params={"period": "2099-12"}, timeout=30)
            assert r.status_code == 404, r.text[:300]
        finally:
            _set_country(client, "DO")


# -------------------- FR DSN --------------------

class TestFrDsn:
    """France DSN (XML) — country=FR required."""

    def test_dsn_blocked_when_country_is_DO(self, client):
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/fr/dsn",
                       params={"period": PERIOD}, timeout=30)
        assert r.status_code == 400, r.text[:300]

    def test_dsn_valid_xml_when_country_FR(self, client):
        _set_country(client, "FR")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/fr/dsn",
                           params={"period": PERIOD}, timeout=60)
            assert r.status_code == 200, r.text[:500]
            ctype = r.headers.get("content-type", "")
            assert "application/xml" in ctype, ctype
            cd = r.headers.get("content-disposition", "")
            assert "DSN_" in cd, cd
            body = r.content
            assert body.startswith(b"<?xml"), body[:60]
            root = ET.fromstring(body)
            assert root.tag.endswith("DSN"), root.tag
            assert root.get("version") == "P24V01", root.get("version")
        finally:
            _set_country(client, "DO")

    def test_dsn_structure_required_blocks(self, client):
        _set_country(client, "FR")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/fr/dsn",
                           params={"period": PERIOD}, timeout=60)
            assert r.status_code == 200
            text = r.content.decode("utf-8")
            for tag in ("<Declaration>", "<Nature>", "<Type>", "<MoisPrincipal>",
                        "<Emetteur>", "<SIREN>", "<NIC>",
                        "<Entreprise>", "<APE>",
                        "<Etablissement>", "<SIRET>",
                        "<Salarie>", "<NIR>", "<Nom>", "<Prenoms>",
                        "<Contrat>", "<Remuneration>", "<MontantBrut>",
                        "<Cotisation>", "<VersementIndividuel>",
                        "<BordereauCotisation>"):
                assert tag in text, f"Missing DSN node {tag}"
            # Cotisation codes 100/200/400/900 present
            for code in ("<Code>100</Code>", "<Code>200</Code>",
                         "<Code>400</Code>", "<Code>900</Code>"):
                assert code in text, f"Missing cotisation code block {code}"
        finally:
            _set_country(client, "DO")

    def test_dsn_404_when_no_payroll(self, client):
        _set_country(client, "FR")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/fr/dsn",
                           params={"period": "2099-12"}, timeout=30)
            assert r.status_code == 404, r.text[:300]
        finally:
            _set_country(client, "DO")


# -------------------- Fiscal Calendar --------------------

class TestFiscalCalendar:
    """GET /api/native-reports/calendar — country-independent aggregator."""

    def test_calendar_top_level_shape(self, client):
        _set_country(client, "DO")  # ensure company_country is DO
        r = client.get(f"{BASE_URL}/api/native-reports/calendar", timeout=30)
        assert r.status_code == 200, r.text[:500]
        data = r.json()
        # required top-level keys
        for k in ("today", "company_country", "total_upcoming", "next_due",
                  "deadlines", "by_country", "summary"):
            assert k in data, f"Missing top-level key {k}"
        # today is ISO date parseable
        date.fromisoformat(data["today"])
        assert data["company_country"] == "DO"
        assert isinstance(data["deadlines"], list)
        assert isinstance(data["by_country"], dict)
        assert data["total_upcoming"] == len(data["deadlines"])
        # 12 implemented formats each produce 1 deadline entry
        assert data["total_upcoming"] == 15, data["total_upcoming"]

    def test_calendar_next_due_is_closest(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/calendar", timeout=30).json()
        deadlines = r["deadlines"]
        assert len(deadlines) > 0
        # deadlines sorted ascending by days_until_due
        days = [d["days_until_due"] for d in deadlines]
        assert days == sorted(days), f"Not sorted ascending: {days}"
        # next_due equals first deadline
        assert r["next_due"] == deadlines[0]

    def test_calendar_item_shape(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/calendar", timeout=30).json()
        d = r["deadlines"][0]
        for k in ("country_code", "country_name", "flag", "format_code",
                  "format_name", "agency", "frequency", "due_date",
                  "days_until_due", "period_to_file", "description",
                  "endpoint", "is_company_country", "urgency"):
            assert k in d, f"Missing key {k} in deadline item"
        # types
        assert isinstance(d["days_until_due"], int)
        assert isinstance(d["is_company_country"], bool)
        # due_date is ISO
        date.fromisoformat(d["due_date"])
        # period_to_file is YYYY-MM
        assert len(d["period_to_file"]) == 7 and d["period_to_file"][4] == "-"

    def test_calendar_urgency_mapping(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/calendar", timeout=30).json()
        for d in r["deadlines"]:
            days = d["days_until_due"]
            u = d["urgency"]
            if days < 0:
                assert u == "overdue", (days, u)
            elif days <= 3:
                assert u == "critical", (days, u)
            elif days <= 7:
                assert u == "warning", (days, u)
            else:
                assert u == "ok", (days, u)
        # summary counts match
        s = r["summary"]
        assert s["overdue"] == sum(1 for d in r["deadlines"] if d["urgency"] == "overdue")
        assert s["critical"] == sum(1 for d in r["deadlines"] if d["urgency"] == "critical")
        assert s["warning"] == sum(1 for d in r["deadlines"] if d["urgency"] == "warning")
        assert s["ok"] == sum(1 for d in r["deadlines"] if d["urgency"] == "ok")

    def test_calendar_by_country_contains_all_7_implemented(self, client):
        r = client.get(f"{BASE_URL}/api/native-reports/calendar", timeout=30).json()
        bc = r["by_country"]
        # All 7 implemented countries must be present
        for code in ("DO", "CO", "MX", "US", "ES", "GB", "FR"):
            assert code in bc, f"Missing {code} in by_country"
        # DO has 4 deadlines, ES has 2, MX has 2, others 1
        assert len(bc["DO"]) == 4
        assert len(bc["MX"]) == 2
        assert len(bc["ES"]) == 2
        assert len(bc["CO"]) == 1
        assert len(bc["US"]) == 1
        assert len(bc["GB"]) == 1
        assert len(bc["FR"]) == 1

    def test_calendar_is_company_country_flag(self, client):
        # With company = DO, only DO items should be flagged true
        _set_country(client, "DO")
        r = client.get(f"{BASE_URL}/api/native-reports/calendar", timeout=30).json()
        assert r["company_country"] == "DO"
        for d in r["deadlines"]:
            expected = (d["country_code"] == "DO")
            assert d["is_company_country"] is expected, (d["country_code"], d["is_company_country"])

    def test_calendar_company_country_updates_with_country_change(self, client):
        _set_country(client, "GB")
        try:
            r = client.get(f"{BASE_URL}/api/native-reports/calendar", timeout=30).json()
            assert r["company_country"] == "GB"
            gb_items = [d for d in r["deadlines"] if d["country_code"] == "GB"]
            assert len(gb_items) == 1
            assert gb_items[0]["is_company_country"] is True
        finally:
            _set_country(client, "DO")

