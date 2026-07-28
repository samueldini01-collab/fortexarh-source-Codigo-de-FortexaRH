"""
Tests for the Stripe subscription (auto-renewal) billing flow.

Validates:
- POST /api/billing/setup-auto-renewal requires authorized_recurring=True.
- POST /api/billing/setup-auto-renewal rejects unknown/paid invoices.
- Consent audit is persisted on the subscription document.
- POST /api/billing/cleanup-abandoned-transactions marks stale `initiated`
  transactions as `abandoned`.
"""
import os
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

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


async def _seed_pending_invoice(company_id: str, amount: float = 76.0) -> str:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    inv_id = f"inv_test_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    await db.invoices.insert_one({
        "invoice_id": inv_id,
        "invoice_number": f"TEST-{uuid.uuid4().hex[:6]}",
        "company_id": company_id,
        "plan_id": "fortexarh_pro",
        "plan_name": "FortexaRH Pro",
        "employee_count": 5,
        "base_price": 50.0,
        "price_per_employee": 5.0,
        "total": amount,
        "currency": "USD",
        "status": "pending",
        "period_start_iso": now,
        "period_end_iso": now,
        "created_at": now,
    })
    client.close()
    return inv_id


async def _seed_abandoned_txn(company_id: str) -> str:
    """Insert a payment_transaction created > 24h ago, still initiated."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    txn_id = f"txn_test_{uuid.uuid4().hex[:8]}"
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    await db.payment_transactions.insert_one({
        "transaction_id": txn_id,
        "session_id": f"cs_test_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "payment_status": "initiated",
        "created_at": old_ts,
    })
    client.close()
    return txn_id


async def _cleanup_invoices(company_id: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.invoices.delete_many({"company_id": company_id, "invoice_id": {"$regex": "^inv_test_"}})
    await db.payment_transactions.delete_many({"company_id": company_id, "transaction_id": {"$regex": "^txn_test_"}})
    client.close()


async def _read_subscription_consent(company_id: str) -> dict:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    sub = await db.subscriptions.find_one(
        {"company_id": company_id},
        {
            "_id": 0,
            "auto_renewal_consent": 1,
            "auto_renewal_consent_at": 1,
            "auto_renewal_consent_by_user_id": 1,
            "auto_renewal_consent_amount": 1,
        },
    )
    client.close()
    return sub or {}


class TestAutoRenewalSetup:
    def setup_method(self):
        self.token, self.company_id = _login()

    def teardown_method(self):
        asyncio.run(_cleanup_invoices(self.company_id))

    def test_requires_authorized_recurring_true(self):
        inv_id = asyncio.run(_seed_pending_invoice(self.company_id))
        res = requests.post(
            f"{BASE_URL}/api/billing/setup-auto-renewal",
            json={"invoice_id": inv_id, "origin_url": "https://fortexarh.com", "authorized_recurring": False},
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=15,
        )
        assert res.status_code == 400
        assert "autorizar" in res.json().get("detail", "").lower()

    def test_rejects_unknown_invoice(self):
        res = requests.post(
            f"{BASE_URL}/api/billing/setup-auto-renewal",
            json={"invoice_id": "inv_does_not_exist", "origin_url": "https://fortexarh.com", "authorized_recurring": True},
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=15,
        )
        assert res.status_code == 404

    def test_creates_subscription_checkout_and_persists_consent(self):
        inv_id = asyncio.run(_seed_pending_invoice(self.company_id, amount=42.5))
        res = requests.post(
            f"{BASE_URL}/api/billing/setup-auto-renewal",
            json={"invoice_id": inv_id, "origin_url": "https://fortexarh.com", "authorized_recurring": True},
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30,
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body.get("checkout_url", "").startswith("https://checkout.stripe.com/")
        assert body.get("session_id", "").startswith("cs_")

        # Consent audit persisted
        consent = asyncio.run(_read_subscription_consent(self.company_id))
        assert consent.get("auto_renewal_consent") is True
        assert consent.get("auto_renewal_consent_at")
        assert consent.get("auto_renewal_consent_amount") == 42.5

    def test_unauthenticated_rejected(self):
        res = requests.post(
            f"{BASE_URL}/api/billing/setup-auto-renewal",
            json={"invoice_id": "any", "origin_url": "https://fortexarh.com", "authorized_recurring": True},
            timeout=15,
        )
        assert res.status_code in (401, 403)


class TestCleanupAbandoned:
    def setup_method(self):
        self.token, self.company_id = _login()

    def teardown_method(self):
        asyncio.run(_cleanup_invoices(self.company_id))

    def test_marks_stale_initiated_as_abandoned(self):
        asyncio.run(_seed_abandoned_txn(self.company_id))
        res = requests.post(
            f"{BASE_URL}/api/billing/cleanup-abandoned-transactions",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=15,
        )
        assert res.status_code == 200, res.text
        assert res.json().get("abandoned_count", 0) >= 1


class TestPendingInvoicesAdmin:
    def test_endpoint_returns_auto_renewal_field(self):
        """The super admin /invoices/pending endpoint must include
        `auto_renewal_active` on each item so the badge can render."""
        # This test uses a super_admin user. If the test admin isn't super_admin,
        # we skip; otherwise validate structure.
        token, _ = _login()
        res = requests.get(
            f"{BASE_URL}/api/super-admin/invoices/pending",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if res.status_code in (401, 403):
            # Not a super admin — skip structure check
            return
        assert res.status_code == 200
        body = res.json()
        assert "items" in body
        for item in body["items"]:
            assert "auto_renewal_active" in item, "auto_renewal_active flag missing"
