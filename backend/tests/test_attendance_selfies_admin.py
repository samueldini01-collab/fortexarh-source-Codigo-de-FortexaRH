"""
Tests for the admin selfie serving endpoint:
  GET /api/attendance/selfies/{selfie_id}

Validates:
- Requires authentication.
- Returns 404 for unknown IDs.
- Streams image/jpeg bytes for a valid selfie belonging to admin's company.
- Enforces tenant isolation (selfie from another company → 404).
"""
import os
import base64
import uuid
import asyncio
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"

# 1x1 PNG (transparent) — valid base64 image payload
TINY_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def _admin_login():
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert res.status_code == 200, res.text
    return res.json()["token"], res.json().get("user", {}).get("company_id")


async def _seed_selfie(company_id: str, image_b64: str = TINY_B64) -> str:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    selfie_id = f"selfie_{uuid.uuid4().hex[:12]}"
    await db.attendance_selfies.insert_one({
        "selfie_id": selfie_id,
        "company_id": company_id,
        "employee_id": "emp_test_selfie",
        "mark_type": "entry",
        "image_data": image_b64,
        "source": "employee_portal",
    })
    client.close()
    return selfie_id


async def _delete_selfies(company_id: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.attendance_selfies.delete_many({"company_id": company_id, "employee_id": "emp_test_selfie"})
    client.close()


class TestAttendanceSelfieServing:
    def setup_method(self):
        self.admin_token, self.company_id = _admin_login()
        # Ensure clean slate
        asyncio.run(_delete_selfies(self.company_id))

    def teardown_method(self):
        asyncio.run(_delete_selfies(self.company_id))
        # Also clean anything left behind under any other company scoped to this test
        async def _q():
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            await db.attendance_selfies.delete_many({"employee_id": "emp_test_selfie"})
            client.close()
        asyncio.run(_q())

    def test_requires_authentication(self):
        selfie_id = asyncio.run(_seed_selfie(self.company_id))
        res = requests.get(f"{BASE_URL}/api/attendance/selfies/{selfie_id}", timeout=15)
        assert res.status_code in (401, 403)

    def test_returns_image_bytes_for_own_company(self):
        selfie_id = asyncio.run(_seed_selfie(self.company_id))
        res = requests.get(
            f"{BASE_URL}/api/attendance/selfies/{selfie_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            timeout=15,
        )
        assert res.status_code == 200, res.text
        assert res.headers.get("content-type", "").startswith("image/")
        # Verify bytes match decoded payload
        expected = base64.b64decode(TINY_B64)
        assert res.content == expected

    def test_returns_404_for_unknown_id(self):
        res = requests.get(
            f"{BASE_URL}/api/attendance/selfies/selfie_does_not_exist",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            timeout=15,
        )
        assert res.status_code == 404

    def test_tenant_isolation(self):
        """A selfie belonging to another company must not be served."""
        other_selfie = asyncio.run(_seed_selfie("comp_other_tenant_xyz"))
        try:
            res = requests.get(
                f"{BASE_URL}/api/attendance/selfies/{other_selfie}",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                timeout=15,
            )
            assert res.status_code == 404
        finally:
            async def _q():
                client = AsyncIOMotorClient(MONGO_URL)
                db = client[DB_NAME]
                await db.attendance_selfies.delete_many({"selfie_id": other_selfie})
                client.close()
            asyncio.run(_q())
