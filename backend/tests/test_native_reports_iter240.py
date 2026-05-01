"""
Iteration 240 backend tests: FortexaRH native fiscal reports coverage expanded
to 33/33 (28 countries fully implemented) + APScheduler daily cron
(/calendar/run-reminders-all).

Scope:
  - Catalog: total_formats=33, implemented_formats=33, catalog exposes endpoint
    URL for each new format code.
  - 18 new endpoints (CL/PE/EC/VE/BO/PY/UY/GY/SR/CR/SV/GT/HN/NI/PA/CU/HT/PR)
    respond with the country-guard HTTP 400 and Spanish guidance when called
    by a DO test company.
  - Regression: existing native formats still return 400 (country mismatch) for
    DO company (not 404/500).
  - /calendar/run-reminders (per-company) still works (schema unchanged).
  - /calendar/run-reminders-all returns the global summary for an admin user
    (processed_companies / total_notifications_sent / total_skipped_already_filed
    / errors[]).
  - /calendar returns deadlines including the new format codes for the user's
    country (DO deadlines for this admin).
  - /filings/history returns {total, filings[]}.
  - Backend logs indicate APScheduler job 'fiscal_reminders_daily @ 08:00 UTC'
    (asserted via a separate log-grep helper).

Test company country is DO — country-guard 400s for non-DO formats are the
CORRECT behaviour per system design, not a bug.
"""
import os
import re
import pytest
import requests

_env_url = os.environ.get("REACT_APP_BACKEND_URL")
if not _env_url:
    # Fallback: read from frontend/.env directly (pytest runs without frontend env loaded)
    try:
        with open("/app/frontend/.env") as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    _env_url = line.split("=", 1)[1].strip()
                    break
    except Exception:
        pass
assert _env_url, "REACT_APP_BACKEND_URL not configured"
BASE_URL = _env_url.rstrip("/")
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASS = "test123"

# The 18 new endpoints added in this iteration.
NEW_ENDPOINTS = [
    ("CL", "PREVIRED",      "/api/native-reports/cl/previred",      "period", "2025-01"),
    ("PE", "PLAME",         "/api/native-reports/pe/plame",         "period", "2025-01"),
    ("EC", "IESS_PLANILLA", "/api/native-reports/ec/iess",          "period", "2025-01"),
    ("VE", "IVSS_FORMA",    "/api/native-reports/ve/ivss",          "period", "2025-01"),
    ("BO", "F110",          "/api/native-reports/bo/f110",          "period", "2025-01"),
    ("PY", "F109",          "/api/native-reports/py/f109",          "period", "2025-01"),
    ("UY", "BPS_1146",      "/api/native-reports/uy/bps-1146",      "period", "2025-01"),
    ("GY", "NIS",           "/api/native-reports/gy/nis",           "period", "2025-01"),
    ("SR", "SZF",           "/api/native-reports/sr/szf",           "period", "2025-01"),
    ("CR", "CCSS_PLANILLA", "/api/native-reports/cr/ccss",          "period", "2025-01"),
    ("SV", "F1_ISSS",       "/api/native-reports/sv/f1-isss",       "period", "2025-01"),
    ("GT", "IGSS_PLANILLA", "/api/native-reports/gt/igss",          "period", "2025-01"),
    ("HN", "IHSS_PLANILLA", "/api/native-reports/hn/ihss",          "period", "2025-01"),
    ("NI", "INSS_PLANILLA", "/api/native-reports/ni/inss",          "period", "2025-01"),
    ("PA", "CSS_PLANILLA",  "/api/native-reports/pa/css",           "period", "2025-01"),
    ("CU", "ONAT_FORM",     "/api/native-reports/cu/onat",          "period", "2025-01"),
    ("HT", "ONA_DECLAR",    "/api/native-reports/ht/ona",           "period", "2025-01"),
    ("PR", "FORM_499R",     "/api/native-reports/pr/form-499r",     "year",   "2025"),
]

EXISTING_ENDPOINTS = [
    ("/api/native-reports/co/pila",        "period", "2025-01"),
    ("/api/native-reports/us/form-941",    "period", "2025-01"),
    ("/api/native-reports/es/modelo-111",  "period", "2025-01"),
    ("/api/native-reports/es/tc1",         "period", "2025-01"),
    ("/api/native-reports/gb/rti-fps",     "period", "2025-01"),
    ("/api/native-reports/fr/dsn",         "period", "2025-01"),
    ("/api/native-reports/ca/t4",          "year",   "2025"),
    ("/api/native-reports/br/esocial",     "period", "2025-01"),
    ("/api/native-reports/ar/f931",        "period", "2025-01"),
    ("/api/native-reports/mx/imss-cuotas", "period", "2025-01"),
    ("/api/native-reports/mx/infonavit",   "period", "2025-01"),
]


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(api_client):
    r = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---------- catalog ----------
class TestCatalog:
    def test_catalog_counts_33(self, api_client, auth_headers):
        r = api_client.get(f"{BASE_URL}/api/native-reports/catalog", headers=auth_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total_formats"] == 33, f"expected 33 total_formats, got {data['total_formats']}"
        assert data["implemented_formats"] == 33, (
            f"expected 33 implemented_formats, got {data['implemented_formats']}"
        )
        # 28 countries listed
        assert data["total_countries"] == 28, data["total_countries"]
        assert len(data["countries"]) == 28

    def test_catalog_exposes_new_endpoint_urls(self, api_client, auth_headers):
        r = api_client.get(f"{BASE_URL}/api/native-reports/catalog", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        by_code = {c["code"]: c for c in data["countries"]}
        for cc, fmt_code, endpoint, _, _ in NEW_ENDPOINTS:
            assert cc in by_code, f"country {cc} missing from catalog"
            fmt = next((f for f in by_code[cc]["formats"] if f["code"] == fmt_code), None)
            assert fmt, f"format {fmt_code} missing for {cc}"
            assert fmt.get("implemented") is True, f"{cc}/{fmt_code} not implemented"
            assert fmt.get("endpoint") == endpoint, f"{cc}/{fmt_code} endpoint={fmt.get('endpoint')} expected {endpoint}"


# ---------- 18 new endpoints country-guard ----------
class TestNewEndpointsCountryGuard:
    @pytest.mark.parametrize("cc,fmt_code,endpoint,pname,pval", NEW_ENDPOINTS)
    def test_country_guard_returns_400_spanish(self, api_client, auth_headers, cc, fmt_code, endpoint, pname, pval):
        r = api_client.get(f"{BASE_URL}{endpoint}?{pname}={pval}", headers=auth_headers, timeout=20)
        # DO company -> 400 guard is expected. A 404 or 500 would be a real bug.
        assert r.status_code == 400, f"{endpoint} expected 400 country-guard, got {r.status_code}: {r.text[:200]}"
        body = r.json()
        detail = (body.get("detail") or "") if isinstance(body, dict) else ""
        # Spanish guidance expectation — look for common Spanish tokens + country code.
        assert any(
            tok.lower() in detail.lower()
            for tok in ("país", "configurada", "configurado", "empresa", "requiere", "debe")
        ), f"{endpoint} detail not in Spanish guidance form: {detail!r}"


# ---------- existing endpoints regression ----------
class TestExistingEndpointsRegression:
    @pytest.mark.parametrize("endpoint,pname,pval", EXISTING_ENDPOINTS)
    def test_existing_endpoint_still_reachable(self, api_client, auth_headers, endpoint, pname, pval):
        r = api_client.get(f"{BASE_URL}{endpoint}?{pname}={pval}", headers=auth_headers, timeout=30)
        # For DO company: non-DO -> 400; endpoints accepting DO should be 200/valid.
        # Either way, must not 404 (route missing) or 500 (server bug).
        assert r.status_code in (200, 400), f"{endpoint} -> {r.status_code}: {r.text[:200]}"


# ---------- calendar ----------
class TestCalendarAndReminders:
    def test_calendar_deadlines(self, api_client, auth_headers):
        r = api_client.get(f"{BASE_URL}/api/native-reports/calendar", headers=auth_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        # should return list of deadlines for the company's country (DO)
        assert "deadlines" in data or isinstance(data, list), data
        items = data.get("deadlines", data if isinstance(data, list) else [])
        # Since the test company is DO, we expect at least the DO deadlines to appear.
        assert len(items) > 0, "calendar returned no deadlines for DO"
        # Validate structure of an entry
        sample = items[0]
        for key in ("country_code", "format_code"):
            assert key in sample, f"missing {key} in calendar item: {sample}"

    def test_run_reminders_per_company(self, api_client, auth_headers):
        r = api_client.post(
            f"{BASE_URL}/api/native-reports/calendar/run-reminders",
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        assert "notifications_sent" in data
        assert "skipped_already_filed" in data
        assert isinstance(data["notifications_sent"], int)
        assert isinstance(data["skipped_already_filed"], int)

    def test_run_reminders_all_requires_auth(self, api_client):
        # no headers -> 401/403
        r = requests.post(
            f"{BASE_URL}/api/native-reports/calendar/run-reminders-all",
            timeout=20,
        )
        assert r.status_code in (401, 403), f"expected auth failure, got {r.status_code}"

    def test_run_reminders_all_admin_ok(self, api_client, auth_headers):
        r = api_client.post(
            f"{BASE_URL}/api/native-reports/calendar/run-reminders-all",
            headers=auth_headers,
            timeout=120,
        )
        # test_refactor@fortexa.com is role=admin → should pass the role check
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        data = r.json()
        assert data.get("success") is True
        for key in (
            "processed_companies",
            "total_notifications_sent",
            "total_skipped_already_filed",
            "errors",
            "ran_at",
        ):
            assert key in data, f"missing {key} in response: {data}"
        assert isinstance(data["processed_companies"], int)
        assert isinstance(data["total_notifications_sent"], int)
        assert isinstance(data["total_skipped_already_filed"], int)
        assert isinstance(data["errors"], list)
        # With at least the admin's company, we should process >= 1
        assert data["processed_companies"] >= 1, data


# ---------- filings history ----------
class TestFilingsHistory:
    def test_history_schema(self, api_client, auth_headers):
        r = api_client.get(f"{BASE_URL}/api/native-reports/filings/history", headers=auth_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "total" in data
        assert "filings" in data
        assert isinstance(data["filings"], list)


# ---------- APScheduler log evidence ----------
class TestAPSchedulerLog:
    def test_scheduler_started_in_logs(self):
        """Check backend stderr log for APScheduler start message."""
        log_path = "/var/log/supervisor/backend.err.log"
        if not os.path.exists(log_path):
            pytest.skip("backend log not found")
        with open(log_path, "r", errors="ignore") as fh:
            content = fh.read()[-20000:]
        assert re.search(r"APScheduler started: fiscal_reminders_daily @ 08:00 UTC", content), (
            "APScheduler start log line not found in backend.err.log"
        )
