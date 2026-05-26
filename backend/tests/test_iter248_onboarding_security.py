"""
Iteration 248 — Validate:
  1) notification-preferences: new event `new_location_login` under `security` category
  2) onboarding: GET /checklist, POST /dismiss, POST /restore
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = {"email": "test_refactor@fortexa.com", "password": "test123"}


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def H(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- Notification Preferences ----------
class TestNotificationPreferences:
    def test_events_includes_new_location_login(self, H):
        r = requests.get(f"{BASE_URL}/api/notification-preferences/events", headers=H, timeout=15)
        assert r.status_code == 200
        body = r.json()
        events = body["events"]
        cats = body["categories"]
        assert "new_location_login" in events, f"missing event. Keys: {list(events.keys())}"
        ev = events["new_location_login"]
        assert ev["category"] == "security"
        assert ev["default"] == {"in_app": True, "email": True, "push": False}
        assert "security" in cats
        assert cats["security"]["label"] == "Seguridad"

    def test_get_prefs(self, H):
        r = requests.get(f"{BASE_URL}/api/notification-preferences", headers=H, timeout=15)
        assert r.status_code == 200
        assert "events" in r.json() or "user_id" in r.json()

    def test_put_prefs_with_new_event(self, H):
        # First fetch existing to merge
        cur = requests.get(f"{BASE_URL}/api/notification-preferences", headers=H, timeout=15).json()
        events = cur.get("events") or {}
        events["new_location_login"] = {"in_app": True, "email": False, "push": False}
        r = requests.put(
            f"{BASE_URL}/api/notification-preferences",
            json={"events": events},
            headers=H, timeout=15,
        )
        assert r.status_code == 200
        # verify persist
        cur2 = requests.get(f"{BASE_URL}/api/notification-preferences", headers=H, timeout=15).json()
        assert cur2["events"]["new_location_login"]["email"] is False
        # restore default
        events["new_location_login"] = {"in_app": True, "email": True, "push": False}
        requests.put(f"{BASE_URL}/api/notification-preferences", json={"events": events}, headers=H, timeout=15)


# ---------- Onboarding ----------
class TestOnboarding:
    def test_restore_then_checklist(self, H):
        # ensure not dismissed
        r = requests.post(f"{BASE_URL}/api/onboarding/restore", headers=H, timeout=15)
        assert r.status_code == 200
        assert r.json()["dismissed"] is False

        r = requests.get(f"{BASE_URL}/api/onboarding/checklist", headers=H, timeout=15)
        assert r.status_code == 200
        data = r.json()
        for k in ("steps", "completed", "total", "progress", "all_done", "dismissed"):
            assert k in data
        assert data["dismissed"] is False
        assert data["total"] == 6
        keys = [s["key"] for s in data["steps"]]
        assert keys == ["company", "employees", "payroll", "bank", "users", "security"]
        for s in data["steps"]:
            for f in ("done", "detail", "title", "description", "cta", "route", "icon"):
                assert f in s, f"step {s.get('key')} missing {f}"
            assert isinstance(s["done"], bool)
        # admin has 6 employees, 8 payroll periods, 2 users → expect not all done (security pending)
        sec = next(s for s in data["steps"] if s["key"] == "security")
        # We don't assert sec["done"]==False (could have been enabled); just ensure consistency
        assert data["progress"] == round(data["completed"] * 100 / data["total"])

    def test_dismiss_and_restore(self, H):
        r = requests.post(f"{BASE_URL}/api/onboarding/dismiss", headers=H, timeout=15)
        assert r.status_code == 200
        assert r.json()["dismissed"] is True

        r = requests.get(f"{BASE_URL}/api/onboarding/checklist", headers=H, timeout=15)
        assert r.status_code == 200
        assert r.json()["dismissed"] is True

        r = requests.post(f"{BASE_URL}/api/onboarding/restore", headers=H, timeout=15)
        assert r.status_code == 200
        assert r.json()["dismissed"] is False

        r = requests.get(f"{BASE_URL}/api/onboarding/checklist", headers=H, timeout=15)
        assert r.json()["dismissed"] is False

    def test_unauthorized(self):
        r = requests.get(f"{BASE_URL}/api/onboarding/checklist", timeout=15)
        assert r.status_code in (401, 403)
