"""Tests for pre-billing reminders (D-3 / D-1) and payment retry cron logic.

Covers:
- `send_billing_reminders`: D-3 / D-1 reminders are sent once (idempotent),
  update the correct tracking fields, and create in-app notifications.
- `retry_failed_payments`: increments failed_retry_count, marks slot done for
  idempotency, and after 3 failures marks the subscription as `suspended`.
- Successful retry marks subscription active and settles the pending invoice.

All Stripe calls and Resend calls are patched so no external I/O occurs.
"""
import sys
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, "/app/backend")


# Ensure a shared loop across tests so Motor stays bound to the same loop
_shared_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_shared_loop)


def run_async(coro):
    """Run coroutine on the shared loop (Motor client is bound to it)."""
    return _shared_loop.run_until_complete(coro)


# Import after loop is set so Motor picks up the shared loop
from config import db  # noqa: E402
from routes import billing_cycle  # noqa: E402


def _iso(d: datetime) -> str:
    return d.astimezone(timezone.utc).isoformat()


@pytest.fixture(autouse=True)
def _patch_env(monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_fake")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)


@pytest.fixture
def company_id():
    cid = f"comp_test_{uuid.uuid4().hex[:8]}"
    yield cid
    # cleanup
    run_async(db.subscriptions.delete_many({"company_id": cid}))
    run_async(db.invoices.delete_many({"company_id": cid}))
    run_async(db.notifications.delete_many({"company_id": cid}))
    run_async(db.users.delete_many({"company_id": cid}))
    run_async(db.companies.delete_many({"company_id": cid}))


async def _seed_active_subscription(company_id: str, period_end: datetime, plan_id: str = "fortexarh_pro"):
    await db.subscriptions.delete_many({"company_id": company_id})
    await db.subscriptions.insert_one({
        "company_id": company_id,
        "plan_id": plan_id,
        "plan_name": "FortexaRH Pro",
        "status": "active",
        "current_period_end": _iso(period_end),
        "currency": "USD",
        "created_at": _iso(datetime.now(timezone.utc)),
    })
    await db.companies.update_one(
        {"company_id": company_id},
        {"$set": {"company_id": company_id, "name": "Test Co", "company_name": "Test Co"}},
        upsert=True,
    )
    await db.users.update_one(
        {"company_id": company_id, "role": "admin"},
        {"$set": {
            "user_id": f"user_{company_id}",
            "company_id": company_id,
            "role": "admin",
            "email": f"admin_{company_id}@test.local",
            "name": "Admin Test",
        }},
        upsert=True,
    )


async def _seed_past_due_subscription(company_id: str, stripe_sub_id: str = None):
    now = datetime.now(timezone.utc)
    await db.subscriptions.delete_many({"company_id": company_id})
    doc = {
        "company_id": company_id,
        "plan_id": "fortexarh_pro",
        "plan_name": "FortexaRH Pro",
        "status": "past_due",
        "current_period_end": _iso(now - timedelta(days=2)),
        "past_due_since": _iso(now - timedelta(days=1)),
        "stripe_customer_id": "cus_fake_123",
        "currency": "USD",
        "created_at": _iso(now),
    }
    if stripe_sub_id:
        doc["stripe_subscription_id"] = stripe_sub_id
    await db.subscriptions.insert_one(doc)
    await db.companies.update_one(
        {"company_id": company_id},
        {"$set": {"company_id": company_id, "name": "Test Co", "company_name": "Test Co"}},
        upsert=True,
    )
    await db.users.update_one(
        {"company_id": company_id, "role": "admin"},
        {"$set": {
            "user_id": f"user_{company_id}",
            "company_id": company_id,
            "role": "admin",
            "email": f"admin_{company_id}@test.local",
            "name": "Admin Test",
        }},
        upsert=True,
    )
    await db.invoices.insert_one({
        "invoice_id": f"inv_{uuid.uuid4().hex[:8]}",
        "invoice_number": "FRH-TEST-001",
        "company_id": company_id,
        "plan_id": "fortexarh_pro",
        "plan_name": "FortexaRH Pro",
        "total": 50.0,
        "currency": "USD",
        "status": "pending",
        "created_at": _iso(now),
    })


def _make_stripe_module_mock(fail_all: bool = True, card_error: bool = True):
    """Return a MagicMock replacement for the `stripe` module used in retry code."""
    mod = MagicMock()

    import stripe as real_stripe
    mod.error = real_stripe.error

    mod.Customer.retrieve.return_value = {
        "invoice_settings": {"default_payment_method": "pm_test_1"},
    }

    pm_list = MagicMock()
    pm_list.data = [MagicMock(id="pm_test_1")]
    mod.PaymentMethod.list.return_value = pm_list

    inv_list = MagicMock()
    inv_list.data = []
    mod.Invoice.list.return_value = inv_list

    if fail_all:
        if card_error:
            mod.PaymentIntent.create.side_effect = real_stripe.error.CardError(
                message="Your card was declined.",
                param=None,
                code="card_declined",
            )
        else:
            intent = MagicMock(status="requires_payment_method", id="pi_x")
            mod.PaymentIntent.create.return_value = intent
    else:
        intent = MagicMock(status="succeeded", id="pi_ok_" + uuid.uuid4().hex[:6])
        mod.PaymentIntent.create.return_value = intent

    return mod


# ============ REMINDERS ============

class TestReminders:
    def test_d3_reminder_sends_once_and_marks_field(self, company_id):
        async def _run():
            now = datetime.now(timezone.utc)
            await _seed_active_subscription(company_id, now + timedelta(days=3, hours=6))
            with patch.object(billing_cycle, "_send_dunning_email", new=AsyncMock(return_value=True)):
                counts = await billing_cycle.send_billing_reminders()
            sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
            assert sub is not None
            assert sub.get("reminder_3d_sent_at"), "reminder_3d_sent_at should be persisted"
            assert sub.get("reminder_upcoming_at"), "legacy field also set"
            assert counts["pre_bill_3d"] >= 1
            # Idempotency
            with patch.object(billing_cycle, "_send_dunning_email", new=AsyncMock(return_value=True)) as mock_send:
                await billing_cycle.send_billing_reminders()
                sub2 = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
                assert sub2["reminder_3d_sent_at"] == sub["reminder_3d_sent_at"]
                calls_for_us = [c for c in mock_send.call_args_list if len(c.args) >= 2 and c.args[1] == company_id]
                assert len(calls_for_us) == 0
        run_async(_run())

    def test_d1_reminder_sends_once_and_marks_field(self, company_id):
        async def _run():
            now = datetime.now(timezone.utc)
            await _seed_active_subscription(company_id, now + timedelta(days=1))
            with patch.object(billing_cycle, "_send_dunning_email", new=AsyncMock(return_value=True)):
                counts = await billing_cycle.send_billing_reminders()
            sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
            assert sub.get("reminder_1d_sent_at"), "reminder_1d_sent_at should be persisted"
            assert counts["pre_bill_1d"] >= 1
            with patch.object(billing_cycle, "_send_dunning_email", new=AsyncMock(return_value=True)) as mock_send:
                await billing_cycle.send_billing_reminders()
                calls_for_us = [c for c in mock_send.call_args_list if len(c.args) >= 2 and c.args[1] == company_id]
                assert len(calls_for_us) == 0
        run_async(_run())

    def test_in_app_notification_created(self, company_id):
        async def _run():
            now = datetime.now(timezone.utc)
            await _seed_active_subscription(company_id, now + timedelta(days=3, hours=6))
            with patch.object(billing_cycle, "_send_dunning_email", new=AsyncMock(return_value=True)):
                await billing_cycle.send_billing_reminders()
            notif = await db.notifications.find_one(
                {"company_id": company_id, "type": "billing_reminder"},
                {"_id": 0},
            )
            assert notif is not None, "in-app notification should be created"
            assert notif.get("metadata", {}).get("kind") == "pre_bill_3d"
        run_async(_run())


# ============ RETRIES ============

class TestPaymentRetries:
    def test_single_failed_retry_bumps_count_but_does_not_suspend(self, company_id):
        async def _run():
            await _seed_past_due_subscription(company_id)
            with patch.object(billing_cycle, "stripe", _make_stripe_module_mock(fail_all=True)):
                stats = await billing_cycle.retry_failed_payments(current_slot=1)
            sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
            assert sub["status"] == "past_due"
            assert sub["failed_retry_count"] == 1
            assert sub.get("retry_slot_1_at")
            assert stats["failed"] >= 1
        run_async(_run())

    def test_slot_idempotency_same_day(self, company_id):
        async def _run():
            await _seed_past_due_subscription(company_id)
            with patch.object(billing_cycle, "stripe", _make_stripe_module_mock(fail_all=True)) as m:
                await billing_cycle.retry_failed_payments(current_slot=1)
                m.PaymentIntent.create.reset_mock()
                await billing_cycle.retry_failed_payments(current_slot=1)
                assert m.PaymentIntent.create.call_count == 0
            sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
            assert sub["failed_retry_count"] == 1
        run_async(_run())

    def test_three_failures_suspend_subscription(self, company_id):
        async def _run():
            await _seed_past_due_subscription(company_id)
            for slot in (1, 2, 3):
                with patch.object(billing_cycle, "stripe", _make_stripe_module_mock(fail_all=True)):
                    await billing_cycle.retry_failed_payments(current_slot=slot)
            sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
            assert sub["status"] == "suspended", f"expected suspended, got {sub['status']}"
            assert sub["failed_retry_count"] >= 3
            assert sub.get("suspended_at")
            assert sub.get("suspended_reason", "").startswith("3 intentos")
        run_async(_run())

    def test_successful_retry_reactivates_and_marks_invoice_paid(self, company_id):
        async def _run():
            await _seed_past_due_subscription(company_id)
            with patch.object(billing_cycle, "stripe", _make_stripe_module_mock(fail_all=False)):
                stats = await billing_cycle.retry_failed_payments(current_slot=1)
            sub = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
            assert sub["status"] == "active"
            assert sub["failed_retry_count"] == 0
            assert sub.get("past_due_since") is None
            assert stats["succeeded"] >= 1
            paid = await db.invoices.find_one(
                {"company_id": company_id, "status": "paid"}, {"_id": 0}
            )
            assert paid is not None
            assert paid.get("source") == "retry_cron"
            assert paid.get("receipt_number", "").startswith("RT-")
            still_pending = await db.invoices.find_one(
                {"company_id": company_id, "status": "pending"}, {"_id": 0}
            )
            assert still_pending is None
        run_async(_run())
