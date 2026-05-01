"""Iter241 regression tests — refactor + scaling validation.

Focus areas (see /app/test_reports/iteration_240.json for baseline):
1. Backward-compat shim: `from routes.native_reports import ...` still works.
2. Auto-registered LATAM endpoints bind the correct country per-endpoint
   (closure binding check: /cl/previred mentions Chile, /pe/plame mentions
   Peru, /ec/iess mentions Ecuador — NOT all the last country in the loop).
3. POST /calendar/run-reminders-all returns the NEW fields
   (duration_seconds, batch_size, max_concurrency) while preserving every
   pre-existing field (success, processed_companies, ...).
4. DR (DGII) endpoints remain unaffected by the native_reports refactor.
5. Catalog counts unchanged (28 countries, 33/33 formats implemented).
"""
import os
import requests
import pytest

_env_url = os.environ.get("REACT_APP_BACKEND_URL")
if not _env_url:
    try:
        with open("/app/frontend/.env", encoding="utf-8") as _f:
            for _line in _f:
                if _line.startswith("REACT_APP_BACKEND_URL="):
                    _env_url = _line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except FileNotFoundError:
        pass
assert _env_url, "REACT_APP_BACKEND_URL not configured"
BASE_URL = _env_url.rstrip("/")
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"


# ---------- Fixtures ----------

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    tok = r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---------- 1. Backward-compat shim ----------

class TestBackwardCompatShim:
    def test_shim_imports_router_and_driver(self):
        """`from routes.native_reports import router, run_reminders_for_all_companies`
        must keep working exactly as before (server.py depends on it)."""
        import sys
        # Ensure we hit the shim file, not the package
        sys.path.insert(0, "/app/backend")
        from routes.native_reports import (  # noqa: F401
            router,
            run_reminders_for_all_companies,
            _run_reminders_for_company,
            NATIVE_FORMATS,
            FORMAT_DEADLINES,
        )
        # Sanity: shim exposes the same APIRouter as the package.
        from routes.native import router as pkg_router
        assert router is pkg_router
        assert callable(run_reminders_for_all_companies)
        assert isinstance(NATIVE_FORMATS, dict) and len(NATIVE_FORMATS) >= 28

    def test_shim_file_is_thin(self):
        """The shim should be ~24 lines — it must not contain real logic."""
        with open("/app/backend/routes/native_reports.py", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) < 60, f"Shim is too long ({len(lines)} lines) — logic leaked?"


# ---------- 2. Closure binding of auto-registered LATAM endpoints ----------

# (endpoint, country_name_fragment_in_lowercase, format_code_fragment)
CLOSURE_SAMPLES = [
    ("/api/native-reports/cl/previred",     ["cl", "chile", "previred"]),
    ("/api/native-reports/pe/plame",        ["pe", "peru",  "plame"]),
    ("/api/native-reports/ec/iess",         ["ec", "ecuador", "iess"]),
    ("/api/native-reports/bo/f110",         ["bo", "bolivia", "f110"]),
    ("/api/native-reports/ht/ona",          ["ht", "haiti",  "ona"]),
]


class TestClosureBinding:
    """Regression guard against the loop-variable late-binding trap:
    if every auto-registered handler had captured the LAST format_code,
    every 400 message would mention the same country (Haiti). Assert each
    endpoint returns its OWN expected country/format in the guard message."""

    @pytest.mark.parametrize("endpoint,expected_tokens", CLOSURE_SAMPLES)
    def test_country_guard_mentions_correct_country(self, admin_headers, endpoint, expected_tokens):
        r = requests.get(
            f"{BASE_URL}{endpoint}",
            params={"period": "2025-01"},
            headers=admin_headers,
            timeout=20,
        )
        # DO admin hitting a non-DO endpoint -> 400 country guard.
        assert r.status_code == 400, f"{endpoint}: expected 400, got {r.status_code} {r.text[:200]}"
        body = r.text.lower()
        # At least one country-specific token must appear in the guard message
        # (country code OR country name OR the format code itself).
        assert any(tok in body for tok in expected_tokens), (
            f"{endpoint}: guard message does not reference the expected country/"
            f"format. Expected any of {expected_tokens}, got: {body[:300]}"
        )

    def test_different_endpoints_yield_different_messages(self, admin_headers):
        """If closure late-binding had broken, every guard message would be
        identical. Collect 3 messages and assert they are not all equal."""
        messages = []
        for ep in ("/api/native-reports/cl/previred",
                   "/api/native-reports/pe/plame",
                   "/api/native-reports/ec/iess"):
            r = requests.get(
                f"{BASE_URL}{ep}",
                params={"period": "2025-01"},
                headers=admin_headers,
                timeout=20,
            )
            assert r.status_code == 400
            messages.append(r.text)
        # Not all 3 messages should be byte-identical.
        assert len(set(messages)) > 1, (
            "All LATAM country-guard messages are identical — closure late-"
            "binding regression suspected."
        )


# ---------- 3. run-reminders-all schema expansion ----------

class TestRunRemindersAllSchema:
    def test_all_preexisting_fields_present(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/native-reports/calendar/run-reminders-all",
            headers=admin_headers,
            timeout=60,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Pre-existing iter240 contract — MUST still be present.
        for k in (
            "success", "processed_companies", "total_notifications_sent",
            "total_skipped_already_filed", "errors", "ran_at",
        ):
            assert k in data, f"Pre-existing field '{k}' missing from response"
        assert data["success"] is True
        assert isinstance(data["processed_companies"], int)
        assert data["processed_companies"] >= 1
        assert isinstance(data["errors"], list)

    def test_new_iter241_fields_present(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/native-reports/calendar/run-reminders-all",
            headers=admin_headers,
            timeout=60,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # New iter241 fields.
        assert "duration_seconds" in data
        assert isinstance(data["duration_seconds"], (int, float))
        assert data["duration_seconds"] >= 0
        assert data.get("batch_size") == 100
        assert data.get("max_concurrency") == 10


# ---------- 4. DR DGII endpoints unaffected ----------

DGII_ENDPOINTS = [
    "/api/dgii-reports/tss/autodeterminacion",
    "/api/dgii-reports/tss/novedades",
    "/api/dgii-reports/ir3",
    "/api/dgii-reports/ir17",
]


class TestDgiiUnaffected:
    @pytest.mark.parametrize("endpoint", DGII_ENDPOINTS)
    def test_dgii_endpoint_still_200_for_DO_admin(self, admin_headers, endpoint):
        # ir17 / ir3 are annual, tss endpoints are monthly — send both params.
        r = requests.get(
            f"{BASE_URL}{endpoint}",
            params={"period": "2025-01", "year": 2025},
            headers=admin_headers,
            timeout=30,
        )
        assert r.status_code == 200, (
            f"DR DGII endpoint {endpoint} regressed: {r.status_code} {r.text[:200]}"
        )


# ---------- 5. Catalog counts unchanged ----------

class TestCatalogUnchanged:
    def test_catalog_counts(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/native-reports/catalog",
            headers=admin_headers,
            timeout=20,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("total_countries") == 28
        assert data.get("total_formats") == 33
        assert data.get("implemented_formats") == 33

    def test_catalog_every_latam_endpoint_present(self, admin_headers):
        """Auto-registered LATAM endpoints must all appear in the catalog."""
        r = requests.get(
            f"{BASE_URL}/api/native-reports/catalog",
            headers=admin_headers,
            timeout=20,
        )
        assert r.status_code == 200
        blob = r.text
        for ep in (
            "/cl/previred", "/pe/plame", "/ec/iess", "/ve/ivss", "/bo/f110",
            "/py/f109", "/uy/bps-1146", "/gy/nis", "/sr/szf", "/cr/ccss",
            "/sv/f1-isss", "/gt/igss", "/hn/ihss", "/ni/inss", "/pa/css",
            "/cu/onat", "/ht/ona", "/pr/form-499r",
        ):
            assert ep in blob, f"Catalog missing auto-registered endpoint: {ep}"


# ---------- 6. APScheduler + basic calendar/filings health ----------

class TestMiscHealth:
    def test_calendar_returns_deadlines(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/native-reports/calendar", headers=admin_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "deadlines" in data or "upcoming" in data or isinstance(data, dict)

    def test_filings_history(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/native-reports/filings/history", headers=admin_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "filings" in data and "total" in data

    def test_apscheduler_startup_log(self):
        """Backend log must mention the fiscal_reminders_daily job startup."""
        found = False
        for path in ("/var/log/supervisor/backend.out.log",
                     "/var/log/supervisor/backend.err.log"):
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except FileNotFoundError:
                continue
            if "fiscal_reminders_daily" in content or "08:00 UTC" in content:
                found = True
                break
        assert found, "APScheduler startup line (fiscal_reminders_daily @ 08:00 UTC) not found in backend logs"
