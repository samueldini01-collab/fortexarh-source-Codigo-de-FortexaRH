"""
Iteration 260 — BillingGateMiddleware end-to-end verification.

Covers:
- suspended / past_due block business endpoints with 402 + billing_required
- allowlisted billing/payment endpoints stay reachable while blocked
- unauthenticated requests are NOT converted to 402 (auth layer still 401/403)
- flipping status back to active unblocks
- super_admin is never blocked
"""
import asyncio
import os

import pytest
import requests
from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL missing"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
SA_USER = "fortexa2026rd"
SA_PASS = "FortexaAdmin2026!"

BUSINESS_PATHS = ["/api/employees", "/api/dashboard/stats", "/api/payroll/periods"]
ALLOWED_GET_PATHS = [
    "/api/billing/status",
    "/api/billing/renewal-history",
    "/api/payment-method",
    "/api/health",
]


def _login(email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=20)
    return res


async def _set_status(company_id, status):
    client = AsyncIOMotorClient(MONGO_URL)
    await client[DB_NAME].subscriptions.update_one({"company_id": company_id}, {"$set": {"status": status}}, upsert=True)
    client.close()


async def _get_status(company_id):
    client = AsyncIOMotorClient(MONGO_URL)
    sub = await client[DB_NAME].subscriptions.find_one({"company_id": company_id}, {"_id": 0, "status": 1})
    client.close()
    return (sub or {}).get("status")


@pytest.fixture(scope="module")
def admin():
    res = _login()
    assert res.status_code == 200, f"admin login failed {res.status_code}: {res.text[:300]}"
    data = res.json()
    user = data.get("user", {})
    assert user.get("role") != "super_admin"
    return {"token": data["token"], "company_id": user.get("company_id"), "user": user}


@pytest.fixture(scope="module", autouse=True)
def restore(admin):
    original = asyncio.run(_get_status(admin["company_id"])) or "active"
    yield
    asyncio.run(_set_status(admin["company_id"], "active"))
    print(f"\n[cleanup] restored status to active (original was {original})")


def _get(path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.get(f"{BASE_URL}{path}", headers=headers, timeout=25)


class TestBillingGate:
    @pytest.mark.parametrize("status", ["suspended", "past_due"])
    def test_blocked_statuses_return_402(self, admin, status):
        asyncio.run(_set_status(admin["company_id"], status))
        for path in BUSINESS_PATHS:
            res = _get(path, admin["token"])
            assert res.status_code == 402, f"{path} status={status} -> {res.status_code}: {res.text[:200]}"
            body = res.json()
            assert body.get("billing_required") is True
            assert body.get("subscription_status") == status
            assert isinstance(body.get("detail"), str) and body["detail"]

    @pytest.mark.parametrize("status", ["suspended", "past_due"])
    def test_allowlisted_gets_not_blocked(self, admin, status):
        asyncio.run(_set_status(admin["company_id"], status))
        for path in ALLOWED_GET_PATHS:
            res = _get(path, admin["token"])
            assert res.status_code != 402, f"{path} must not be blocked -> {res.status_code}: {res.text[:200]}"
            assert res.status_code < 500, f"{path} server error {res.status_code}: {res.text[:200]}"

    def test_allowlisted_posts_not_blocked(self, admin):
        asyncio.run(_set_status(admin["company_id"], "suspended"))
        h = {"Authorization": f"Bearer {admin['token']}"}
        res = requests.post(
            f"{BASE_URL}/api/billing/setup-auto-renewal",
            headers=h,
            json={"enabled": True},
            timeout=25,
        )
        assert res.status_code != 402, f"setup-auto-renewal blocked: {res.text[:300]}"
        res2 = requests.post(f"{BASE_URL}/api/billing/customer-portal", headers=h, json={}, timeout=25)
        assert res2.status_code != 402, f"customer-portal blocked: {res2.text[:300]}"

    def test_login_and_health_work_when_blocked(self, admin):
        asyncio.run(_set_status(admin["company_id"], "suspended"))
        assert _login().status_code == 200
        assert _get("/api/health").status_code == 200

    def test_unauthenticated_request_not_402(self, admin):
        asyncio.run(_set_status(admin["company_id"], "suspended"))
        res = _get("/api/employees")
        assert res.status_code in (401, 403), f"expected 401/403 got {res.status_code}: {res.text[:200]}"

    def test_invalid_token_not_402(self, admin):
        asyncio.run(_set_status(admin["company_id"], "suspended"))
        res = _get("/api/employees", token="not.a.valid.jwt")
        assert res.status_code in (401, 403), f"expected 401/403 got {res.status_code}"

    def test_active_unblocks(self, admin):
        asyncio.run(_set_status(admin["company_id"], "suspended"))
        assert _get("/api/employees", admin["token"]).status_code == 402
        asyncio.run(_set_status(admin["company_id"], "active"))
        res = _get("/api/employees", admin["token"])
        assert res.status_code == 200, f"active company blocked: {res.status_code} {res.text[:200]}"
        assert isinstance(res.json(), (list, dict))

    def test_super_admin_exempt(self, admin):
        asyncio.run(_set_status(admin["company_id"], "suspended"))
        sa = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={"username": SA_USER, "password": SA_PASS},
            timeout=20,
        )
        assert sa.status_code == 200, f"super admin login failed {sa.status_code}: {sa.text[:300]}"
        token = sa.json()["token"]
        for path in ("/api/super-admin/companies", "/api/super-admin/stats"):
            res = _get(path, token)
            assert res.status_code != 402, f"super admin blocked on {path}: {res.text[:200]}"
