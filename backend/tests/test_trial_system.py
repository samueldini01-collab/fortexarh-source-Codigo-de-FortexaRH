"""
Test Trial System - FortexaRH
Tests for 3-day trial system, trial-status endpoint, and login trial response
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTrialSystem:
    """Trial system endpoint tests"""
    
    # Test credentials from the request
    PRO_USER_EMAIL = "test_refactor@fortexa.com"
    PRO_USER_PASSWORD = "test123"
    
    def test_login_pro_user_returns_null_trial(self):
        """POST /api/auth/login - Pro plan user should have trial: null"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.PRO_USER_EMAIL,
            "password": self.PRO_USER_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Pro user should have trial: null (not on trial)
        assert "trial" in data, "Response should contain 'trial' field"
        trial_info = data.get("trial")
        
        # For paid plans, trial should be null
        print(f"Trial info for Pro user: {trial_info}")
        assert trial_info is None, f"Pro plan user should have trial: null, got: {trial_info}"
        
        # Verify user data
        assert "user" in data
        assert data["user"]["email"] == self.PRO_USER_EMAIL
        
        return data.get("token")
    
    def test_trial_status_endpoint_for_pro_user(self):
        """GET /api/auth/trial-status - Pro plan user should have on_trial: false"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.PRO_USER_EMAIL,
            "password": self.PRO_USER_PASSWORD
        })
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        
        # Now check trial status
        response = requests.get(
            f"{BASE_URL}/api/auth/trial-status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Trial status failed: {response.text}"
        data = response.json()
        
        print(f"Trial status for Pro user: {data}")
        
        # Pro user should NOT be on trial
        assert data.get("on_trial") == False, f"Pro user should have on_trial: false, got: {data.get('on_trial')}"
        assert data.get("trial_expired") == False, f"Pro user should have trial_expired: false"
        
        # Should have a plan that's not 'trial' or 'free'
        plan = data.get("plan")
        print(f"User plan: {plan}")
        assert plan not in ("trial", "free"), f"Pro user should not be on trial/free plan, got: {plan}"
    
    def test_login_response_structure_for_trial_user(self):
        """Verify login response structure includes trial field with correct keys"""
        # This test verifies the structure - we use the Pro user but check structure
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.PRO_USER_EMAIL,
            "password": self.PRO_USER_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has required fields
        assert "token" in data, "Response should have 'token'"
        assert "user" in data, "Response should have 'user'"
        assert "trial" in data, "Response should have 'trial' field"
        
        # If trial is not null, it should have these keys
        trial = data.get("trial")
        if trial is not None:
            expected_keys = ["on_trial", "trial_expired", "days_left"]
            for key in expected_keys:
                assert key in trial, f"Trial object should have '{key}' key"
    
    def test_trial_status_endpoint_requires_auth(self):
        """GET /api/auth/trial-status - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/trial-status")
        
        # Should return 401 or 403 without auth
        assert response.status_code in (401, 403), f"Expected 401/403 without auth, got: {response.status_code}"


class TestTrialExpiredPage:
    """Tests for trial-expired page accessibility"""
    
    def test_trial_expired_page_accessible(self):
        """Verify /trial-expired page is accessible (returns HTML)"""
        response = requests.get(f"{BASE_URL}/trial-expired")
        
        # Should return 200 (React SPA will handle routing)
        assert response.status_code == 200, f"Trial expired page should be accessible, got: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
