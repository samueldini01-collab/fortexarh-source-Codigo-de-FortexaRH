"""Tests for PATCH /api/employees/{employee_id}/bank-info endpoint (iter 254).

The endpoint is used by the ACH dialog drill-down so the admin can fix a single
employee's bank data without sending the full employee payload.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASS = "test123"


@pytest.fixture(scope="module")
def auth_token():
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=20,
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code} {resp.text}")
    return resp.json().get("access_token") or resp.json().get("token")


@pytest.fixture(scope="module")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def some_employee(headers):
    resp = requests.get(f"{BASE_URL}/api/employees", headers=headers, timeout=20)
    assert resp.status_code == 200, resp.text
    emps = resp.json()
    assert isinstance(emps, list) and len(emps) > 0, "No employees found for admin company"
    return emps[0]


# Snapshot original then restore at end of module
@pytest.fixture(scope="module")
def original_bank(headers, some_employee):
    eid = some_employee["employee_id"]
    resp = requests.get(f"{BASE_URL}/api/employees/{eid}", headers=headers, timeout=20)
    assert resp.status_code == 200
    data = resp.json()
    snapshot = {
        "bank_name": data.get("bank_name") or "",
        "account_number": data.get("account_number") or "",
        "account_type": data.get("account_type") or "CC",
    }
    yield snapshot
    # restore
    requests.patch(
        f"{BASE_URL}/api/employees/{eid}/bank-info",
        json=snapshot,
        headers=headers,
        timeout=20,
    )


class TestBankInfoPatch:
    def test_patch_updates_only_account_number(self, headers, some_employee, original_bank):
        eid = some_employee["employee_id"]
        new_account = "TEST9988776655"
        resp = requests.patch(
            f"{BASE_URL}/api/employees/{eid}/bank-info",
            json={"account_number": new_account},
            headers=headers,
            timeout=20,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("updated", {}).get("account_number") == new_account
        # Verify via GET
        g = requests.get(f"{BASE_URL}/api/employees/{eid}", headers=headers, timeout=20)
        assert g.status_code == 200
        assert g.json().get("account_number") == new_account
        # bank_name preserved
        assert g.json().get("bank_name") == original_bank["bank_name"]

    def test_patch_all_three_fields(self, headers, some_employee):
        eid = some_employee["employee_id"]
        payload = {
            "bank_name": "Banreservas",
            "account_number": "TEST1122334455",
            "account_type": "CA",
        }
        resp = requests.patch(
            f"{BASE_URL}/api/employees/{eid}/bank-info",
            json=payload,
            headers=headers,
            timeout=20,
        )
        assert resp.status_code == 200, resp.text
        g = requests.get(f"{BASE_URL}/api/employees/{eid}", headers=headers, timeout=20)
        data = g.json()
        assert data["bank_name"] == "Banreservas"
        assert data["account_number"] == "TEST1122334455"
        assert data["account_type"] == "CA"

    def test_empty_body_returns_400(self, headers, some_employee):
        eid = some_employee["employee_id"]
        resp = requests.patch(
            f"{BASE_URL}/api/employees/{eid}/bank-info",
            json={},
            headers=headers,
            timeout=20,
        )
        assert resp.status_code == 400, resp.text

    def test_unknown_employee_returns_404(self, headers):
        resp = requests.patch(
            f"{BASE_URL}/api/employees/EMP_DOES_NOT_EXIST_xyz/bank-info",
            json={"bank_name": "Banreservas"},
            headers=headers,
            timeout=20,
        )
        assert resp.status_code == 404, resp.text

    def test_unauthenticated_rejected(self, some_employee):
        eid = some_employee["employee_id"]
        resp = requests.patch(
            f"{BASE_URL}/api/employees/{eid}/bank-info",
            json={"bank_name": "Banreservas"},
            timeout=20,
        )
        assert resp.status_code in (401, 403), resp.text


class TestAchPreviewIntegration:
    """Validate that after clearing account_number the employee shows up in ACH preview's missing list, and after PATCHing it disappears."""

    def test_clear_then_fix_account(self, headers, some_employee, original_bank):
        eid = some_employee["employee_id"]
        # 1. clear account_number
        r = requests.patch(
            f"{BASE_URL}/api/employees/{eid}/bank-info",
            json={"account_number": ""},
            headers=headers,
            timeout=20,
        )
        assert r.status_code == 200, r.text

        # 2. find an approved/paid period — try iter253's known period
        period_id = "period_42a51c051530"
        # 3. call ACH preview
        prev = requests.get(
            f"{BASE_URL}/api/bank-files/preview/{period_id}/banreservas",
            headers=headers,
            timeout=30,
        )
        if prev.status_code != 200:
            pytest.skip(f"ach-preview not available for {period_id}: {prev.status_code} {prev.text[:200]}")
        data = prev.json()
        # employee should appear in missing list (only if it is actually in this period)
        missing_ids = [m.get("employee_id") for m in data.get("missing", [])]
        in_missing = eid in missing_ids
        if not in_missing:
            # if employee is not part of that period, skip the rest meaningfully
            pytest.skip(f"Employee {eid} not part of period {period_id}; ready={data.get('ready_count')} missing={data.get('missing_count')}")

        # 4. fix account
        r2 = requests.patch(
            f"{BASE_URL}/api/employees/{eid}/bank-info",
            json={"account_number": "TEST5050505050", "bank_name": "Banreservas", "account_type": "CC"},
            headers=headers,
            timeout=20,
        )
        assert r2.status_code == 200

        # 5. preview should no longer show this employee in missing
        prev2 = requests.get(
            f"{BASE_URL}/api/bank-files/preview/{period_id}/banreservas",
            headers=headers,
            timeout=30,
        )
        assert prev2.status_code == 200
        d2 = prev2.json()
        assert eid not in [m.get("employee_id") for m in d2.get("missing", [])], "Employee still in missing after PATCH"
