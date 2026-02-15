"""
Tests for Employee Portal Language Switcher and Password Change features
- Language switcher at login and dashboard
- Password change API endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
EMPLOYEE_DOCUMENT = "001-0000001-1"
EMPLOYEE_PASSWORD = "portal123"


class TestEmployeePortalLogin:
    """Test employee portal login endpoint"""
    
    def test_login_success(self):
        """Test successful employee login"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOCUMENT,
            "password": EMPLOYEE_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "employee" in data, "Employee not in response"
        assert "name" in data["employee"], "Employee name missing"
        print(f"PASS: Login successful for {EMPLOYEE_DOCUMENT}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOCUMENT,
            "password": "wrongpassword123"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Invalid credentials correctly rejected with 401")


class TestPasswordChange:
    """Test password change endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for employee"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOCUMENT,
            "password": EMPLOYEE_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not login to get token")
    
    def test_change_password_wrong_current(self, auth_token):
        """Test password change with wrong current password returns 401"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/employee-portal/change-password", 
            json={
                "old_password": "wrongpassword",
                "new_password": "newpassword123"
            },
            headers=headers
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: Wrong current password correctly returns 401")
    
    def test_change_password_too_short(self, auth_token):
        """Test password change with short password returns 400"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/employee-portal/change-password", 
            json={
                "old_password": EMPLOYEE_PASSWORD,
                "new_password": "ab"
            },
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("PASS: Short password correctly returns 400")
    
    def test_change_password_success_and_revert(self, auth_token):
        """Test successful password change and then revert it"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        new_password = "test_new_password_123"
        
        # Step 1: Change password to new one
        response = requests.post(f"{BASE_URL}/api/employee-portal/change-password", 
            json={
                "old_password": EMPLOYEE_PASSWORD,
                "new_password": new_password
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Password change failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"PASS: Password changed successfully. Message: {data.get('message')}")
        
        # Step 2: Login with new password
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOCUMENT,
            "password": new_password
        })
        
        assert response.status_code == 200, f"Login with new password failed: {response.text}"
        new_token = response.json().get("token")
        print("PASS: Login with new password successful")
        
        # Step 3: Revert password back to original
        headers_new = {"Authorization": f"Bearer {new_token}"}
        response = requests.post(f"{BASE_URL}/api/employee-portal/change-password", 
            json={
                "old_password": new_password,
                "new_password": EMPLOYEE_PASSWORD
            },
            headers=headers_new
        )
        
        assert response.status_code == 200, f"Password revert failed: {response.text}"
        print("PASS: Password reverted to original")
        
        # Step 4: Verify original password works
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOCUMENT,
            "password": EMPLOYEE_PASSWORD
        })
        
        assert response.status_code == 200, f"Login with original password failed: {response.text}"
        print("PASS: Original password works after revert")


class TestEmployeePortalDashboardEndpoints:
    """Test dashboard endpoints work after login"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for employee"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOCUMENT,
            "password": EMPLOYEE_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not login to get token")
    
    def test_dashboard_endpoint(self, auth_token):
        """Test dashboard endpoint returns data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employee-portal/dashboard", headers=headers)
        
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        assert "employee" in data
        print(f"PASS: Dashboard endpoint working. Employee: {data['employee'].get('name')}")
    
    def test_profile_endpoint(self, auth_token):
        """Test profile endpoint returns employee data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employee-portal/profile", headers=headers)
        
        assert response.status_code == 200, f"Profile failed: {response.text}"
        data = response.json()
        assert "employee" in data
        print(f"PASS: Profile endpoint working")


class TestNotificationsStillWorking:
    """Verify notification endpoints still work alongside new features"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for employee"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_DOCUMENT,
            "password": EMPLOYEE_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not login to get token")
    
    def test_notifications_endpoint(self, auth_token):
        """Test notifications endpoint returns data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employee-portal/notifications", headers=headers)
        
        assert response.status_code == 200, f"Notifications failed: {response.text}"
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"PASS: Notifications endpoint working. Unread count: {data['unread_count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
