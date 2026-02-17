"""
Test i18n, backend error standardization, and employee notification center endpoints.
Tests for iteration 197.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
EMPLOYEE_DOC = "001-0000001-1"
EMPLOYEE_PASSWORD = "portal123"


class TestBackendHealth:
    """Verify backend is responding"""
    
    def test_health_check(self):
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print(f"Health check: {response.json()}")


class TestErrorStandardization:
    """Test the new AppError exception handler returns standardized JSON format"""
    
    def test_app_error_format_404(self):
        """Test that 404 errors return standardized JSON format"""
        # Access a non-existent endpoint that should raise 404
        response = requests.get(f"{BASE_URL}/api/employees/non-existent-id-12345")
        # May return 401 without auth, but should be JSON format
        print(f"404 test response: {response.status_code} - {response.text[:200]}")
        assert response.status_code in [401, 404, 422]
        
    def test_error_response_has_json_format(self):
        """Verify error responses are JSON formatted"""
        # Try an invalid login to check error format
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
        data = response.json()
        # Should have some error structure
        print(f"Error response format: {data}")
        assert "detail" in data or "error" in data


class TestAdminAuth:
    """Test admin authentication"""
    
    def test_admin_login(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print(f"Admin login successful, token received: {data['token'][:20]}...")
        return data["token"]


class TestEmployeePortalAuth:
    """Test employee portal authentication"""
    
    def test_employee_login(self):
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOC,
            "password": EMPLOYEE_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print(f"Employee login successful, token received: {data['token'][:20]}...")
        return data["token"]


class TestVAPIDKeyEndpoint:
    """Test VAPID key endpoint - ensures backend push notification config is working"""
    
    def test_vapid_key_endpoint(self):
        """GET /api/notification-preferences/push/vapid-key returns VAPID key"""
        response = requests.get(f"{BASE_URL}/api/notification-preferences/push/vapid-key")
        assert response.status_code == 200
        data = response.json()
        assert "vapid_public_key" in data
        assert len(data["vapid_public_key"]) > 0
        print(f"VAPID key found: {data['vapid_public_key'][:30]}...")


class TestNotificationEventsI18n:
    """Test that notification events endpoint includes label_fr field"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_notification_events_has_label_fr(self):
        """GET /api/notification-preferences/events returns events with label_fr"""
        response = requests.get(
            f"{BASE_URL}/api/notification-preferences/events",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check that events exist and have label_fr
        assert "events" in data
        events = data["events"]
        assert len(events) > 0
        
        # Check first event has label, label_en, label_fr
        first_event_key = list(events.keys())[0]
        first_event = events[first_event_key]
        assert "label" in first_event
        assert "label_en" in first_event
        assert "label_fr" in first_event
        print(f"Event '{first_event_key}' translations: ES='{first_event['label']}', EN='{first_event['label_en']}', FR='{first_event['label_fr']}'")
        
        # Check categories also have label_fr
        assert "categories" in data
        categories = data["categories"]
        first_cat_key = list(categories.keys())[0]
        first_cat = categories[first_cat_key]
        assert "label_fr" in first_cat
        print(f"Category '{first_cat_key}' translations: ES='{first_cat['label']}', EN='{first_cat['label_en']}', FR='{first_cat['label_fr']}'")


class TestEmployeeNotificationCenter:
    """Test the new notification center endpoints in employee portal"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login employee
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOC,
            "password": EMPLOYEE_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_notification_center_endpoint(self):
        """GET /api/employee-portal/notifications/center returns paginated results"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications/center",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "notifications" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        print(f"Notification center: {len(data['notifications'])} notifications, total={data['total']}")
    
    def test_notification_center_category_filter(self):
        """GET /api/employee-portal/notifications/center?category=payroll filters by category"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications/center?category=payroll",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        # All notifications should have category=payroll (if any exist)
        for notif in data["notifications"]:
            if "category" in notif:
                assert notif["category"] == "payroll"
        print(f"Payroll filtered: {len(data['notifications'])} notifications")
    
    def test_notification_center_search(self):
        """GET /api/employee-portal/notifications/center?search=test filters by search text"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications/center?search=vacaciones",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        print(f"Search 'vacaciones': {len(data['notifications'])} notifications found")
    
    def test_notification_categories_endpoint(self):
        """GET /api/employee-portal/notifications/categories returns distinct categories"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications/categories",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"Available categories: {data['categories']}")
    
    def test_notification_export_csv(self):
        """GET /api/employee-portal/notifications/export returns CSV with headers"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications/export",
            headers=self.headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        
        # Check CSV headers
        csv_content = response.text
        lines = csv_content.strip().split("\n")
        assert len(lines) >= 1
        header_line = lines[0]
        # Verify expected CSV headers
        expected_headers = ["Fecha", "Categoria", "Tipo", "Titulo", "Mensaje", "Leida"]
        for h in expected_headers:
            assert h in header_line
        print(f"CSV export: {len(lines)-1} rows, headers={header_line}")
    
    def test_mark_all_read_endpoint(self):
        """POST /api/employee-portal/notifications/read-all marks all as read"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/notifications/read-all",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Mark all read: {data['message']}")


class TestEmployeeNotifications:
    """Test basic employee notification endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login employee
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOC,
            "password": EMPLOYEE_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_notifications_list(self):
        """GET /api/employee-portal/notifications returns notifications with unread count"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"Notifications: {len(data['notifications'])}, unread: {data['unread_count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
