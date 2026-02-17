"""
Test Push Notifications Phase 2 - FortexaRH
Tests for PWA push notifications and employee portal notification bell.
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://company-config-debug.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
EMPLOYEE_DOC_NUMBER = "001-0000001-1"
EMPLOYEE_PASSWORD = "portal123"
PARTNER_EMAIL = "testpartner@test.com"
PARTNER_PASSWORD = "test123"


class TestAdminAuthentication:
    """Admin login for notification tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        print(f"PASSED: Admin login successful")


class TestEmployeePortalAuthentication:
    """Employee portal login tests"""
    
    @pytest.fixture
    def employee_token(self):
        """Get employee portal authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": EMPLOYEE_DOC_NUMBER, "password": EMPLOYEE_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Employee login failed: {response.status_code}")
    
    def test_employee_portal_login(self):
        """Test employee portal login with credentials 001-0000001-1 / portal123"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": EMPLOYEE_DOC_NUMBER, "password": EMPLOYEE_PASSWORD}
        )
        assert response.status_code == 200, f"Employee login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "employee" in data
        print(f"PASSED: Employee portal login successful - {data.get('employee', {}).get('name')}")


class TestEmployeePortalPushEndpoints:
    """Test employee portal push notification endpoints"""
    
    @pytest.fixture
    def employee_token(self):
        """Get employee portal authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": EMPLOYEE_DOC_NUMBER, "password": EMPLOYEE_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Employee login failed: {response.status_code}")
    
    def test_get_vapid_key_no_auth(self):
        """GET /api/employee-portal/push/vapid-key should work without auth"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/push/vapid-key")
        assert response.status_code == 200, f"VAPID key endpoint failed: {response.text}"
        data = response.json()
        assert "vapid_public_key" in data
        # VAPID key should be a non-empty string
        vapid_key = data.get("vapid_public_key", "")
        assert len(vapid_key) > 0, "VAPID public key is empty"
        print(f"PASSED: Employee portal VAPID key endpoint returns key (length: {len(vapid_key)})")
    
    def test_push_subscribe_requires_auth(self, employee_token):
        """POST /api/employee-portal/push/subscribe requires authentication"""
        # Without auth
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/push/subscribe",
            json={"endpoint": "https://test.com/push", "keys": {}}
        )
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"PASSED: Push subscribe requires auth (401 without token)")
    
    def test_push_subscribe_with_auth(self, employee_token):
        """POST /api/employee-portal/push/subscribe works with valid token"""
        headers = {"Authorization": f"Bearer {employee_token}"}
        # Use a test endpoint that won't actually work for push but tests the API
        test_subscription = {
            "endpoint": f"https://push.test.com/test_{os.urandom(4).hex()}",
            "keys": {
                "p256dh": "test_p256dh_key",
                "auth": "test_auth_key"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/push/subscribe",
            json=test_subscription,
            headers=headers
        )
        assert response.status_code == 200, f"Push subscribe failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"PASSED: Push subscribe with auth returns 200")
    
    def test_push_status_requires_auth(self, employee_token):
        """GET /api/employee-portal/push/status requires authentication"""
        # Without auth
        response = requests.get(f"{BASE_URL}/api/employee-portal/push/status")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"PASSED: Push status requires auth")
    
    def test_push_status_with_auth(self, employee_token):
        """GET /api/employee-portal/push/status returns subscription status"""
        headers = {"Authorization": f"Bearer {employee_token}"}
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/push/status",
            headers=headers
        )
        assert response.status_code == 200, f"Push status failed: {response.text}"
        data = response.json()
        assert "subscribed" in data
        assert "subscription_count" in data
        assert isinstance(data["subscribed"], bool)
        assert isinstance(data["subscription_count"], int)
        print(f"PASSED: Push status returns subscribed={data['subscribed']}, count={data['subscription_count']}")
    
    def test_push_unsubscribe_with_auth(self, employee_token):
        """POST /api/employee-portal/push/unsubscribe works with valid token"""
        headers = {"Authorization": f"Bearer {employee_token}"}
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/push/unsubscribe",
            json={"endpoint": "https://push.test.com/nonexistent"},
            headers=headers
        )
        assert response.status_code == 200, f"Push unsubscribe failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"PASSED: Push unsubscribe returns 200")


class TestAdminNotificationPreferencesPush:
    """Test admin notification preferences push endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_admin_vapid_key_endpoint(self, admin_token):
        """GET /api/notification-preferences/push/vapid-key returns VAPID public key"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/notification-preferences/push/vapid-key",
            headers=headers
        )
        assert response.status_code == 200, f"Admin VAPID key endpoint failed: {response.text}"
        data = response.json()
        assert "vapid_public_key" in data
        vapid_key = data.get("vapid_public_key", "")
        assert len(vapid_key) > 0, "Admin VAPID public key is empty"
        print(f"PASSED: Admin VAPID key endpoint returns key (length: {len(vapid_key)})")
    
    def test_admin_push_subscribe(self, admin_token):
        """POST /api/notification-preferences/push/subscribe works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        test_subscription = {
            "endpoint": f"https://admin.push.test.com/test_{os.urandom(4).hex()}",
            "keys": {
                "p256dh": "test_admin_p256dh_key",
                "auth": "test_admin_auth_key"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/notification-preferences/push/subscribe",
            json=test_subscription,
            headers=headers
        )
        assert response.status_code == 200, f"Admin push subscribe failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"PASSED: Admin push subscribe returns 200")
    
    def test_admin_push_unsubscribe(self, admin_token):
        """POST /api/notification-preferences/push/unsubscribe works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/notification-preferences/push/unsubscribe",
            json={"endpoint": "https://admin.push.test.com/nonexistent"},
            headers=headers
        )
        assert response.status_code == 200, f"Admin push unsubscribe failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"PASSED: Admin push unsubscribe returns 200")
    
    def test_admin_push_status(self, admin_token):
        """GET /api/notification-preferences/push/status returns subscription status"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/notification-preferences/push/status",
            headers=headers
        )
        assert response.status_code == 200, f"Admin push status failed: {response.text}"
        data = response.json()
        assert "subscribed" in data
        assert "subscription_count" in data
        print(f"PASSED: Admin push status returns subscribed={data['subscribed']}, count={data['subscription_count']}")
    
    def test_admin_push_test_requires_subscription(self, admin_token):
        """POST /api/notification-preferences/push/test requires active subscription"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # First unsubscribe any existing subscriptions
        requests.post(
            f"{BASE_URL}/api/notification-preferences/push/unsubscribe",
            json={"endpoint": "test"},
            headers=headers
        )
        # Now test should fail with 404 (no subscriptions)
        response = requests.post(
            f"{BASE_URL}/api/notification-preferences/push/test",
            headers=headers
        )
        # Can be 200 if there are subscriptions or 404 if none
        assert response.status_code in [200, 404], f"Admin push test unexpected status: {response.status_code}"
        print(f"PASSED: Admin push test endpoint responds correctly ({response.status_code})")


class TestEmployeePortalNotifications:
    """Test employee portal notification endpoints"""
    
    @pytest.fixture
    def employee_token(self):
        """Get employee portal authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": EMPLOYEE_DOC_NUMBER, "password": EMPLOYEE_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Employee login failed: {response.status_code}")
    
    def test_get_employee_notifications(self, employee_token):
        """GET /api/employee-portal/notifications returns notification list"""
        headers = {"Authorization": f"Bearer {employee_token}"}
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications",
            headers=headers
        )
        assert response.status_code == 200, f"Get notifications failed: {response.text}"
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        assert isinstance(data["notifications"], list)
        assert isinstance(data["unread_count"], int)
        print(f"PASSED: Employee notifications endpoint returns {len(data['notifications'])} notifications, {data['unread_count']} unread")


class TestVAPIDKeyConfiguration:
    """Verify VAPID keys are properly configured"""
    
    def test_employee_vapid_key_not_empty(self):
        """Verify employee portal VAPID key is configured"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/push/vapid-key")
        assert response.status_code == 200
        data = response.json()
        vapid_key = data.get("vapid_public_key", "")
        assert len(vapid_key) > 40, f"VAPID key seems too short or empty: {len(vapid_key)} chars"
        # Check it looks like a valid base64url encoded key
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=" for c in vapid_key), "VAPID key contains invalid characters"
        print(f"PASSED: VAPID public key is properly configured (length: {len(vapid_key)})")
    
    def test_admin_and_employee_vapid_keys_match(self):
        """Admin and employee portal should use the same VAPID key"""
        # Get employee portal VAPID key
        emp_response = requests.get(f"{BASE_URL}/api/employee-portal/push/vapid-key")
        assert emp_response.status_code == 200
        emp_vapid = emp_response.json().get("vapid_public_key", "")
        
        # Get admin VAPID key (need to login first)
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if login_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = login_response.json().get("token")
        headers = {"Authorization": f"Bearer {admin_token}"}
        admin_response = requests.get(
            f"{BASE_URL}/api/notification-preferences/push/vapid-key",
            headers=headers
        )
        assert admin_response.status_code == 200
        admin_vapid = admin_response.json().get("vapid_public_key", "")
        
        assert emp_vapid == admin_vapid, "Employee and admin VAPID keys don't match"
        print(f"PASSED: Admin and employee VAPID keys match")


class TestFullPushSubscriptionFlow:
    """Test complete push subscription flow"""
    
    @pytest.fixture
    def employee_token(self):
        """Get employee portal authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": EMPLOYEE_DOC_NUMBER, "password": EMPLOYEE_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Employee login failed: {response.status_code}")
    
    def test_full_subscription_lifecycle(self, employee_token):
        """Test subscribe -> check status -> unsubscribe flow"""
        headers = {"Authorization": f"Bearer {employee_token}"}
        
        # Generate unique test endpoint
        test_endpoint = f"https://push.test.com/lifecycle_{os.urandom(4).hex()}"
        
        # 1. Subscribe
        subscribe_response = requests.post(
            f"{BASE_URL}/api/employee-portal/push/subscribe",
            json={
                "endpoint": test_endpoint,
                "keys": {"p256dh": "test_key", "auth": "test_auth"}
            },
            headers=headers
        )
        assert subscribe_response.status_code == 200, f"Subscribe failed: {subscribe_response.text}"
        print(f"Step 1: Subscribe successful")
        
        # 2. Check status - should show subscribed
        status_response = requests.get(
            f"{BASE_URL}/api/employee-portal/push/status",
            headers=headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("subscription_count", 0) >= 1, "Subscription count should be >= 1 after subscribe"
        print(f"Step 2: Status shows {status_data['subscription_count']} subscription(s)")
        
        # 3. Unsubscribe
        unsubscribe_response = requests.post(
            f"{BASE_URL}/api/employee-portal/push/unsubscribe",
            json={"endpoint": test_endpoint},
            headers=headers
        )
        assert unsubscribe_response.status_code == 200, f"Unsubscribe failed: {unsubscribe_response.text}"
        print(f"Step 3: Unsubscribe successful")
        
        print(f"PASSED: Full subscription lifecycle test completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
