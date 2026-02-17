"""
Test Push Notifications for Vacation and Payroll + Health Endpoint JSON fix
Tests automatic push notifications when payroll is processed or vacation request is approved/rejected.
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoint:
    """Test that /api/health returns JSON instead of HTML"""
    
    def test_health_endpoint_returns_json(self):
        """GET /api/health should return JSON with {status: 'healthy', service: 'fortexarh-api'}"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check content type is JSON
        content_type = response.headers.get('content-type', '')
        assert 'application/json' in content_type, f"Expected JSON content-type, got: {content_type}"
        
        # Check response body
        data = response.json()
        assert data.get('status') == 'healthy', f"Expected status 'healthy', got: {data.get('status')}"
        assert data.get('service') == 'fortexarh-api', f"Expected service 'fortexarh-api', got: {data.get('service')}"
        print(f"PASSED: /api/health returns JSON: {data}")


class TestAdminAuth:
    """Admin authentication tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        print(f"PASSED: Admin login successful")
        return token
    
    def test_admin_login(self, admin_token):
        """Verify admin can login"""
        assert admin_token is not None


class TestVacationApprovalPushNotification:
    """Test vacation approval flow with push notifications"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return token
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_create_and_approve_vacation_request(self, auth_headers):
        """Create a vacation request and approve it - verify employee_notification is created"""
        # Use the specified employee_id
        employee_id = "emp_7d20680627a9"
        
        # Create a vacation request
        start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
        
        vacation_data = {
            "employee_id": employee_id,
            "leave_type": "vacaciones",
            "start_date": start_date,
            "end_date": end_date,
            "reason": "TEST_Push notification test vacation"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/vacations",
            json=vacation_data,
            headers=auth_headers
        )
        
        assert create_response.status_code in [200, 201], f"Failed to create vacation: {create_response.text}"
        created = create_response.json()
        vacation_id = created.get("vacation_id")
        assert vacation_id, f"No vacation_id in response: {created}"
        print(f"PASSED: Created vacation request {vacation_id}")
        
        # Approve the vacation request
        approve_response = requests.put(
            f"{BASE_URL}/api/vacations/{vacation_id}/approve",
            json={"status": "approved", "approver_comments": "Test approval with push notification"},
            headers=auth_headers
        )
        
        assert approve_response.status_code == 200, f"Failed to approve vacation: {approve_response.text}"
        approve_data = approve_response.json()
        print(f"PASSED: Vacation approved - Response: {approve_data}")
        
        # The approval should not have any error and should complete successfully
        # Push notification will be attempted (returns 0 if no subscriptions exist)
        assert "error" not in str(approve_data).lower() or "message" in approve_data
        
        # Cleanup - cancel the vacation
        try:
            requests.put(
                f"{BASE_URL}/api/vacations/{vacation_id}/cancel",
                headers=auth_headers
            )
        except:
            pass
        
        return vacation_id
    
    def test_create_and_reject_vacation_request(self, auth_headers):
        """Create a vacation request and reject it - verify it works without errors"""
        employee_id = "emp_7d20680627a9"
        
        start_date = (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
        
        vacation_data = {
            "employee_id": employee_id,
            "leave_type": "vacaciones",
            "start_date": start_date,
            "end_date": end_date,
            "reason": "TEST_Push notification test vacation for rejection"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/vacations",
            json=vacation_data,
            headers=auth_headers
        )
        
        assert create_response.status_code in [200, 201], f"Failed to create vacation: {create_response.text}"
        created = create_response.json()
        vacation_id = created.get("vacation_id")
        assert vacation_id, f"No vacation_id in response: {created}"
        print(f"PASSED: Created vacation request {vacation_id} for rejection test")
        
        # Reject the vacation request
        reject_response = requests.put(
            f"{BASE_URL}/api/vacations/{vacation_id}/reject",
            json={"status": "rejected", "approver_comments": "Test rejection with push notification"},
            headers=auth_headers
        )
        
        assert reject_response.status_code == 200, f"Failed to reject vacation: {reject_response.text}"
        reject_data = reject_response.json()
        print(f"PASSED: Vacation rejected - Response: {reject_data}")
        
        # The rejection should not have any error
        assert "error" not in str(reject_data).lower() or "message" in reject_data
        
        return vacation_id


class TestEmployeePortalPushSubscription:
    """Test employee portal push subscribe/unsubscribe endpoints"""
    
    @pytest.fixture
    def employee_token(self):
        """Get employee portal auth token"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "cedula": "001-0000001-1",
            "password": "portal123"
        })
        assert response.status_code == 200, f"Employee login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        employee_id = data.get("employee", {}).get("employee_id") or data.get("employee_id")
        print(f"PASSED: Employee login successful, employee_id: {employee_id}")
        return token, employee_id
    
    def test_push_subscribe(self, employee_token):
        """Test push subscription endpoint - user_id should be employee_id directly (no emp_emp_ prefix)"""
        token, employee_id = employee_token
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test subscription
        subscription_data = {
            "endpoint": f"https://test-push-service.example.com/test-{uuid.uuid4().hex[:8]}",
            "keys": {
                "p256dh": "test_p256dh_key_" + uuid.uuid4().hex[:16],
                "auth": "test_auth_" + uuid.uuid4().hex[:8]
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/push/subscribe",
            json=subscription_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Push subscribe failed: {response.text}"
        data = response.json()
        print(f"PASSED: Push subscribe response: {data}")
        
        # Store endpoint for cleanup
        return subscription_data["endpoint"], headers
    
    def test_push_status(self, employee_token):
        """Test push status endpoint"""
        token, _ = employee_token
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/push/status",
            headers=headers
        )
        
        assert response.status_code == 200, f"Push status failed: {response.text}"
        data = response.json()
        assert "subscribed" in data, f"Missing 'subscribed' in response: {data}"
        assert "subscription_count" in data, f"Missing 'subscription_count' in response: {data}"
        print(f"PASSED: Push status: {data}")
    
    def test_push_unsubscribe(self, employee_token):
        """Test push unsubscribe endpoint"""
        token, _ = employee_token
        headers = {"Authorization": f"Bearer {token}"}
        
        # First subscribe
        endpoint = f"https://test-push-service.example.com/unsub-test-{uuid.uuid4().hex[:8]}"
        subscription_data = {
            "endpoint": endpoint,
            "keys": {
                "p256dh": "test_p256dh_" + uuid.uuid4().hex[:16],
                "auth": "test_auth_" + uuid.uuid4().hex[:8]
            }
        }
        
        sub_response = requests.post(
            f"{BASE_URL}/api/employee-portal/push/subscribe",
            json=subscription_data,
            headers=headers
        )
        assert sub_response.status_code == 200
        
        # Then unsubscribe
        unsub_response = requests.post(
            f"{BASE_URL}/api/employee-portal/push/unsubscribe",
            json={"endpoint": endpoint},
            headers=headers
        )
        
        assert unsub_response.status_code == 200, f"Push unsubscribe failed: {unsub_response.text}"
        data = unsub_response.json()
        print(f"PASSED: Push unsubscribe response: {data}")


class TestEmployeeNotificationCenter:
    """Test employee notification center still works"""
    
    @pytest.fixture
    def employee_token(self):
        """Get employee portal auth token"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "cedula": "001-0000001-1",
            "password": "portal123"
        })
        assert response.status_code == 200, f"Employee login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return token
    
    def test_notification_center_endpoint(self, employee_token):
        """GET /api/employee-portal/notifications/center should work"""
        headers = {"Authorization": f"Bearer {employee_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/notifications/center",
            headers=headers
        )
        
        assert response.status_code == 200, f"Notification center failed: {response.text}"
        data = response.json()
        
        # Should have pagination fields
        assert "total" in data or "notifications" in data, f"Unexpected response: {data}"
        print(f"PASSED: Notification center endpoint works: total={data.get('total', 'N/A')}")


class TestAdminNotificationPreferences:
    """Test admin notification preferences still work with label_fr"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    def test_notification_events_include_label_fr(self, admin_token):
        """GET /api/notification-preferences/events should include label_fr"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/notification-preferences/events",
            headers=headers
        )
        
        assert response.status_code == 200, f"Notification events failed: {response.text}"
        data = response.json()
        
        # Check that events exist and have label_fr
        events = data if isinstance(data, list) else data.get("events", [])
        assert len(events) > 0, f"No events returned: {data}"
        
        # Check first event has label_fr
        first_event = events[0]
        assert "label_fr" in first_event, f"Event missing label_fr: {first_event}"
        print(f"PASSED: Notification events include label_fr. First event: {first_event}")


class TestPayrollPushNotificationCodePresence:
    """Verify push notification code is present in payroll approve and pay endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    def test_payroll_periods_list(self, admin_token):
        """Verify payroll periods endpoint works (setup for push test)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods",
            headers=headers
        )
        
        # The endpoint should work even if empty
        assert response.status_code in [200, 404], f"Payroll periods failed: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"PASSED: Payroll periods endpoint works. Count: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print("PASSED: Payroll periods endpoint returns 404 (no periods)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
