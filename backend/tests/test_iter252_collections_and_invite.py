"""
Iter 252 tests:
- POST /api/system-users triggers invite email (does not block on send)
- GET /api/super-admin/collections/dashboard (auth + structure)
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://company-config-debug.preview.emergentagent.com").rstrip("/")

SA_USER = "fortexa2026rd"
SA_PASS = "FortexaAdmin2026!"
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASS = "test123"


@pytest.fixture(scope="module")
def sa_token():
    r = requests.post(f"{BASE_URL}/api/super-admin/login", json={"username": SA_USER, "password": SA_PASS}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json().get("token") or r.json().get("access_token")


# ---------- Collections dashboard ----------

def test_collections_requires_auth():
    r = requests.get(f"{BASE_URL}/api/super-admin/collections/dashboard", timeout=30)
    assert r.status_code == 401


def test_collections_dashboard_default(sa_token):
    r = requests.get(
        f"{BASE_URL}/api/super-admin/collections/dashboard",
        headers={"Authorization": f"Bearer {sa_token}"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    for k in ["kpis", "aging_buckets", "daily_curve", "top_offenders", "window_days"]:
        assert k in data, f"missing top-level key {k}"
    kpis = data["kpis"]
    for k in [
        "outstanding_amount", "pending_count", "past_due_count", "suspended_count",
        "due_emails_sent", "due_emails_recovered", "recovery_rate_due",
        "final_emails_sent", "final_emails_recovered", "recovery_rate_final",
    ]:
        assert k in kpis, f"missing kpi {k}"
    assert isinstance(data["aging_buckets"], list) and len(data["aging_buckets"]) == 4
    keys = {b["key"] for b in data["aging_buckets"]}
    assert keys == {"0_7", "8_15", "16_30", "30_plus"}
    for b in data["aging_buckets"]:
        assert "label" in b and "count" in b and "amount" in b
    assert data["window_days"] == 90


@pytest.mark.parametrize("days", [7, 30, 180, 365])
def test_collections_dashboard_window(sa_token, days):
    r = requests.get(
        f"{BASE_URL}/api/super-admin/collections/dashboard?days={days}",
        headers={"Authorization": f"Bearer {sa_token}"},
        timeout=30,
    )
    assert r.status_code == 200
    assert r.json()["window_days"] == days


def test_collections_dashboard_clamps(sa_token):
    # below min clamps to 7
    r = requests.get(
        f"{BASE_URL}/api/super-admin/collections/dashboard?days=1",
        headers={"Authorization": f"Bearer {sa_token}"},
        timeout=30,
    )
    assert r.status_code == 200
    assert r.json()["window_days"] == 7
    # above max clamps to 365
    r = requests.get(
        f"{BASE_URL}/api/super-admin/collections/dashboard?days=9999",
        headers={"Authorization": f"Bearer {sa_token}"},
        timeout=30,
    )
    assert r.status_code == 200
    assert r.json()["window_days"] == 365


# ---------- Invitation email on user create ----------

def test_create_system_user_triggers_invite(admin_token):
    if not admin_token:
        pytest.skip("admin login failed")
    ts = int(time.time())
    email = f"invitee_test_iter252_{ts}@example.com"
    body = {
        "email": email,
        "name": "Invitee Test",
        "password": "TempPass123!",
        "role": "user",
        "modules": ["dashboard"],
        "is_active": True,
    }
    r = requests.post(
        f"{BASE_URL}/api/system-users",
        json=body,
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "user_id" in data
    user_id = data["user_id"]

    # Cleanup
    d = requests.delete(
        f"{BASE_URL}/api/system-users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=30,
    )
    assert d.status_code in (200, 204)
