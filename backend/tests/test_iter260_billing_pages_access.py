"""Iter260 — verify endpoints needed by /subscriptions & /billing-required pages
are reachable while the subscription is suspended (user must be able to pay /
change card)."""
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

PAGE_ENDPOINTS = [
    "/api/subscription",
    "/api/plans",
    "/api/invoices",
    "/api/payment-method/history",
    "/api/subscription/cancellation-info",
]


async def _set_status(company_id, status):
    c = AsyncIOMotorClient(MONGO_URL)
    await c[DB_NAME].subscriptions.update_one({"company_id": company_id}, {"$set": {"status": status}}, upsert=True)
    c.close()


@pytest.fixture(scope="module")
def admin():
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "test_refactor@fortexa.com", "password": "test123"}, timeout=20)
    assert res.status_code == 200, res.text
    d = res.json()
    return {"token": d["token"], "company_id": d["user"]["company_id"]}


@pytest.fixture(scope="module", autouse=True)
def restore(admin):
    yield
    asyncio.run(_set_status(admin["company_id"], "active"))


@pytest.mark.parametrize("path", PAGE_ENDPOINTS)
def test_subscription_page_endpoints_reachable_when_suspended(admin, path):
    asyncio.run(_set_status(admin["company_id"], "suspended"))
    res = requests.get(f"{BASE_URL}{path}", headers={"Authorization": f"Bearer {admin['token']}"}, timeout=25)
    assert res.status_code != 402, f"{path} blocked with 402 — user cannot pay/change card: {res.text[:200]}"


def test_checkout_post_reachable_when_suspended(admin):
    asyncio.run(_set_status(admin["company_id"], "suspended"))
    res = requests.post(
        f"{BASE_URL}/api/checkout",
        headers={"Authorization": f"Bearer {admin['token']}"},
        json={"plan_id": "basic", "billing_cycle": "monthly"},
        timeout=30,
    )
    assert res.status_code != 402, f"checkout blocked: {res.text[:200]}"
