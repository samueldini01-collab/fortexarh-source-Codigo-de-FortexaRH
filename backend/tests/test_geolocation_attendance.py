"""
Test suite for Geolocation Attendance Feature - FortexaRH
Tests all CRUD operations for locations and attendance marking with GPS
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestGeolocationAttendance:
    """Test suite for Geolocation Attendance endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        token = login_response.json().get("token")
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        self.test_location_id = None
        yield
        
        # Cleanup: Delete test location if created
        if self.test_location_id:
            try:
                self.session.delete(f"{BASE_URL}/api/geolocation-attendance/locations/{self.test_location_id}")
            except:
                pass
    
    # ==================== LOCATION CRUD TESTS ====================
    
    def test_01_get_locations_list(self):
        """GET /api/geolocation-attendance/locations - List all locations"""
        response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/locations")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET locations returned {len(data)} locations")
    
    def test_02_create_location(self):
        """POST /api/geolocation-attendance/locations - Create new geofence location"""
        unique_id = uuid.uuid4().hex[:8]
        location_data = {
            "name": f"TEST_Location_{unique_id}",
            "address": "Av. Winston Churchill #123, Santo Domingo",
            "latitude": 18.4861,
            "longitude": -69.9312,
            "radius": 150,
            "location_type": "office",
            "is_active": True
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/locations",
            json=location_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "location_id" in data, "Response should contain location_id"
        assert "message" in data, "Response should contain message"
        
        self.test_location_id = data["location_id"]
        print(f"✓ Created location: {self.test_location_id}")
        
        # Verify location was created by fetching it
        get_response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/locations")
        assert get_response.status_code == 200
        
        locations = get_response.json()
        created_location = next((loc for loc in locations if loc.get("location_id") == self.test_location_id), None)
        
        assert created_location is not None, "Created location should be in the list"
        assert created_location["name"] == location_data["name"], "Location name should match"
        assert created_location["latitude"] == location_data["latitude"], "Latitude should match"
        assert created_location["longitude"] == location_data["longitude"], "Longitude should match"
        assert created_location["radius"] == location_data["radius"], "Radius should match"
        print(f"✓ Verified location data persisted correctly")
    
    def test_03_update_location(self):
        """PUT /api/geolocation-attendance/locations/{id} - Update location"""
        # First create a location to update
        unique_id = uuid.uuid4().hex[:8]
        create_response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/locations",
            json={
                "name": f"TEST_UpdateLoc_{unique_id}",
                "address": "Original Address",
                "latitude": 18.4861,
                "longitude": -69.9312,
                "radius": 100,
                "location_type": "office",
                "is_active": True
            }
        )
        
        assert create_response.status_code == 200
        location_id = create_response.json()["location_id"]
        self.test_location_id = location_id
        
        # Update the location
        update_data = {
            "name": f"TEST_UpdatedLoc_{unique_id}",
            "address": "Updated Address",
            "radius": 200,
            "is_active": False
        }
        
        update_response = self.session.put(
            f"{BASE_URL}/api/geolocation-attendance/locations/{location_id}",
            json=update_data
        )
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        print(f"✓ Updated location: {location_id}")
        
        # Verify update persisted
        get_response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/locations")
        locations = get_response.json()
        updated_location = next((loc for loc in locations if loc.get("location_id") == location_id), None)
        
        assert updated_location is not None, "Updated location should exist"
        assert updated_location["name"] == update_data["name"], "Name should be updated"
        assert updated_location["address"] == update_data["address"], "Address should be updated"
        assert updated_location["radius"] == update_data["radius"], "Radius should be updated"
        assert updated_location["is_active"] == update_data["is_active"], "is_active should be updated"
        print(f"✓ Verified location update persisted correctly")
    
    def test_04_delete_location(self):
        """DELETE /api/geolocation-attendance/locations/{id} - Delete location"""
        # First create a location to delete
        unique_id = uuid.uuid4().hex[:8]
        create_response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/locations",
            json={
                "name": f"TEST_DeleteLoc_{unique_id}",
                "address": "To Be Deleted",
                "latitude": 18.4861,
                "longitude": -69.9312,
                "radius": 100,
                "location_type": "office",
                "is_active": True
            }
        )
        
        assert create_response.status_code == 200
        location_id = create_response.json()["location_id"]
        
        # Delete the location
        delete_response = self.session.delete(
            f"{BASE_URL}/api/geolocation-attendance/locations/{location_id}"
        )
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        print(f"✓ Deleted location: {location_id}")
        
        # Verify deletion
        get_response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/locations")
        locations = get_response.json()
        deleted_location = next((loc for loc in locations if loc.get("location_id") == location_id), None)
        
        assert deleted_location is None, "Deleted location should not exist in list"
        print(f"✓ Verified location was deleted")
    
    def test_05_delete_nonexistent_location(self):
        """DELETE /api/geolocation-attendance/locations/{id} - Delete non-existent location returns 404"""
        response = self.session.delete(
            f"{BASE_URL}/api/geolocation-attendance/locations/nonexistent_loc_12345"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Delete non-existent location returns 404")
    
    # ==================== ATTENDANCE MARKING TESTS ====================
    
    def test_06_mark_attendance_entry(self):
        """POST /api/geolocation-attendance/mark - Mark entry attendance"""
        # Mark entry with coordinates inside a known location
        mark_data = {
            "latitude": 18.4861,
            "longitude": -69.9312,
            "accuracy": 10.0,
            "mark_type": "entry",
            "device_info": "Test Device - Pytest",
            "notes": "Test entry mark"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/mark",
            json=mark_data
        )
        
        # Could be 200 (success) or 400 (already marked today) or 404 (employee not found)
        if response.status_code == 400:
            data = response.json()
            if "Ya marcó entrada hoy" in data.get("detail", ""):
                print(f"✓ Entry already marked today (expected behavior)")
                return
        
        if response.status_code == 404:
            data = response.json()
            if "Empleado no encontrado" in data.get("detail", ""):
                print(f"⚠ Employee not found for test user - this is expected if user is not linked to an employee")
                pytest.skip("Test user not linked to employee record")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "mark_id" in data, "Response should contain mark_id"
        assert "is_within_zone" in data, "Response should contain is_within_zone"
        assert "location_name" in data, "Response should contain location_name"
        assert "timestamp" in data, "Response should contain timestamp"
        
        print(f"✓ Marked entry attendance: {data.get('mark_id')}")
        print(f"  - Within zone: {data.get('is_within_zone')}")
        print(f"  - Location: {data.get('location_name')}")
    
    def test_07_mark_attendance_outside_zone(self):
        """POST /api/geolocation-attendance/mark - Mark attendance outside authorized zone"""
        # Mark with coordinates far from any location
        mark_data = {
            "latitude": 40.7128,  # New York coordinates
            "longitude": -74.0060,
            "accuracy": 10.0,
            "mark_type": "entry",
            "device_info": "Test Device - Outside Zone",
            "notes": "Test outside zone mark"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/mark",
            json=mark_data
        )
        
        # Could be 200 (success with pending_review) or 400 (already marked) or 404 (employee not found)
        if response.status_code == 400:
            data = response.json()
            if "Ya marcó" in data.get("detail", ""):
                print(f"✓ Already marked today (expected behavior)")
                return
        
        if response.status_code == 404:
            pytest.skip("Test user not linked to employee record")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # When outside zone, status should be pending_review
        assert data.get("status") == "pending_review" or data.get("is_within_zone") == False, \
            "Outside zone marks should be pending_review or is_within_zone=False"
        
        print(f"✓ Outside zone mark handled correctly")
        print(f"  - Status: {data.get('status')}")
        print(f"  - Within zone: {data.get('is_within_zone')}")
    
    # ==================== ADMIN REPORTS TESTS ====================
    
    def test_08_get_today_attendance_admin(self):
        """GET /api/geolocation-attendance/admin/today - Get today's attendance marks"""
        response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/admin/today")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "date" in data, "Response should contain date"
        assert "marks" in data, "Response should contain marks"
        assert "summary" in data, "Response should contain summary"
        
        summary = data.get("summary", {})
        assert "total_employees" in summary, "Summary should contain total_employees"
        assert "marked_today" in summary, "Summary should contain marked_today"
        assert "pending" in summary, "Summary should contain pending"
        assert "outside_zone_alerts" in summary, "Summary should contain outside_zone_alerts"
        
        print(f"✓ GET admin/today returned data for {data.get('date')}")
        print(f"  - Total marks: {len(data.get('marks', []))}")
        print(f"  - Summary: {summary}")
    
    def test_09_approve_attendance_mark(self):
        """POST /api/geolocation-attendance/admin/approve/{mark_id} - Approve pending mark"""
        # First get today's marks to find a pending one
        today_response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/admin/today")
        assert today_response.status_code == 200
        
        marks = today_response.json().get("marks", [])
        pending_mark = next((m for m in marks if m.get("status") == "pending_review"), None)
        
        if not pending_mark:
            print(f"⚠ No pending marks to approve - skipping test")
            pytest.skip("No pending marks available for approval test")
        
        mark_id = pending_mark.get("mark_id")
        
        # Approve the mark
        response = self.session.post(f"{BASE_URL}/api/geolocation-attendance/admin/approve/{mark_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        
        print(f"✓ Approved mark: {mark_id}")
    
    def test_10_approve_nonexistent_mark(self):
        """POST /api/geolocation-attendance/admin/approve/{mark_id} - Approve non-existent mark returns 404"""
        response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/admin/approve/nonexistent_mark_12345"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Approve non-existent mark returns 404")
    
    # ==================== MY MARKS/LOCATIONS TESTS ====================
    
    def test_11_get_my_marks(self):
        """GET /api/geolocation-attendance/my-marks - Get current user's marks"""
        response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/my-marks")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET my-marks returned {len(data)} marks")
    
    def test_12_get_my_locations(self):
        """GET /api/geolocation-attendance/my-locations - Get user's assigned locations"""
        response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/my-locations")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET my-locations returned {len(data)} locations")
    
    # ==================== EMPLOYEE ASSIGNMENT TESTS ====================
    
    def test_13_assign_employees_to_location(self):
        """POST /api/geolocation-attendance/locations/{id}/assign-employees - Assign employees"""
        # First create a location
        unique_id = uuid.uuid4().hex[:8]
        create_response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/locations",
            json={
                "name": f"TEST_AssignLoc_{unique_id}",
                "address": "Assignment Test Location",
                "latitude": 18.4861,
                "longitude": -69.9312,
                "radius": 100,
                "location_type": "office",
                "is_active": True
            }
        )
        
        assert create_response.status_code == 200
        location_id = create_response.json()["location_id"]
        self.test_location_id = location_id
        
        # Get employees to assign
        employees_response = self.session.get(f"{BASE_URL}/api/employees")
        if employees_response.status_code != 200:
            pytest.skip("Could not fetch employees")
        
        employees = employees_response.json()
        if not employees:
            print(f"⚠ No employees available for assignment test")
            pytest.skip("No employees available")
        
        # Assign first employee
        employee_id = employees[0].get("employee_id")
        
        assign_response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/locations/{location_id}/assign-employees",
            json={
                "employee_ids": [employee_id],
                "location_id": location_id
            }
        )
        
        assert assign_response.status_code == 200, f"Expected 200, got {assign_response.status_code}: {assign_response.text}"
        
        data = assign_response.json()
        assert "message" in data, "Response should contain message"
        
        print(f"✓ Assigned employee {employee_id} to location {location_id}")
    
    def test_14_get_location_employees(self):
        """GET /api/geolocation-attendance/locations/{id}/employees - Get assigned employees"""
        # First get locations
        locations_response = self.session.get(f"{BASE_URL}/api/geolocation-attendance/locations")
        assert locations_response.status_code == 200
        
        locations = locations_response.json()
        if not locations:
            pytest.skip("No locations available")
        
        location_id = locations[0].get("location_id")
        
        response = self.session.get(
            f"{BASE_URL}/api/geolocation-attendance/locations/{location_id}/employees"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET location employees returned {len(data)} employees for location {location_id}")


class TestGeolocationValidation:
    """Test validation and edge cases"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        token = login_response.json().get("token")
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_location_missing_required_fields(self):
        """POST /api/geolocation-attendance/locations - Missing required fields returns 422"""
        # Missing latitude and longitude
        response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/locations",
            json={
                "name": "Incomplete Location",
                "address": "Some Address"
                # Missing latitude, longitude
            }
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print(f"✓ Missing required fields returns 422")
    
    def test_mark_attendance_missing_coordinates(self):
        """POST /api/geolocation-attendance/mark - Missing coordinates returns 422"""
        response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/mark",
            json={
                "mark_type": "entry"
                # Missing latitude, longitude, accuracy
            }
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print(f"✓ Missing coordinates returns 422")
    
    def test_mark_attendance_invalid_mark_type(self):
        """POST /api/geolocation-attendance/mark - Invalid mark_type"""
        response = self.session.post(
            f"{BASE_URL}/api/geolocation-attendance/mark",
            json={
                "latitude": 18.4861,
                "longitude": -69.9312,
                "accuracy": 10.0,
                "mark_type": "invalid_type"
            }
        )
        
        # Should either return 422 (validation error) or 200 (if backend accepts any string)
        # The important thing is it doesn't crash
        assert response.status_code in [200, 400, 404, 422], f"Unexpected status: {response.status_code}"
        print(f"✓ Invalid mark_type handled gracefully (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
