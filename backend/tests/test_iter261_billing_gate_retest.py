"""Iter261 — Retest of P0 billing-gate fixes.

Covers:
 (1) /subscriptions-page endpoints must be reachable (no 402) for suspended & past_due
 (2) /api/billing/status is_blocked == True for past_due (and suspended)
 (3) business endpoints still 402 for suspended & past_due
 (4) active status restores full access (and DB is restored at teardown)
"""
import asyncio
import os

import pytest
import requests
from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or frontend_env["REACT_APP_BACKEND_URL"]).rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ALLOWED_ENDPOINTS = [
    "/api/subscription",
    "/api/plans",
    "/api/invoices",
    "/api/subscription/cancellation-info",
    "/api/billing/renewal-history",
    "/api/payment-method",
    "/api/payment-method/history",
    "/api/billing/status",
]

BLOCKED_ENDPOINTS = [
    "/api/employees",
    "/api/dashboard/stats",
    "/api/notifications",
    "/api/payroll/periods",
]

BLOCKED_STATUSES = ["suspended", "past_due"]


async def _set_status(company_id, status):
    c = AsyncIOMotorClient(MONGO_URL)
    await c[DB_NAME].subscriptions.update_one(
        {"company_id": company_id}, {"$set": {"status": status}}, upsert=True
    )
    doc = await c[DB_NAME].subscriptions.find_one({"company_id": company_id}, {"_id": 0, "status": 1})
    c.close()
    return doc


def set_status(company_id, status):
    doc = asyncio.run(_set_status(company_id, status))
    assert doc and doc["status"] == status
    return doc


@pytest.fixture(scope="module")
def admin():
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test_refactor@fortexa.com", "password": "test123"},
        timeout=30,
    )
    if res.status_code != 200:
        pytest.fail(f"admin login failed {res.status_code}: {res.text[:300]}")
    d = res.json()
    return {"token": d["token"], "company_id": d["user"]["company_id"], "headers": {"Authorization": f"Bearer {d['token']}"}}


@pytest.fixture(scope="module", autouse=True)
def restore_active(admin):
    yield
    doc = set_status(admin["company_id"], "active")
    print("restored subscription status:", doc)


# ---- (1) allowlisted endpoints reachable ----
@pytest.mark.parametrize("status", BLOCKED_STATUSES)
@pytest.mark.parametrize("path", ALLOWED_ENDPOINTS)
def test_subscription_page_endpoints_not_402(admin, status, path):
    set_status(admin["company_id"], status)
    res = requests.get(f"{BASE_URL}{path}", headers=admin["headers"], timeout=30)
    assert res.status_code != 402, f"[{status}] {path} blocked with 402: {res.text[:200]}"
    assert res.status_code < 500, f"[{status}] {path} server error {res.status_code}: {res.text[:200]}"


# ---- (2) billing/status is_blocked for past_due & suspended ----
@pytest.mark.parametrize("status", BLOCKED_STATUSES)
def test_billing_status_is_blocked_true(admin, status):
    set_status(admin["company_id"], status)
    res = requests.get(f"{BASE_URL}/api/billing/status", headers=admin["headers"], timeout=30)
    assert res.status_code == 200, res.text[:300]
    data = res.json()
    assert data["is_blocked"] is True, f"[{status}] is_blocked={data.get('is_blocked')} payload={data}"
    assert data["subscription_status"] == status


def test_billing_status_not_blocked_when_active(admin):
    set_status(admin["company_id"], "active")
    res = requests.get(f"{BASE_URL}/api/billing/status", headers=admin["headers"], timeout=30)
    assert res.status_code == 200, res.text[:300]
    data = res.json()
    assert data["is_blocked"] is False
    assert data["subscription_status"] == "active"


# ---- (3) business endpoints still blocked ----
@pytest.mark.parametrize("status", BLOCKED_STATUSES)
@pytest.mark.parametrize("path", BLOCKED_ENDPOINTS)
def test_business_endpoints_still_402(admin, status, path):
    set_status(admin["company_id"], status)
    res = requests.get(f"{BASE_URL}{path}", headers=admin["headers"], timeout=30)
    assert res.status_code == 402, f"[{status}] {path} expected 402, got {res.status_code}: {res.text[:200]}"
    body = res.json()
    assert body.get("billing_required") is True
    assert body.get("subscription_status") == status


# ---- (4) data content sanity for /subscriptions page while suspended ----
def test_subscriptions_page_payload_while_suspended(admin):
    set_status(admin["company_id"], "suspended")
    sub = requests.get(f"{BASE_URL}/api/subscription", headers=admin["headers"], timeout=30)
    assert sub.status_code == 200, sub.text[:300]
    sub_data = sub.json()
    assert "_id" not in sub_data, "raw Mongo _id leaked in /api/subscription"
    assert sub_data.get("status") == "suspended", f"subscription payload status={sub_data.get('status')}"

    plans = requests.get(f"{BASE_URL}/api/plans", headers=admin["headers"], timeout=30)
    assert plans.status_code == 200, plans.text[:300]
    plans_data = plans.json()
    items = plans_data if isinstance(plans_data, list) else plans_data.get("plans", [])
    assert len(items) > 0, f"no plans returned: {plans_data}"

    pm = requests.get(f"{BASE_URL}/api/payment-method", headers=admin["headers"], timeout=30)
    assert pm.status_code == 200, pm.text[:300]

    rh = requests.get(f"{BASE_URL}/api/billing/renewal-history", headers=admin["headers"], timeout=30)
    assert rh.status_code == 200, rh.text[:300]


def test_active_restores_business_access(admin):
    set_status(admin["company_id"], "active")
    res = requests.get(f"{BASE_URL}/api/employees", headers=admin["headers"], timeout=30)
    assert res.status_code == 200, f"expected 200 after restore, got {res.status_code}: {res.text[:200]}"
