"""Iteration 251 — Billing cycle subscription module tests.

Covers:
- GET  /api/billing/status (auth required, pending invoice data, suspension)
- POST /api/billing/pay-pending (Stripe Checkout creation + txn record + 404 path)
- run_billing_cycle() cron: generation + idempotency
- suspend_overdue_subscriptions() cron after GRACE_DAYS
- /api/invoices includes pending invoice
- Webhook code path reads transaction.invoice_id (DB inspection on
  payment_transactions doc created by /pay-pending)
"""
import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta

import pytest
import requests

# Allow importing backend modules to drive crons directly
sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
API = f"{BASE_URL}/api"
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
TEST_COMPANY_ID = "comp_7bf9f34ab85e"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="session")
def headers(token):
    assert token, "no token"
    return {"Authorization": f"Bearer {token}"}


# ---------- billing/status ----------
class TestBillingStatus:
    def test_status_requires_auth(self):
        r = requests.get(f"{API}/billing/status", timeout=15)
        assert r.status_code in (401, 403)

    def test_status_returns_pending_invoice(self, headers):
        r = requests.get(f"{API}/billing/status", headers=headers, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("has_pending") is True
        inv = d.get("pending_invoice")
        assert inv is not None, "pending_invoice missing"
        for f in ("invoice_id", "invoice_number", "plan_id", "plan_name",
                  "employee_count", "base_price", "price_per_employee",
                  "subtotal", "total", "period_start", "period_end", "status"):
            assert f in inv, f"missing {f}"
        assert inv["status"] == "pending"
        assert d.get("subscription_status") in ("past_due", "suspended")
        assert "grace_days_left" in d
        assert "current_period_end" in d


# ---------- /api/invoices includes pending ----------
class TestInvoicesListing:
    def test_invoices_contains_pending(self, headers):
        r = requests.get(f"{API}/invoices", headers=headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        invoices = data if isinstance(data, list) else data.get("invoices", [])
        pendings = [i for i in invoices if i.get("status") == "pending"]
        assert pendings, "no pending invoices returned by /api/invoices"


# ---------- billing/pay-pending ----------
class TestPayPending:
    def test_pay_pending_404_for_unknown_invoice(self, headers):
        r = requests.post(
            f"{API}/billing/pay-pending",
            headers=headers,
            json={"invoice_id": "inv_does_not_exist_xxx", "origin_url": BASE_URL},
            timeout=20,
        )
        assert r.status_code == 404, r.text

    def test_pay_pending_creates_checkout_session(self, headers):
        s = requests.get(f"{API}/billing/status", headers=headers, timeout=15).json()
        invoice_id = s["pending_invoice"]["invoice_id"]
        r = requests.post(
            f"{API}/billing/pay-pending",
            headers=headers,
            json={"invoice_id": invoice_id, "origin_url": BASE_URL},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "checkout_url" in d and "session_id" in d
        assert d["checkout_url"].startswith("https://checkout.stripe.com"), d["checkout_url"]

        # Verify a payment_transactions row was created carrying the invoice_id
        from config import db
        async def _check():
            doc = await db.payment_transactions.find_one(
                {"session_id": d["session_id"]}, {"_id": 0}
            )
            return doc
        doc = asyncio.get_event_loop().run_until_complete(_check())
        assert doc is not None, "payment_transactions row not inserted"
        assert doc.get("invoice_id") == invoice_id
        assert doc.get("payment_status") == "initiated"


# ---------- cron: run_billing_cycle (idempotency + generation) ----------
class TestCronBillingCycle:
    def test_run_billing_cycle_idempotent(self):
        from routes.billing_cycle import run_billing_cycle
        from config import db

        async def _go():
            before = await db.invoices.count_documents({
                "company_id": TEST_COMPANY_ID, "status": "pending"
            })
            r1 = await run_billing_cycle()
            after1 = await db.invoices.count_documents({
                "company_id": TEST_COMPANY_ID, "status": "pending"
            })
            r2 = await run_billing_cycle()
            after2 = await db.invoices.count_documents({
                "company_id": TEST_COMPANY_ID, "status": "pending"
            })
            return before, r1, after1, r2, after2

        before, r1, after1, r2, after2 = asyncio.get_event_loop().run_until_complete(_go())
        # second run should not create additional pending invoices for same period
        assert after2 == after1, f"cron not idempotent: {after1} -> {after2}"
        assert isinstance(r1.get("invoices_created"), int)
        assert isinstance(r2.get("invoices_created"), int)


# ---------- cron: suspend_overdue_subscriptions ----------
class TestCronSuspend:
    def test_suspends_after_grace_days(self):
        from routes.billing_cycle import suspend_overdue_subscriptions, GRACE_DAYS
        from config import db

        async def _go():
            # Backdate past_due_since beyond grace
            old = (datetime.now(timezone.utc) - timedelta(days=GRACE_DAYS + 2)).isoformat()
            await db.subscriptions.update_one(
                {"company_id": TEST_COMPANY_ID},
                {"$set": {"status": "past_due", "past_due_since": old}},
            )
            n = await suspend_overdue_subscriptions()
            sub = await db.subscriptions.find_one(
                {"company_id": TEST_COMPANY_ID}, {"_id": 0, "status": 1, "suspended_at": 1}
            )
            # restore to past_due so subsequent UI tests behave as expected
            await db.subscriptions.update_one(
                {"company_id": TEST_COMPANY_ID},
                {"$set": {"status": "past_due", "past_due_since": datetime.now(timezone.utc).isoformat()},
                 "$unset": {"suspended_at": ""}},
            )
            return n, sub

        n, sub = asyncio.get_event_loop().run_until_complete(_go())
        assert sub is not None
        assert sub.get("status") == "suspended", f"expected suspended, got {sub.get('status')}"
        assert sub.get("suspended_at"), "suspended_at not set"


# ---------- Webhook/checkout-status integration: ensure invoice_id is on txn ----------
class TestCheckoutStatusIntegrationContract:
    def test_payment_transaction_has_invoice_id_for_webhook_lookup(self, headers):
        s = requests.get(f"{API}/billing/status", headers=headers, timeout=15).json()
        invoice_id = s["pending_invoice"]["invoice_id"]
        r = requests.post(
            f"{API}/billing/pay-pending",
            headers=headers,
            json={"invoice_id": invoice_id, "origin_url": BASE_URL},
            timeout=30,
        )
        assert r.status_code == 200
        session_id = r.json()["session_id"]

        from config import db
        async def _fetch():
            return await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        doc = asyncio.get_event_loop().run_until_complete(_fetch())
        assert doc and doc.get("invoice_id") == invoice_id, (
            "checkout.py webhook depends on transaction.invoice_id to advance "
            "the subscription period; missing field"
        )
