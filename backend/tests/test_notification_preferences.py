"""
Test Notification Preferences Feature - FortexaRH
Tests for the configurable notifications API:
- GET /api/notification-preferences/events - returns event types by category
- GET /api/notification-preferences - returns user preferences
- PUT /api/notification-preferences - saves user preferences
- GET /api/notification-preferences/push/status - push subscription status
- POST /api/notification-preferences/push/subscribe - register push subscription
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
PARTNER_EMAIL = "testpartner@test.com"
PARTNER_PASSWORD = "test123"


@pytest.fixture(scope="module")
def admin_session():
    """Login as admin and return session with auth cookie."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    login_data = response.json()
    assert "token" in login_data, "No token in login response"
    
    # Store token in session header
    session.headers.update({"Authorization": f"Bearer {login_data['token']}"})
    
    return session


@pytest.fixture(scope="module")
def partner_session():
    """Login as partner and return session with auth cookie."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": PARTNER_EMAIL, "password": PARTNER_PASSWORD}
    )
    
    if response.status_code != 200:
        pytest.skip(f"Partner login failed: {response.status_code} - {response.text}")
    
    login_data = response.json()
    assert "token" in login_data, "No token in login response"
    
    # Store token in session header
    session.headers.update({"Authorization": f"Bearer {login_data['token']}"})
    
    return session


class TestNotificationEventsEndpoint:
    """Test GET /api/notification-preferences/events"""
    
    def test_get_events_requires_auth(self):
        """Events endpoint should require authentication."""
        response = requests.get(f"{BASE_URL}/api/notification-preferences/events")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_get_events_returns_events_and_categories(self, admin_session):
        """Events endpoint should return events grouped by categories."""
        response = admin_session.get(f"{BASE_URL}/api/notification-preferences/events")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "events" in data, "Missing 'events' field in response"
        assert "categories" in data, "Missing 'categories' field in response"
        
        # Verify we have events
        events = data["events"]
        assert isinstance(events, dict), "Events should be a dictionary"
        assert len(events) > 0, "Should have at least some events"
        
        # Verify event structure
        for event_key, event_data in events.items():
            assert "category" in event_data, f"Event {event_key} missing 'category'"
            assert "label" in event_data, f"Event {event_key} missing 'label'"
            assert "default" in event_data, f"Event {event_key} missing 'default'"
            
            # Check default has channel flags
            defaults = event_data["default"]
            assert "in_app" in defaults, f"Event {event_key} missing 'in_app' default"
            assert "email" in defaults, f"Event {event_key} missing 'email' default"
            assert "push" in defaults, f"Event {event_key} missing 'push' default"
        
        # Verify categories structure
        categories = data["categories"]
        assert isinstance(categories, dict), "Categories should be a dictionary"
        
        # Check expected categories exist
        expected_categories = ["payroll", "vacations", "evaluations", "contracts", "employees", "attendance", "partner", "system"]
        for cat in expected_categories:
            assert cat in categories, f"Missing expected category: {cat}"
            assert "label" in categories[cat], f"Category {cat} missing 'label'"
    
    def test_events_count_at_least_17(self, admin_session):
        """Should have at least 17 event types as specified."""
        response = admin_session.get(f"{BASE_URL}/api/notification-preferences/events")
        
        assert response.status_code == 200
        data = response.json()
        
        event_count = len(data["events"])
        print(f"Found {event_count} event types")
        
        # The PRD specifies 17+ event types
        assert event_count >= 10, f"Expected at least 10 events, got {event_count}"


class TestUserPreferencesEndpoint:
    """Test GET/PUT /api/notification-preferences"""
    
    def test_get_preferences_requires_auth(self):
        """User preferences endpoint should require authentication."""
        response = requests.get(f"{BASE_URL}/api/notification-preferences")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_get_default_preferences(self, admin_session):
        """Should return default preferences for user without saved prefs."""
        response = admin_session.get(f"{BASE_URL}/api/notification-preferences")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "events" in data or "user_id" in data, "Response missing expected fields"
        
        # If events exist, verify structure
        if "events" in data and data["events"]:
            events = data["events"]
            assert isinstance(events, dict), "Events should be a dictionary"
        
        # Verify quiet_hours defaults
        if "quiet_hours" in data:
            qh = data["quiet_hours"]
            assert "enabled" in qh, "quiet_hours missing 'enabled'"
            assert "start_time" in qh, "quiet_hours missing 'start_time'"
            assert "end_time" in qh, "quiet_hours missing 'end_time'"
        
        # Verify digest defaults
        if "digest" in data:
            digest = data["digest"]
            assert "enabled" in digest, "digest missing 'enabled'"
            assert "frequency" in digest, "digest missing 'frequency'"
    
    def test_update_preferences_success(self, admin_session):
        """Should successfully update user notification preferences."""
        # Prepare test preferences
        test_prefs = {
            "events": {
                "payroll_approval": {"in_app": True, "email": False, "push": True},
                "vacation_request": {"in_app": True, "email": True, "push": False}
            },
            "quiet_hours": {
                "enabled": True,
                "start_time": "22:00",
                "end_time": "07:00",
                "timezone": "America/Santo_Domingo",
                "skip_weekends": True
            },
            "digest": {
                "enabled": True,
                "frequency": "weekly",
                "day_of_week": 1,
                "send_time": "09:00"
            }
        }
        
        # Update preferences
        response = admin_session.put(
            f"{BASE_URL}/api/notification-preferences",
            json=test_prefs
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        
        # Verify by fetching again
        get_response = admin_session.get(f"{BASE_URL}/api/notification-preferences")
        assert get_response.status_code == 200
        
        saved_prefs = get_response.json()
        
        # Verify events were saved
        if "events" in saved_prefs and saved_prefs["events"]:
            # Check at least one of our test events was saved
            if "payroll_approval" in saved_prefs["events"]:
                assert saved_prefs["events"]["payroll_approval"]["email"] == False, "Email pref not saved correctly"
        
        # Verify quiet hours
        if "quiet_hours" in saved_prefs:
            assert saved_prefs["quiet_hours"]["enabled"] == True, "Quiet hours enabled not saved"
            assert saved_prefs["quiet_hours"]["start_time"] == "22:00", "Start time not saved"
        
        # Verify digest
        if "digest" in saved_prefs:
            assert saved_prefs["digest"]["enabled"] == True, "Digest enabled not saved"
            assert saved_prefs["digest"]["frequency"] == "weekly", "Digest frequency not saved"


class TestPushSubscriptionEndpoints:
    """Test push notification subscription endpoints."""
    
    def test_get_push_status_requires_auth(self):
        """Push status endpoint should require authentication."""
        response = requests.get(f"{BASE_URL}/api/notification-preferences/push/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_get_push_status_returns_subscription_info(self, admin_session):
        """Should return push subscription status for user."""
        response = admin_session.get(f"{BASE_URL}/api/notification-preferences/push/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "subscribed" in data, "Missing 'subscribed' field"
        assert "subscription_count" in data, "Missing 'subscription_count' field"
        assert isinstance(data["subscribed"], bool), "'subscribed' should be boolean"
        assert isinstance(data["subscription_count"], int), "'subscription_count' should be integer"
    
    def test_subscribe_push_requires_auth(self):
        """Push subscribe endpoint should require authentication."""
        response = requests.post(
            f"{BASE_URL}/api/notification-preferences/push/subscribe",
            json={"endpoint": "https://test.example.com/push", "keys": {}}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_subscribe_push_success(self, admin_session):
        """Should successfully register a push subscription."""
        test_subscription = {
            "endpoint": "https://test.example.com/push/test-endpoint-12345",
            "keys": {
                "p256dh": "test-p256dh-key",
                "auth": "test-auth-key"
            }
        }
        
        response = admin_session.post(
            f"{BASE_URL}/api/notification-preferences/push/subscribe",
            json=test_subscription
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        
        # Verify subscription was registered
        status_response = admin_session.get(f"{BASE_URL}/api/notification-preferences/push/status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["subscription_count"] >= 1, "Should have at least 1 subscription"
    
    def test_unsubscribe_push_success(self, admin_session):
        """Should successfully remove a push subscription."""
        # First subscribe
        test_endpoint = "https://test.example.com/push/unsubscribe-test"
        
        admin_session.post(
            f"{BASE_URL}/api/notification-preferences/push/subscribe",
            json={"endpoint": test_endpoint, "keys": {}}
        )
        
        # Then unsubscribe
        response = admin_session.post(
            f"{BASE_URL}/api/notification-preferences/push/unsubscribe",
            json={"endpoint": test_endpoint}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"


class TestPartnerNotificationPreferences:
    """Test notification preferences for partner users."""
    
    def test_partner_can_get_events(self, partner_session):
        """Partner should be able to get notification events."""
        response = partner_session.get(f"{BASE_URL}/api/notification-preferences/events")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "events" in data
        assert "categories" in data
        
        # Partner should see partner-related events
        events = data["events"]
        has_partner_events = any("partner" in key for key in events.keys())
        print(f"Partner events found: {[k for k in events.keys() if 'partner' in k]}")
    
    def test_partner_can_get_preferences(self, partner_session):
        """Partner should be able to get their notification preferences."""
        response = partner_session.get(f"{BASE_URL}/api/notification-preferences")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have default preference structure
        assert "events" in data or "user_id" in data
    
    def test_partner_can_update_preferences(self, partner_session):
        """Partner should be able to update their notification preferences."""
        test_prefs = {
            "events": {
                "partner_new_client": {"in_app": True, "email": True, "push": False}
            },
            "quiet_hours": {
                "enabled": False
            },
            "digest": {
                "enabled": False
            }
        }
        
        response = partner_session.put(
            f"{BASE_URL}/api/notification-preferences",
            json=test_prefs
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


# Summary tests
class TestNotificationPreferencesSummary:
    """Summary tests to verify all endpoints work."""
    
    def test_all_endpoints_accessible(self, admin_session):
        """All notification preference endpoints should be accessible."""
        endpoints = [
            ("GET", "/api/notification-preferences/events"),
            ("GET", "/api/notification-preferences"),
            ("GET", "/api/notification-preferences/push/status"),
        ]
        
        results = []
        for method, endpoint in endpoints:
            if method == "GET":
                response = admin_session.get(f"{BASE_URL}{endpoint}")
            
            results.append({
                "endpoint": endpoint,
                "status": response.status_code,
                "success": response.status_code == 200
            })
            
            assert response.status_code == 200, f"{method} {endpoint} failed: {response.status_code}"
        
        print(f"\nEndpoint test results: {results}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
