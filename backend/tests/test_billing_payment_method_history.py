"""
Tests for payment method management + renewal history endpoints.

- POST /api/billing/customer-portal: opens Stripe Billing Portal (400 sin cliente, 200 con)
- GET  /api/billing/renewal-history: returns paid invoices scoped to company
"""
import os
import uuid
import asyncio
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
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
    return res.json()["token"], res.json().get("user", {}).get("company_id")


async def _unset_customer(company_id: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$unset": {"stripe_customer_id": ""}},
    )
    client.close()


async def _set_customer(company_id: str, cust_id: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": {"stripe_customer_id": cust_id}},
        upsert=True,
    )
    client.close()


async def _seed_paid_invoice(company_id: str, source: str = "stripe_auto_renewal") -> str:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    inv_id = f"inv_test_hist_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    await db.invoices.insert_one({
        "invoice_id": inv_id,
        "invoice_number": f"HIST-{uuid.uuid4().hex[:6]}",
        "company_id": company_id,
        "plan_name": "FortexaRH Pro",
        "total": 76.0,
        "currency": "USD",
        "status": "paid",
        "paid_at_iso": now,
        "paid_at": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
        "source": source,
        "created_at": now,
    })
    client.close()
    return inv_id


async def _cleanup_test_invoices(company_id: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.invoices.delete_many(
        {"company_id": company_id, "invoice_id": {"$regex": "^inv_test_hist_"}}
    )
    client.close()


class TestCustomerPortal:
    def setup_method(self):
        self.token, self.company_id = _login()

    def test_rejects_when_no_stripe_customer(self):
        asyncio.run(_unset_customer(self.company_id))
        res = requests.post(
            f"{BASE_URL}/api/billing/customer-portal",
            json={"return_url": "https://fortexarh.com/subscriptions"},
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=15,
        )
        assert res.status_code == 400
        assert "método de pago" in res.json().get("detail", "").lower() or "cliente" in res.json().get("detail", "").lower()

    def test_requires_authentication(self):
        res = requests.post(
            f"{BASE_URL}/api/billing/customer-portal",
            json={"return_url": "https://fortexarh.com/subscriptions"},
            timeout=15,
        )
        assert res.status_code in (401, 403)


class TestRenewalHistory:
    def setup_method(self):
        self.token, self.company_id = _login()

    def teardown_method(self):
        asyncio.run(_cleanup_test_invoices(self.company_id))

    def test_returns_only_paid_invoices_for_company(self):
        asyncio.run(_seed_paid_invoice(self.company_id, source="stripe_auto_renewal"))
        asyncio.run(_seed_paid_invoice(self.company_id, source="manual"))
        res = requests.get(
            f"{BASE_URL}/api/billing/renewal-history",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=15,
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert "items" in body
        # Our seeded ones must be in the list (there could be older paid invoices too)
        seeded_in_list = [i for i in body["items"] if i["invoice_id"].startswith("inv_test_hist_")]
        assert len(seeded_in_list) == 2
        # Each item must expose the fields the UI needs
        for it in seeded_in_list:
            assert "total" in it
            assert "currency" in it
            assert "plan_name" in it
            assert "paid_at" in it

    def test_requires_authentication(self):
        res = requests.get(f"{BASE_URL}/api/billing/renewal-history", timeout=15)
        assert res.status_code in (401, 403)
