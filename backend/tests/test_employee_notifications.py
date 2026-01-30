"""
Test Employee Portal Notifications and Announcements
Tests for the notification system in the employee self-service portal
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_DOCUMENT = "001-0000001-1"
TEST_PASSWORD = "portal123"


class TestEmployeeNotifications:
    """Test notification endpoints for employee portal"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": TEST_DOCUMENT, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.employee_id = data["employee"]["employee_id"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_notifications(self):
        """Test GET /api/employee-portal/notifications - should return list and unread count"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get notifications: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "notifications" in data, "Response should contain 'notifications' key"
        assert "unread_count" in data, "Response should contain 'unread_count' key"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        assert isinstance(data["unread_count"], int), "unread_count should be an integer"
        
        print(f"SUCCESS: Got {len(data['notifications'])} notifications, {data['unread_count']} unread")
        return data
    
    def test_get_notifications_unread_only(self):
        """Test GET /api/employee-portal/notifications?unread_only=true"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications?unread_only=true",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get unread notifications: {response.text}"
        data = response.json()
        
        # All returned notifications should be unread
        for notif in data["notifications"]:
            assert notif.get("read") == False, f"Notification {notif.get('notification_id')} should be unread"
        
        print(f"SUCCESS: Got {len(data['notifications'])} unread notifications")
    
    def test_mark_notification_read(self):
        """Test POST /api/employee-portal/notifications/{id}/read"""
        # First get notifications
        get_response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications",
            headers=self.headers
        )
        data = get_response.json()
        
        if not data["notifications"]:
            pytest.skip("No notifications to mark as read")
        
        # Find an unread notification
        unread = [n for n in data["notifications"] if not n.get("read")]
        if not unread:
            pytest.skip("No unread notifications to test")
        
        notification_id = unread[0]["notification_id"]
        
        # Mark as read
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/notifications/{notification_id}/read",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to mark notification as read: {response.text}"
        result = response.json()
        assert "message" in result, "Response should contain message"
        
        print(f"SUCCESS: Marked notification {notification_id} as read")
    
    def test_mark_notification_read_not_found(self):
        """Test marking non-existent notification as read returns 404"""
        fake_id = f"notif_{uuid.uuid4().hex[:12]}"
        
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/notifications/{fake_id}/read",
            headers=self.headers
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent notification, got {response.status_code}"
        print("SUCCESS: Non-existent notification returns 404")
    
    def test_mark_all_notifications_read(self):
        """Test POST /api/employee-portal/notifications/read-all"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/notifications/read-all",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to mark all as read: {response.text}"
        result = response.json()
        assert "message" in result, "Response should contain message"
        
        # Verify all are now read
        verify_response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications?unread_only=true",
            headers=self.headers
        )
        verify_data = verify_response.json()
        assert len(verify_data["notifications"]) == 0, "All notifications should be read now"
        
        print(f"SUCCESS: Marked all notifications as read - {result['message']}")
    
    def test_delete_notification(self):
        """Test DELETE /api/employee-portal/notifications/{id}"""
        # First get notifications
        get_response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications",
            headers=self.headers
        )
        data = get_response.json()
        
        if not data["notifications"]:
            pytest.skip("No notifications to delete")
        
        notification_id = data["notifications"][0]["notification_id"]
        initial_count = len(data["notifications"])
        
        # Delete notification
        response = requests.delete(
            f"{BASE_URL}/api/employee-portal/notifications/{notification_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to delete notification: {response.text}"
        result = response.json()
        assert "message" in result, "Response should contain message"
        
        # Verify deletion
        verify_response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications",
            headers=self.headers
        )
        verify_data = verify_response.json()
        assert len(verify_data["notifications"]) == initial_count - 1, "Notification count should decrease by 1"
        
        print(f"SUCCESS: Deleted notification {notification_id}")
    
    def test_delete_notification_not_found(self):
        """Test deleting non-existent notification returns 404"""
        fake_id = f"notif_{uuid.uuid4().hex[:12]}"
        
        response = requests.delete(
            f"{BASE_URL}/api/employee-portal/notifications/{fake_id}",
            headers=self.headers
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent notification, got {response.status_code}"
        print("SUCCESS: Non-existent notification delete returns 404")


class TestEmployeeAnnouncements:
    """Test announcement endpoints for employee portal"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": TEST_DOCUMENT, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_announcements(self):
        """Test GET /api/employee-portal/announcements"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/announcements",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get announcements: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "announcements" in data, "Response should contain 'announcements' key"
        assert isinstance(data["announcements"], list), "announcements should be a list"
        
        # If there are announcements, verify structure
        if data["announcements"]:
            announcement = data["announcements"][0]
            assert "title" in announcement, "Announcement should have title"
            assert "content" in announcement or "message" in announcement, "Announcement should have content/message"
        
        print(f"SUCCESS: Got {len(data['announcements'])} announcements")
        return data


class TestEmployeePortalAuth:
    """Test authentication for employee portal"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": TEST_DOCUMENT, "password": TEST_PASSWORD}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "token" in data, "Response should contain token"
        assert "employee" in data, "Response should contain employee info"
        assert data["employee"]["employee_id"], "Employee should have ID"
        assert data["employee"]["name"], "Employee should have name"
        
        print(f"SUCCESS: Logged in as {data['employee']['name']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": "999-9999999-9", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("SUCCESS: Invalid credentials return 401")
    
    def test_notifications_without_auth(self):
        """Test that notifications endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/notifications")
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("SUCCESS: Notifications endpoint requires authentication")
    
    def test_announcements_without_auth(self):
        """Test that announcements endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/announcements")
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("SUCCESS: Announcements endpoint requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
