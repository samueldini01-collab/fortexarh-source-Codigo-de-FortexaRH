"""
Tests for Employee Portal attendance with geofence enforcement.

Validates:
1. When the company has NO geo_locations → check-in/out works without GPS (back-compat).
2. When the company HAS geo_locations and employee has NO assignment → 403 strict block.
3. When the employee has an assignment and submits coords INSIDE radius → allowed.
4. When the employee has an assignment and submits coords OUTSIDE radius → 403 with distance.
5. When required and GPS is missing from the request → 403.
"""
import os
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
EMPLOYEE_DOCUMENT = "001-0000001-1"
EMPLOYEE_PASSWORD = "portal123"

# Synthetic test location coordinates (Santo Domingo center)
TEST_LAT = 18.4861
TEST_LON = -69.9312
TEST_RADIUS = 100  # meters
# A point roughly 5km away (clearly outside radius)
FAR_LAT = 18.5500
FAR_LON = -69.9800


def _admin_login():
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert res.status_code == 200, res.text
    return res.json()["token"], res.json().get("user", {}).get("company_id")


def _portal_login():
    res = requests.post(
        f"{BASE_URL}/api/employee-portal/login",
        json={"document_number": EMPLOYEE_DOCUMENT, "password": EMPLOYEE_PASSWORD},
        timeout=15,
    )
    assert res.status_code == 200, f"Portal login failed: {res.text}"
    body = res.json()
    return body["token"], body["employee"]["employee_id"]


def _find_admin_employee(admin_token, document_number):
    res = requests.get(
        f"{BASE_URL}/api/employees",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=15,
    )
    for emp in res.json():
        if emp.get("document_number") == document_number:
            return emp["employee_id"], emp.get("company_id")
    return None, None


async def _db():
    client = AsyncIOMotorClient(MONGO_URL)
    return client, client[DB_NAME]


async def _cleanup_company_geo(company_id: str):
    """Wipe geo_locations + employee_locations + today's attendance for the company."""
    client, db = await _db()
    today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")
    await db.geo_locations.delete_many({"company_id": company_id})
    await db.employee_locations.delete_many({"company_id": company_id})
    await db.attendances.delete_many({"company_id": company_id, "date": today})
    client.close()


async def _seed_location(company_id: str, name: str, lat: float, lon: float, radius: int):
    client, db = await _db()
    loc_id = f"loc_test_{__import__('uuid').uuid4().hex[:8]}"
    await db.geo_locations.insert_one({
        "location_id": loc_id,
        "company_id": company_id,
        "name": name,
        "address": "Test address",
        "latitude": lat,
        "longitude": lon,
        "radius": radius,
        "is_active": True,
    })
    client.close()
    return loc_id


async def _assign_employee_to_location(company_id: str, employee_id: str, location_id: str):
    client, db = await _db()
    await db.employee_locations.insert_one({
        "company_id": company_id,
        "employee_id": employee_id,
        "location_id": location_id,
    })
    client.close()


def _check_in(portal_token, body=None):
    return requests.post(
        f"{BASE_URL}/api/employee-portal/attendance/check-in",
        headers={"Authorization": f"Bearer {portal_token}"},
        json=body or {},
        timeout=15,
    )


def _cleanup_attendance_for_admin_company(company_id: str):
    async def _q():
        client, db = await _db()
        today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")
        await db.attendances.delete_many({"company_id": company_id, "date": today})
        client.close()
    asyncio.run(_q())


class TestGeofenceEnforcement:
    def setup_method(self):
        admin_token, _ = _admin_login()
        self.admin_token = admin_token
        emp_id, company_id = _find_admin_employee(admin_token, EMPLOYEE_DOCUMENT)
        assert emp_id and company_id
        self.employee_id = emp_id
        self.company_id = company_id
        # Clean slate per test
        asyncio.run(_cleanup_company_geo(self.company_id))

    def teardown_method(self):
        asyncio.run(_cleanup_company_geo(self.company_id))

    def test_no_geo_locations_allows_checkin_without_gps(self):
        """Back-compat: empresa sin geofence configurado → check-in funciona sin GPS."""
        portal_token, _ = _portal_login()
        res = _check_in(portal_token, {})
        assert res.status_code == 200, f"Should allow without geofence config, got {res.status_code}: {res.text}"
        assert res.json().get("check_in")

    def test_geo_required_no_gps_blocks(self):
        """Empresa con geofence + GPS missing → 403."""
        asyncio.run(_seed_location(self.company_id, "Oficina", TEST_LAT, TEST_LON, TEST_RADIUS))
        portal_token, _ = _portal_login()
        res = _check_in(portal_token, {})
        assert res.status_code == 403
        assert "geolocalización" in res.json().get("detail", "").lower() or "ubicación" in res.json().get("detail", "").lower()

    def test_geo_required_no_assignment_blocks(self):
        """Empresa con geofence, empleado sin asignación → 403 strict."""
        asyncio.run(_seed_location(self.company_id, "Oficina", TEST_LAT, TEST_LON, TEST_RADIUS))
        portal_token, _ = _portal_login()
        res = _check_in(portal_token, {"latitude": TEST_LAT, "longitude": TEST_LON, "accuracy": 10})
        assert res.status_code == 403
        assert "asignada" in res.json().get("detail", "").lower()

    def test_geo_inside_radius_allows(self):
        loc_id = asyncio.run(_seed_location(self.company_id, "Oficina", TEST_LAT, TEST_LON, TEST_RADIUS))
        asyncio.run(_assign_employee_to_location(self.company_id, self.employee_id, loc_id))
        portal_token, _ = _portal_login()
        # Same coords → distance ~0
        res = _check_in(portal_token, {"latitude": TEST_LAT, "longitude": TEST_LON, "accuracy": 5})
        assert res.status_code == 200, res.text
        body = res.json()
        assert body.get("location", {}).get("name") == "Oficina"
        assert body["location"]["distance_m"] < TEST_RADIUS

    def test_geo_outside_radius_blocks_with_distance(self):
        loc_id = asyncio.run(_seed_location(self.company_id, "Oficina", TEST_LAT, TEST_LON, TEST_RADIUS))
        asyncio.run(_assign_employee_to_location(self.company_id, self.employee_id, loc_id))
        portal_token, _ = _portal_login()
        # 5km away → outside 100m radius
        res = _check_in(portal_token, {"latitude": FAR_LAT, "longitude": FAR_LON, "accuracy": 10})
        assert res.status_code == 403, res.text
        detail = res.json().get("detail", "")
        assert "Oficina" in detail
        # Should mention meters
        assert "m" in detail


class TestAttendanceTodayGeofenceInfo:
    def test_today_endpoint_exposes_geofence_state(self):
        """The /attendance/today endpoint must expose geofence.required and assigned_locations."""
        admin_token, _ = _admin_login()
        _, company_id = _find_admin_employee(admin_token, EMPLOYEE_DOCUMENT)
        asyncio.run(_cleanup_company_geo(company_id))
        portal_token, _ = _portal_login()

        # Without geofence configured
        res = requests.get(
            f"{BASE_URL}/api/employee-portal/attendance/today",
            headers={"Authorization": f"Bearer {portal_token}"},
            timeout=15,
        )
        assert res.status_code == 200
        gf = res.json().get("geofence", {})
        assert gf.get("required") is False
        assert gf.get("assigned_locations") == []

        # With geofence + assignment
        loc_id = asyncio.run(_seed_location(company_id, "HQ", TEST_LAT, TEST_LON, TEST_RADIUS))
        emp_id, _ = _find_admin_employee(admin_token, EMPLOYEE_DOCUMENT)
        asyncio.run(_assign_employee_to_location(company_id, emp_id, loc_id))

        res2 = requests.get(
            f"{BASE_URL}/api/employee-portal/attendance/today",
            headers={"Authorization": f"Bearer {portal_token}"},
            timeout=15,
        )
        gf2 = res2.json().get("geofence", {})
        assert gf2.get("required") is True
        assert len(gf2.get("assigned_locations", [])) == 1
        assert gf2["assigned_locations"][0]["name"] == "HQ"

        asyncio.run(_cleanup_company_geo(company_id))
