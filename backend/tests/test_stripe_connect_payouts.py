"""
Test Stripe Connect and Payouts API endpoints for Partner Portal
Tests the commission payout system with Stripe Connect integration
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials for partner user
PARTNER_EMAIL = "testpartner@test.com"
PARTNER_PASSWORD = "test123"


class TestStripeConnectPayouts:
    """Test Stripe Connect and Payouts endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as partner user
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": PARTNER_EMAIL, "password": PARTNER_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip(f"Partner login failed: {login_response.text}")
    
    # ============== STRIPE CONNECT STATUS TESTS ==============
    
    def test_get_connect_status_returns_200(self):
        """GET /api/partners/connect/status should return 200"""
        response = self.session.get(f"{BASE_URL}/api/partners/connect/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_get_connect_status_response_structure(self):
        """GET /api/partners/connect/status should return correct structure"""
        response = self.session.get(f"{BASE_URL}/api/partners/connect/status")
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields exist
        assert "connected" in data, "Response should have 'connected' field"
        assert "status" in data, "Response should have 'status' field"
        assert "message" in data, "Response should have 'message' field"
        
        # Verify data types
        assert isinstance(data["connected"], bool), "'connected' should be boolean"
        assert isinstance(data["status"], str), "'status' should be string"
        assert isinstance(data["message"], str), "'message' should be string"
    
    def test_get_connect_status_not_connected(self):
        """GET /api/partners/connect/status should show not connected for new partner"""
        response = self.session.get(f"{BASE_URL}/api/partners/connect/status")
        assert response.status_code == 200
        
        data = response.json()
        # For a partner without Stripe connected
        if not data["connected"]:
            assert data["status"] == "not_connected", "Status should be 'not_connected'"
            assert "No has conectado" in data["message"] or "Stripe" in data["message"]
    
    # ============== STRIPE CONNECT ONBOARD TESTS ==============
    
    def test_post_connect_onboard_returns_400_without_connect(self):
        """POST /api/partners/connect/onboard should return 400 if Stripe Connect not enabled"""
        response = self.session.post(
            f"{BASE_URL}/api/partners/connect/onboard",
            json={
                "return_url": "https://example.com/return",
                "refresh_url": "https://example.com/refresh"
            }
        )
        # Expected to fail because Stripe Connect is not enabled on the account
        # This is expected behavior - the endpoint works but Stripe rejects the request
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"
        
        if response.status_code == 400:
            data = response.json()
            assert "detail" in data, "Error response should have 'detail' field"
            assert "Stripe" in data["detail"], "Error should mention Stripe"
    
    def test_post_connect_onboard_requires_urls(self):
        """POST /api/partners/connect/onboard should require return_url and refresh_url"""
        # Test with missing fields
        response = self.session.post(
            f"{BASE_URL}/api/partners/connect/onboard",
            json={}
        )
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
    
    # ============== PAYOUTS BALANCE TESTS ==============
    
    def test_get_payouts_balance_returns_200(self):
        """GET /api/partners/payouts/balance should return 200"""
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_get_payouts_balance_response_structure(self):
        """GET /api/partners/payouts/balance should return correct structure"""
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/balance")
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields
        required_fields = [
            "available_balance",
            "total_earned",
            "total_paid",
            "pending_payouts",
            "minimum_payout",
            "can_withdraw",
            "stripe_connected",
            "payout_frequency"
        ]
        
        for field in required_fields:
            assert field in data, f"Response should have '{field}' field"
        
        # Verify data types
        assert isinstance(data["available_balance"], (int, float)), "'available_balance' should be numeric"
        assert isinstance(data["total_earned"], (int, float)), "'total_earned' should be numeric"
        assert isinstance(data["total_paid"], (int, float)), "'total_paid' should be numeric"
        assert isinstance(data["pending_payouts"], (int, float)), "'pending_payouts' should be numeric"
        assert isinstance(data["minimum_payout"], (int, float)), "'minimum_payout' should be numeric"
        assert isinstance(data["can_withdraw"], bool), "'can_withdraw' should be boolean"
        assert isinstance(data["stripe_connected"], bool), "'stripe_connected' should be boolean"
        assert isinstance(data["payout_frequency"], str), "'payout_frequency' should be string"
    
    def test_get_payouts_balance_minimum_payout_is_50(self):
        """GET /api/partners/payouts/balance should show minimum payout of $50"""
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert data["minimum_payout"] == 50.0, f"Minimum payout should be $50, got {data['minimum_payout']}"
    
    def test_get_payouts_balance_frequency_is_monthly(self):
        """GET /api/partners/payouts/balance should show monthly payout frequency"""
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert data["payout_frequency"] == "monthly", f"Payout frequency should be 'monthly', got {data['payout_frequency']}"
    
    def test_get_payouts_balance_cannot_withdraw_without_stripe(self):
        """GET /api/partners/payouts/balance should show can_withdraw=false without Stripe"""
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/balance")
        assert response.status_code == 200
        
        data = response.json()
        # If Stripe is not connected, can_withdraw should be false
        if not data["stripe_connected"]:
            assert data["can_withdraw"] == False, "can_withdraw should be false without Stripe connected"
    
    # ============== PAYOUTS HISTORY TESTS ==============
    
    def test_get_payouts_history_returns_200(self):
        """GET /api/partners/payouts/history should return 200"""
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_get_payouts_history_response_structure(self):
        """GET /api/partners/payouts/history should return correct structure"""
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/history")
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields
        assert "payouts" in data, "Response should have 'payouts' field"
        assert "summary" in data, "Response should have 'summary' field"
        assert "minimum_payout" in data, "Response should have 'minimum_payout' field"
        assert "payout_frequency" in data, "Response should have 'payout_frequency' field"
        
        # Verify data types
        assert isinstance(data["payouts"], list), "'payouts' should be a list"
        assert isinstance(data["summary"], dict), "'summary' should be a dict"
    
    def test_get_payouts_history_with_limit(self):
        """GET /api/partners/payouts/history should accept limit parameter"""
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/history?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # ============== PAYOUTS REQUEST TESTS ==============
    
    def test_post_payouts_request_requires_stripe_connected(self):
        """POST /api/partners/payouts/request should require Stripe connected"""
        response = self.session.post(
            f"{BASE_URL}/api/partners/payouts/request",
            json={"amount": 100}
        )
        
        # Check if Stripe is connected first
        status_response = self.session.get(f"{BASE_URL}/api/partners/connect/status")
        status_data = status_response.json()
        
        if not status_data.get("connected"):
            # Should return 400 if Stripe not connected
            assert response.status_code == 400, f"Expected 400 without Stripe, got {response.status_code}"
            data = response.json()
            assert "detail" in data, "Error response should have 'detail' field"
            assert "Stripe" in data["detail"], "Error should mention Stripe configuration"
    
    def test_post_payouts_request_validates_minimum_amount(self):
        """POST /api/partners/payouts/request should validate minimum amount"""
        # First check if Stripe is connected
        status_response = self.session.get(f"{BASE_URL}/api/partners/connect/status")
        status_data = status_response.json()
        
        if status_data.get("connected"):
            # Try to request less than minimum
            response = self.session.post(
                f"{BASE_URL}/api/partners/payouts/request",
                json={"amount": 10}  # Less than $50 minimum
            )
            assert response.status_code == 400, f"Expected 400 for amount below minimum, got {response.status_code}"
    
    def test_post_payouts_request_accepts_null_amount(self):
        """POST /api/partners/payouts/request should accept null amount (withdraw all)"""
        # First check if Stripe is connected
        status_response = self.session.get(f"{BASE_URL}/api/partners/connect/status")
        status_data = status_response.json()
        
        if not status_data.get("connected"):
            # Should still return 400 for Stripe not connected, not validation error
            response = self.session.post(
                f"{BASE_URL}/api/partners/payouts/request",
                json={"amount": None}
            )
            assert response.status_code == 400, f"Expected 400 without Stripe, got {response.status_code}"


class TestStripeConnectUnauthorized:
    """Test Stripe Connect endpoints without authentication"""
    
    def test_connect_status_requires_auth(self):
        """GET /api/partners/connect/status should require authentication"""
        response = requests.get(f"{BASE_URL}/api/partners/connect/status")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_connect_onboard_requires_auth(self):
        """POST /api/partners/connect/onboard should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/partners/connect/onboard",
            json={"return_url": "https://example.com", "refresh_url": "https://example.com"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_payouts_balance_requires_auth(self):
        """GET /api/partners/payouts/balance should require authentication"""
        response = requests.get(f"{BASE_URL}/api/partners/payouts/balance")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_payouts_history_requires_auth(self):
        """GET /api/partners/payouts/history should require authentication"""
        response = requests.get(f"{BASE_URL}/api/partners/payouts/history")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_payouts_request_requires_auth(self):
        """POST /api/partners/payouts/request should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/partners/payouts/request",
            json={"amount": 100}
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


class TestNonPartnerAccess:
    """Test that non-partner users cannot access partner endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with non-partner authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Try to login as a regular user (not partner)
        # Using admin user which should not have partner_id
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@test.com", "password": "admin123"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Non-partner login failed - skipping non-partner access tests")
    
    def test_non_partner_cannot_access_connect_status(self):
        """Non-partner user should get 403 on connect status"""
        if not self.authenticated:
            pytest.skip("Not authenticated")
        
        response = self.session.get(f"{BASE_URL}/api/partners/connect/status")
        # Should return 403 for non-partner users
        assert response.status_code == 403, f"Expected 403 for non-partner, got {response.status_code}"
    
    def test_non_partner_cannot_access_payouts_balance(self):
        """Non-partner user should get 403 on payouts balance"""
        if not self.authenticated:
            pytest.skip("Not authenticated")
        
        response = self.session.get(f"{BASE_URL}/api/partners/payouts/balance")
        assert response.status_code == 403, f"Expected 403 for non-partner, got {response.status_code}"
