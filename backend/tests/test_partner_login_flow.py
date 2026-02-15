"""
Partner Login Flow Tests - FortexaRH
Tests the unified login flow for partner and regular users.
Verifies is_partner and partner_id fields in login, session, and me endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PARTNER_EMAIL = "testpartner@test.com"
PARTNER_PASSWORD = "test123"
REGULAR_EMAIL = "test_refactor@fortexa.com"
REGULAR_PASSWORD = "test123"


class TestPartnerLogin:
    """Tests for partner user login flow"""
    
    def test_partner_login_returns_is_partner_true(self):
        """Login as partner should return is_partner=true and partner_id"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Token assertion
        assert "token" in data
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
        
        # User data assertions
        assert "user" in data
        user = data["user"]
        assert user["email"] == PARTNER_EMAIL
        assert user["is_partner"] == True
        assert user["partner_id"] is not None
        assert isinstance(user["partner_id"], str)
        assert user["role"] == "partner_admin"
        
    def test_partner_me_endpoint_returns_correct_data(self):
        """GET /auth/me for partner should return is_partner=true and partner_id"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Call /me endpoint
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == PARTNER_EMAIL
        assert data["is_partner"] == True
        assert data["partner_id"] is not None
        assert isinstance(data["partner_id"], str)
        assert data["role"] == "partner_admin"
        assert "company_name" in data


class TestRegularUserLogin:
    """Tests for regular (non-partner) user login flow"""
    
    def test_regular_user_login_returns_is_partner_false(self):
        """Login as regular user should return is_partner=false"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_EMAIL,
            "password": REGULAR_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Token assertion
        assert "token" in data
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
        
        # User data assertions
        assert "user" in data
        user = data["user"]
        assert user["email"] == REGULAR_EMAIL
        assert user["is_partner"] == False
        assert user["partner_id"] is None
        assert user["role"] == "admin"
        
    def test_regular_user_me_endpoint_returns_correct_data(self):
        """GET /auth/me for regular user should return is_partner=false"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_EMAIL,
            "password": REGULAR_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Call /me endpoint
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == REGULAR_EMAIL
        assert data["is_partner"] == False
        assert data["partner_id"] is None
        assert data["role"] == "admin"
        assert "company_name" in data


class TestInvalidLogin:
    """Tests for invalid login attempts"""
    
    def test_invalid_credentials_returns_401(self):
        """Login with invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        
    def test_wrong_password_returns_401(self):
        """Login with correct email but wrong password should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401


class TestMeEndpointAuth:
    """Tests for /me endpoint authentication"""
    
    def test_me_without_token_returns_error(self):
        """GET /auth/me without token should return error"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403, 422]
        
    def test_me_with_invalid_token_returns_error(self):
        """GET /auth/me with invalid token should return error"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": "Bearer invalid_token_here"
        })
        
        # Should return 401 or 403
        assert response.status_code in [401, 403]
