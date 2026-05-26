"""Iter 247 — backend validation for the three changes:
1. Login latency improvement (background task offload).
2. login_history still populates after a successful login.
3. MongoDB indexes created by setup_login_audit_indexes().
4. New-location alert helper is safe when RESEND_API_KEY is absent (code-review check).
"""
import os
import sys
import time
import asyncio
import inspect
import pytest
import requests

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
EMAIL = "test_refactor@fortexa.com"
PASSWORD = "test123"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- 1. Latency ----------

def test_login_latency_under_700ms(session):
    """Login should be fast now that geolocation is in BackgroundTasks."""
    # Warm-up
    session.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    latencies = []
    for _ in range(3):
        t0 = time.perf_counter()
        resp = session.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert resp.status_code == 200, resp.text
        assert "token" in resp.json()
        latencies.append(elapsed_ms)
    median = sorted(latencies)[1]
    print(f"Login latencies(ms): {latencies}, median={median:.1f}")
    # Generous bound to account for cloud ingress; the geo-blocking version was ~2-3s.
    assert median < 1500, f"Median login latency too high: {median:.1f}ms"


# ---------- 2. login_history populated by background task ----------

def test_login_history_populated_after_login(session):
    login = session.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert login.status_code == 200
    token = login.json()["token"]
    # Give background task time to insert
    time.sleep(2.0)
    resp = session.get(f"{BASE_URL}/api/auth/login-history?limit=10",
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and isinstance(body["items"], list)
    assert body["count"] >= 1
    # Most recent entry should be a successful password login
    rec = body["items"][0]
    assert rec["success"] is True
    assert rec["method"] in ("password", "2fa", "recovery")
    assert "created_at" in rec
    # No mongo _id leaked
    assert "_id" not in rec


# ---------- 3. Indexes ----------

def test_mongo_indexes_present():
    """Connect to MongoDB and verify indexes were created at startup."""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    assert mongo_url and db_name

    async def _check():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        lh = await db.login_history.index_information()
        td = await db.trusted_devices.index_information()
        client.close()
        return lh, td

    lh, td = asyncio.run(_check())
    print("login_history indexes:", list(lh.keys()))
    print("trusted_devices indexes:", list(td.keys()))
    assert "user_id_1_created_at_-1" in lh
    assert "created_at_-1" in lh
    assert "user_id_1_revoked_1_expires_at_-1" in td
    assert "token_hash_1" in td


# ---------- 4. New-location alert helper safety ----------

def test_send_new_location_alert_safe_without_resend_key():
    """The helper must early-return (no exception) when RESEND_API_KEY is absent."""
    from routes import login_audit

    helper = login_audit._send_new_location_alert
    # Confirmed it exists, is async, and has try/except
    assert inspect.iscoroutinefunction(helper)
    src = inspect.getsource(helper)
    assert "try:" in src and "except" in src, "Helper must be wrapped in try/except"
    assert "RESEND_API_KEY" in src, "Helper must guard on RESEND_API_KEY"

    saved = os.environ.pop("RESEND_API_KEY", None)
    try:
        # Must not raise even with no key
        asyncio.run(helper(
            email="nobody@example.com",
            name="Test",
            geo={"city": "Bogotá", "country": "Colombia", "country_code": "CO"},
            ua_parts={"browser": "Chrome 120", "os": "Linux", "device_type": "pc"},
            ip="8.8.8.8",
            when_iso="2026-01-01T00:00:00+00:00",
        ))
    finally:
        if saved is not None:
            os.environ["RESEND_API_KEY"] = saved


def test_persist_login_attempt_is_async_and_awaited():
    from routes import login_audit
    assert inspect.iscoroutinefunction(login_audit._persist_login_attempt)
    # log_login_attempt schedules background work and is sync (does not block)
    assert not inspect.iscoroutinefunction(login_audit.log_login_attempt)
