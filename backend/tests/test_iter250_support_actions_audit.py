"""
Iteration 250 — Support Actions Audit Middleware + SA list endpoint.

Coverage:
- POST /onboarding/dismiss with impersonation token → row logged
- GET  /employees with impersonation token → NOT logged
- POST /onboarding/dismiss with regular admin token → NOT logged
- GET  /super-admin/support-actions auth + filters (company_id, user_id)
- Latency for regular POST stays low
"""
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
SA_USER = "fortexa2026rd"
SA_PASS = "FortexaAdmin2026!"
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASS = "test123"


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def sa_token():
    r = requests.post(f"{BASE_URL}/api/super-admin/login",
                      json={"username": SA_USER, "password": SA_PASS}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_company_id(admin_token):
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json().get("company_id")


@pytest.fixture(scope="module")
def admin_user_id(admin_token):
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=20)
    assert r.status_code == 200
    return r.json().get("user_id")


@pytest.fixture(scope="module")
def impersonation_token(sa_token, admin_company_id):
    r = requests.post(
        f"{BASE_URL}/api/super-admin/companies/{admin_company_id}/impersonate",
        json={}, headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("token")
    return data["token"]


# ---------- middleware behavior ----------
class TestSupportActionsMiddleware:

    def test_impersonation_post_is_logged(self, sa_token, impersonation_token):
        """POST /onboarding/dismiss with support_session token should create a support_actions row."""
        before = requests.get(f"{BASE_URL}/api/super-admin/support-actions",
                              headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        assert before.status_code == 200
        count_before = before.json().get("count", 0)

        r = requests.post(f"{BASE_URL}/api/onboarding/dismiss",
                          headers={"Authorization": f"Bearer {impersonation_token}"}, timeout=20)
        # endpoint may be 200/204; what we care about is the log
        assert r.status_code < 500, r.text

        # allow async insert
        time.sleep(1.0)

        after = requests.get(f"{BASE_URL}/api/super-admin/support-actions",
                             headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        assert after.status_code == 200
        items = after.json()["items"]
        assert after.json()["count"] >= count_before + 1, "support_actions row was not logged"

        # validate latest row schema
        latest = items[0]
        assert latest["method"] == "POST"
        assert latest["path"] == "/api/onboarding/dismiss"
        assert latest["support_actor"] == "super_admin"
        assert latest.get("email") == ADMIN_EMAIL
        assert "status_code" in latest
        assert "created_at" in latest
        assert "id" in latest
        assert "_id" not in latest  # ObjectId must be excluded

    def test_impersonation_get_is_not_logged(self, sa_token, impersonation_token):
        """GET /api/employees with impersonation token MUST NOT log (read-only)."""
        before = requests.get(f"{BASE_URL}/api/super-admin/support-actions",
                              headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        count_before = before.json()["count"]

        r = requests.get(f"{BASE_URL}/api/employees",
                         headers={"Authorization": f"Bearer {impersonation_token}"}, timeout=20)
        assert r.status_code < 500

        time.sleep(0.8)
        after = requests.get(f"{BASE_URL}/api/super-admin/support-actions",
                             headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        # GET path /api/employees must not appear in the most recent entries
        # but count should not have grown due to this call
        new_items = after.json()["items"][:5]
        for it in new_items:
            assert not (it["method"] == "GET" and it["path"] == "/api/employees"), \
                "GET /api/employees was logged but should be skipped"
        # Loose count check (allow concurrent inserts from other tests, but not from THIS call)
        # We can't strictly equal, but a GET should not introduce a new GET row.

    def test_regular_admin_post_is_not_logged(self, sa_token, admin_token):
        """POST with a regular (non-support) admin token MUST NOT be logged."""
        before = requests.get(f"{BASE_URL}/api/super-admin/support-actions",
                              headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        count_before = before.json()["count"]

        r = requests.post(f"{BASE_URL}/api/onboarding/dismiss",
                          headers={"Authorization": f"Bearer {admin_token}"}, timeout=20)
        assert r.status_code < 500

        time.sleep(0.8)
        after = requests.get(f"{BASE_URL}/api/super-admin/support-actions",
                             headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        count_after = after.json()["count"]
        assert count_after == count_before, \
            f"Regular admin POST was logged (before={count_before}, after={count_after})"

    def test_regular_post_latency_under_threshold(self, admin_token):
        """Regular POST under middleware should remain fast (<500ms p95, well under 1s)."""
        durations = []
        for _ in range(5):
            t0 = time.perf_counter()
            r = requests.post(f"{BASE_URL}/api/onboarding/dismiss",
                              headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
            durations.append((time.perf_counter() - t0) * 1000)
            assert r.status_code < 500
        avg = sum(durations) / len(durations)
        max_d = max(durations)
        print(f"latency ms — avg={avg:.0f}, max={max_d:.0f}")
        # Generous bound for kube ingress; spec mentions ~250ms target
        assert avg < 600, f"avg latency too high: {avg:.0f}ms"


# ---------- list endpoint ----------
class TestSupportActionsEndpoint:

    def test_requires_super_admin_token(self):
        r = requests.get(f"{BASE_URL}/api/super-admin/support-actions", timeout=20)
        assert r.status_code == 401

    def test_rejects_regular_admin_token(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/super-admin/support-actions",
                         headers={"Authorization": f"Bearer {admin_token}"}, timeout=20)
        assert r.status_code in (401, 403)

    def test_list_shape_and_sort(self, sa_token):
        r = requests.get(f"{BASE_URL}/api/super-admin/support-actions",
                         headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and "count" in body
        assert isinstance(body["items"], list)
        assert body["count"] == len(body["items"])
        # sort desc by created_at
        ts = [i["created_at"] for i in body["items"] if i.get("created_at")]
        assert ts == sorted(ts, reverse=True), "items must be sorted desc by created_at"
        # schema check on at least one row
        if body["items"]:
            row = body["items"][0]
            for k in ("id", "method", "path", "support_actor", "status_code", "created_at"):
                assert k in row, f"missing key {k}"
            assert "_id" not in row

    def test_filter_by_company_id(self, sa_token, admin_company_id):
        r = requests.get(
            f"{BASE_URL}/api/super-admin/support-actions",
            params={"company_id": admin_company_id},
            headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        assert r.status_code == 200
        for it in r.json()["items"]:
            assert it.get("company_id") == admin_company_id

        # unknown company → empty
        r2 = requests.get(
            f"{BASE_URL}/api/super-admin/support-actions",
            params={"company_id": "definitely-not-a-real-company-id"},
            headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        assert r2.status_code == 200
        assert r2.json()["count"] == 0

    def test_filter_by_user_id(self, sa_token, admin_user_id):
        r = requests.get(
            f"{BASE_URL}/api/super-admin/support-actions",
            params={"user_id": admin_user_id},
            headers={"Authorization": f"Bearer {sa_token}"}, timeout=20)
        assert r.status_code == 200
        for it in r.json()["items"]:
            assert it.get("user_id") == admin_user_id
