"""
Tests for the BillingGateMiddleware.

Given a company with subscription status in {"suspended", "past_due"}:
- Requests to arbitrary API endpoints (e.g. /api/employees, /api/dashboard,
  /api/payroll) MUST return 402 Payment Required with billing_required=True.
- Requests to allowlisted paths remain accessible so the user can pay:
    /api/auth/*, /api/billing/*, /api/checkout*, /api/webhook/*,
    /api/payment-method*, /api/create-setup-intent, /api/health.

When the status returns to "active", all endpoints work again.
"""
import asyncio
import os

import requests
from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

_frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL") or _frontend_env.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL missing from env and /app/frontend/.env"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"


def _login():
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert res.status_code == 200, res.text
    return res.json()["token"], res.json().get("user", {}).get("company_id"), res.json().get("user", {}).get("role")


async def _set_subscription_status(company_id: str, status: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": {"status": status}},
        upsert=True,
    )
    client.close()


async def _get_subscription_status(company_id: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0, "status": 1})
    client.close()
    return (sub or {}).get("status")


def _get(path: str, token: str):
    return requests.get(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )


class TestBillingGate:
    def setup_method(self):
        self.token, self.company_id, self.role = _login()
        assert self.role != "super_admin", "This test needs a regular company admin — super admin is exempt from the gate"
        # Snapshot original status to restore later
        self.original_status = asyncio.run(_get_subscription_status(self.company_id))

    def teardown_method(self):
        # Restore original status so we don't leave the company blocked
        target = self.original_status or "active"
        asyncio.run(_set_subscription_status(self.company_id, target))

    def test_active_status_does_not_block_normal_endpoints(self):
        asyncio.run(_set_subscription_status(self.company_id, "active"))
        # /api/employees should NOT be blocked by the gate (200 or 4xx from route, but never 402)
        res = _get("/api/employees", self.token)
        assert res.status_code != 402, f"Active company must not be blocked. Got {res.status_code}: {res.text[:200]}"

    def test_suspended_blocks_arbitrary_endpoints_with_402(self):
        asyncio.run(_set_subscription_status(self.company_id, "suspended"))
        for path in ("/api/employees", "/api/dashboard/stats", "/api/payroll/periods"):
            res = _get(path, self.token)
            assert res.status_code == 402, f"{path} should be blocked. Got {res.status_code}: {res.text[:200]}"
            body = res.json()
            assert body.get("billing_required") is True
            assert body.get("subscription_status") == "suspended"

    def test_past_due_blocks_arbitrary_endpoints_with_402(self):
        asyncio.run(_set_subscription_status(self.company_id, "past_due"))
        res = _get("/api/employees", self.token)
        assert res.status_code == 402
        assert res.json().get("subscription_status") == "past_due"

    def test_allowlist_paths_pass_when_blocked(self):
        asyncio.run(_set_subscription_status(self.company_id, "suspended"))
        allowed = [
            "/api/billing/status",
            "/api/billing/renewal-history",
            "/api/payment-method",
            "/api/health",
        ]
        for path in allowed:
            res = _get(path, self.token)
            assert res.status_code != 402, f"{path} must NOT be blocked. Got {res.status_code}: {res.text[:200]}"

    def test_auth_login_works_when_blocked(self):
        asyncio.run(_set_subscription_status(self.company_id, "suspended"))
        # Login is on /api/auth/login — must always be accessible
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15,
        )
        assert res.status_code == 200, f"Login must always work. Got {res.status_code}: {res.text[:200]}"

    def test_missing_token_is_not_blocked_by_gate(self):
        """Without credentials, request should reach the auth layer (401), not
        be short-circuited by the billing gate to 402."""
        asyncio.run(_set_subscription_status(self.company_id, "suspended"))
        res = requests.get(f"{BASE_URL}/api/employees", timeout=15)
        assert res.status_code != 402, "Gate must not respond 402 for unauthenticated requests"
        assert res.status_code in (401, 403)

    def test_status_change_to_active_unblocks(self):
        asyncio.run(_set_subscription_status(self.company_id, "suspended"))
        res_blocked = _get("/api/employees", self.token)
        assert res_blocked.status_code == 402

        asyncio.run(_set_subscription_status(self.company_id, "active"))
        res_ok = _get("/api/employees", self.token)
        assert res_ok.status_code != 402
