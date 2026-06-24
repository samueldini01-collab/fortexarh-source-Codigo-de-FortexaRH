"""
Tests for admin-initiated Employee Portal password reset.

Flow under test:
1. Admin logs in with company tenant credentials.
2. Admin calls POST /api/employees/{employee_id}/reset-portal-password.
3. The endpoint returns the document_number as temporary_password.
4. The stored bcrypt hash matches the employee's document_number.
5. Endpoint requires auth and rejects unknown employees.
"""
import os
import asyncio
import bcrypt
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
EMPLOYEE_DOCUMENT = "001-0000001-1"


def _admin_login():
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    return res.json()["token"]


def _find_employee_for_admin(admin_token, document_number):
    res = requests.get(
        f"{BASE_URL}/api/employees",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=15,
    )
    assert res.status_code == 200, f"Get employees failed: {res.text}"
    for emp in res.json():
        if emp.get("document_number") == document_number:
            return emp["employee_id"], emp.get("company_id")
    return None, None


def _get_stored_password_hash(employee_id, company_id):
    async def _q():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        emp = await db.employees.find_one(
            {"employee_id": employee_id, "company_id": company_id},
            {"_id": 0, "portal_password": 1, "portal_enabled": 1, "portal_password_reset_at": 1},
        )
        client.close()
        return emp

    return asyncio.run(_q())


class TestPortalPasswordReset:
    def test_admin_can_reset_employee_portal_password(self):
        token = _admin_login()
        employee_id, company_id = _find_employee_for_admin(token, EMPLOYEE_DOCUMENT)
        assert employee_id, f"Test employee {EMPLOYEE_DOCUMENT} not found for admin"

        reset_res = requests.post(
            f"{BASE_URL}/api/employees/{employee_id}/reset-portal-password",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert reset_res.status_code == 200, f"Reset failed: {reset_res.text}"
        payload = reset_res.json()
        assert payload.get("temporary_password") == EMPLOYEE_DOCUMENT
        assert payload.get("employee_id") == employee_id
        assert "reset_at" in payload
        assert payload.get("message")

        # Validate DB state: portal_enabled True and stored hash matches the document number
        stored = _get_stored_password_hash(employee_id, company_id)
        assert stored is not None, "Employee not found in DB after reset"
        assert stored.get("portal_enabled") is True
        assert stored.get("portal_password_reset_at"), "reset_at timestamp not persisted"
        assert bcrypt.checkpw(
            EMPLOYEE_DOCUMENT.encode(),
            stored["portal_password"].encode(),
        ), "Stored hash does not verify against document_number"

    def test_reset_requires_authentication(self):
        res = requests.post(
            f"{BASE_URL}/api/employees/any-id/reset-portal-password",
            timeout=15,
        )
        assert res.status_code in (401, 403)

    def test_reset_rejects_unknown_employee(self):
        token = _admin_login()
        res = requests.post(
            f"{BASE_URL}/api/employees/nonexistent-employee-xyz/reset-portal-password",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert res.status_code == 404
