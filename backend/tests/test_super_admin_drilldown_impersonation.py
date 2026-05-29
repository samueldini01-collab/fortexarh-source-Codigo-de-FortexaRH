"""Tests for Super Admin drilldown, pending invoices, mark-paid, and impersonation.

Covers iteration 249 features:
 - GET  /api/super-admin/companies/{id}/detail
 - GET  /api/super-admin/invoices/pending
 - POST /api/super-admin/companies/{id}/invoices/mark-paid
 - POST /api/super-admin/companies/{id}/impersonate
"""
import os
import jwt
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://company-config-debug.preview.emergentagent.com").rstrip("/")
SA_USER = "fortexa2026rd"
SA_PASS = "FortexaAdmin2026!"


@pytest.fixture(scope="module")
def sa_token():
    r = requests.post(f"{BASE_URL}/api/super-admin/login", json={"username": SA_USER, "password": SA_PASS}, timeout=20)
    assert r.status_code == 200, f"SA login failed: {r.status_code} {r.text}"
    tok = r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def sa_headers(sa_token):
    return {"Authorization": f"Bearer {sa_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def first_company(sa_headers):
    r = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    # Endpoint may return list or {items:[..]}
    companies = data if isinstance(data, list) else data.get("items") or data.get("companies") or []
    assert companies, "no companies returned"
    return companies[0]


# ==================== Auth guard ====================

def test_impersonate_requires_sa_auth():
    r = requests.post(f"{BASE_URL}/api/super-admin/companies/anything/impersonate", json={}, timeout=15)
    assert r.status_code == 401


def test_detail_requires_sa_auth():
    r = requests.get(f"{BASE_URL}/api/super-admin/companies/anything/detail", timeout=15)
    assert r.status_code == 401


def test_invoices_pending_requires_sa_auth():
    r = requests.get(f"{BASE_URL}/api/super-admin/invoices/pending", timeout=15)
    assert r.status_code == 401


# ==================== Company detail ====================

def test_company_detail_returns_full_payload(sa_headers, first_company):
    cid = first_company.get("company_id") or first_company.get("id")
    r = requests.get(f"{BASE_URL}/api/super-admin/companies/{cid}/detail", headers=sa_headers, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("company", "subscription", "contact", "users", "transactions", "events"):
        assert key in body, f"missing key {key} in detail response"
    sub = body["subscription"]
    for key in ("plan_name", "monthly_billing"):
        assert key in sub, f"subscription missing {key}"
    # status / current_period_end may exist on saved sub
    assert isinstance(body["users"], list)
    assert isinstance(body["transactions"], list)
    assert isinstance(body["events"], list)


def test_company_detail_404_for_unknown(sa_headers):
    r = requests.get(f"{BASE_URL}/api/super-admin/companies/non_existent_xxx/detail", headers=sa_headers, timeout=15)
    assert r.status_code == 404


# ==================== Pending invoices ====================

def test_pending_invoices_shape(sa_headers):
    r = requests.get(f"{BASE_URL}/api/super-admin/invoices/pending", headers=sa_headers, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body and "count" in body and "total_amount" in body
    assert body["count"] == len(body["items"])
    for inv in body["items"]:
        for f in ("invoice_id", "company_id", "company_name", "plan_id", "amount", "currency", "period_end", "days_overdue", "severity", "status"):
            assert f in inv, f"invoice missing field {f}"
        assert inv["days_overdue"] > 0
        assert inv["severity"] in ("low", "medium", "high")
        assert inv["status"] == "past_due"


# ==================== Mark invoice paid ====================

def test_mark_paid_advances_period(sa_headers, first_company):
    cid = first_company.get("company_id") or first_company.get("id")
    # Snapshot before
    before = requests.get(f"{BASE_URL}/api/super-admin/companies/{cid}/detail", headers=sa_headers, timeout=15).json()
    prev_end = before.get("subscription", {}).get("current_period_end")

    r = requests.post(
        f"{BASE_URL}/api/super-admin/companies/{cid}/invoices/mark-paid",
        headers=sa_headers,
        json={"payment_method": "transferencia", "amount": 50.0, "notes": "TEST mark-paid"},
        timeout=20,
    )
    if r.status_code == 404:
        pytest.skip("Company has no subscription to mark paid")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "new_period_end" in body

    # Verify persisted
    after = requests.get(f"{BASE_URL}/api/super-admin/companies/{cid}/detail", headers=sa_headers, timeout=15).json()
    new_end = after.get("subscription", {}).get("current_period_end")
    assert new_end == body["new_period_end"]
    if prev_end:
        assert new_end != prev_end, "period_end did not change after mark-paid"

    # Verify transaction was inserted
    txs = after.get("transactions", [])
    assert any(t.get("notes") == "TEST mark-paid" or t.get("amount") == 50.0 for t in txs), "no payment_transactions record created"


# ==================== Impersonation ====================

def test_impersonate_returns_valid_jwt(sa_headers, first_company):
    cid = first_company.get("company_id") or first_company.get("id")
    r = requests.post(
        f"{BASE_URL}/api/super-admin/companies/{cid}/impersonate",
        headers=sa_headers,
        json={},
        timeout=20,
    )
    if r.status_code == 404:
        pytest.skip(f"Company {cid} has no users to impersonate")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "token" in body
    assert body.get("expires_in") == 3600
    user = body.get("user", {})
    assert user.get("support_session") is True
    assert user.get("company_id") == cid

    # Decode JWT (without verification) to confirm support_session claim
    decoded = jwt.decode(body["token"], options={"verify_signature": False})
    assert decoded.get("support_session") is True
    assert "exp" in decoded and "iat" in decoded
    # Window ~ 1h ± 60s
    assert 3500 < (decoded["exp"] - decoded["iat"]) < 3700


def test_impersonation_token_works_on_employees(sa_headers, first_company):
    cid = first_company.get("company_id") or first_company.get("id")
    r = requests.post(
        f"{BASE_URL}/api/super-admin/companies/{cid}/impersonate",
        headers=sa_headers,
        json={},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"impersonate failed: {r.status_code}")
    token = r.json()["token"]
    r2 = requests.get(
        f"{BASE_URL}/api/employees",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    assert r2.status_code == 200, f"GET /api/employees with impersonation token failed: {r2.status_code} {r2.text[:300]}"


def test_impersonate_404_when_company_missing(sa_headers):
    r = requests.post(
        f"{BASE_URL}/api/super-admin/companies/non_existent_xxx/impersonate",
        headers=sa_headers,
        json={},
        timeout=15,
    )
    assert r.status_code == 404
