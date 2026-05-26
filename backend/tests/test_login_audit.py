"""
Backend tests for login audit + trusted devices + Google removal validation
Validates iteration testing for: /api/auth/login-history, /api/auth/trusted-devices
and login_history persistence + UserLogin.device_token field.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://company-config-debug.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data
    return data["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# Login flow: wrong password creates failure record
# ---------------------------------------------------------------------------
class TestLoginAttempts:
    def test_login_wrong_password_returns_401_and_logs(self, session, auth_headers):
        r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "WRONG_BAD_PASS_xyz"})
        assert r.status_code == 401, r.text
        # Verify it shows up in history
        time.sleep(0.3)
        h = session.get(f"{API}/auth/login-history", headers=auth_headers)
        assert h.status_code == 200, h.text
        items = h.json().get("items", [])
        # First item should be the latest failure
        fails = [i for i in items if i.get("success") is False and i.get("reason") == "invalid_credentials"]
        assert len(fails) >= 1, f"No invalid_credentials entry found: {items[:3]}"
        assert fails[0].get("method") == "password"

    def test_login_correct_creates_success_history(self, session, auth_headers):
        r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        assert "token" in r.json()
        time.sleep(0.3)
        h = session.get(f"{API}/auth/login-history", headers=auth_headers)
        assert h.status_code == 200
        items = h.json().get("items", [])
        successes = [i for i in items if i.get("success") is True]
        assert len(successes) >= 1
        latest = items[0]
        # Required keys
        for key in ("browser", "os", "ip", "city", "method", "success", "created_at", "email"):
            assert key in latest, f"Missing key {key} in {latest}"
        assert "_id" not in latest


# ---------------------------------------------------------------------------
# Login history endpoint
# ---------------------------------------------------------------------------
class TestLoginHistoryEndpoint:
    def test_login_history_requires_auth(self, session):
        r = session.get(f"{API}/auth/login-history")
        assert r.status_code in (401, 403)

    def test_login_history_shape_and_no_objectid(self, session, auth_headers):
        r = session.get(f"{API}/auth/login-history", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "count" in data
        assert isinstance(data["items"], list)
        assert data["count"] == len(data["items"])
        for item in data["items"]:
            assert "_id" not in item

    def test_login_history_sorted_desc(self, session, auth_headers):
        r = session.get(f"{API}/auth/login-history", headers=auth_headers)
        items = r.json()["items"]
        if len(items) >= 2:
            assert items[0]["created_at"] >= items[1]["created_at"]


# ---------------------------------------------------------------------------
# Trusted devices endpoints
# ---------------------------------------------------------------------------
class TestTrustedDevices:
    def test_list_trusted_devices_initial(self, session, auth_headers):
        r = session.get(f"{API}/auth/trusted-devices", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "count" in data
        # User without 2FA flow has no devices, but allow non-zero in case prior tests created some
        assert isinstance(data["items"], list)

    def test_delete_nonexistent_device_404(self, session, auth_headers):
        r = session.delete(f"{API}/auth/trusted-devices/nonexistent_device_xyz_123", headers=auth_headers)
        assert r.status_code == 404
        body = r.json()
        assert "detail" in body

    def test_revoke_all_devices_returns_count(self, session, auth_headers):
        r = session.delete(f"{API}/auth/trusted-devices", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert "revoked" in data
        assert isinstance(data["revoked"], int)

    def test_trusted_devices_requires_auth(self, session):
        r = session.get(f"{API}/auth/trusted-devices")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Login with bad device_token must NOT block login
# ---------------------------------------------------------------------------
class TestDeviceTokenAcceptedField:
    def test_login_with_bad_device_token_in_body(self, session):
        r = session.post(f"{API}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "device_token": "this_is_a_fake_token_should_be_ignored",
        })
        assert r.status_code == 200, r.text
        assert "token" in r.json()

    def test_login_with_bad_device_token_in_header(self, session):
        r = session.post(
            f"{API}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Device-Token": "fake_header_token", "Content-Type": "application/json"},
        )
        assert r.status_code == 200
        assert "token" in r.json()


# ---------------------------------------------------------------------------
# 2FA setup/status endpoints not broken by new imports
# ---------------------------------------------------------------------------
class Test2FAEndpointsStillWork:
    def test_2fa_status_works(self, session, auth_headers):
        r = session.get(f"{API}/auth/2fa/status", headers=auth_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "totp_enabled" in data

    def test_2fa_setup_endpoint_responds(self, session, auth_headers):
        # We just check the endpoint is reachable (200 or 400-class business error) not 500
        r = session.post(f"{API}/auth/2fa/setup", headers=auth_headers, json={})
        assert r.status_code != 500, f"2FA setup is broken: {r.text}"
        assert r.status_code < 500
