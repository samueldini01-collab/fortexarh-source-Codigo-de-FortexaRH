"""
Test SetupIntent Endpoints for Stripe Elements Payment Method Flow
Tests for: POST /api/create-setup-intent, POST /api/confirm-setup-intent
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSetupIntentEndpoints:
    """Tests for SetupIntent endpoints used by Stripe Elements inline card collection"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test credentials and get auth token"""
        self.email = "test_refactor@fortexa.com"
        self.password = "test123"
        self.token = None
        
        # Login to get token
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.email, "password": self.password}
        )
        if response.status_code == 200:
            self.token = response.json().get("token")
        
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_login_success(self):
        """Test login endpoint works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.email, "password": self.password}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"PASS: Login successful for {self.email}")

    def test_create_setup_intent_returns_client_secret(self):
        """Test POST /api/create-setup-intent returns client_secret and customer_id"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.post(
            f"{BASE_URL}/api/create-setup-intent",
            headers=self.get_headers(),
            json={}
        )
        
        # Expect 200 OK
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure - must contain client_secret and customer_id
        assert "client_secret" in data, "Response must contain 'client_secret'"
        assert "customer_id" in data, "Response must contain 'customer_id'"
        
        # Verify client_secret format (starts with 'seti_' for SetupIntent)
        assert data["client_secret"].startswith("seti_"), "client_secret should start with 'seti_'"
        
        # Verify customer_id format (starts with 'cus_')
        assert data["customer_id"].startswith("cus_"), "customer_id should start with 'cus_'"
        
        print(f"PASS: create-setup-intent returned client_secret={data['client_secret'][:20]}... and customer_id={data['customer_id']}")

    def test_create_setup_intent_without_auth_fails(self):
        """Test POST /api/create-setup-intent requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/create-setup-intent",
            headers={"Content-Type": "application/json"},
            json={}
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401, f"Expected 401 but got {response.status_code}"
        print("PASS: create-setup-intent correctly requires authentication")

    def test_confirm_setup_intent_with_invalid_payment_method(self):
        """Test POST /api/confirm-setup-intent with invalid payment_method_id returns error"""
        if not self.token:
            pytest.skip("No auth token available")
        
        # Use a fake payment method ID
        response = requests.post(
            f"{BASE_URL}/api/confirm-setup-intent",
            headers=self.get_headers(),
            json={"payment_method_id": "pm_invalid_test_12345"}
        )
        
        # Should return 5xx error since the payment method doesn't exist in Stripe
        assert response.status_code >= 500, f"Expected 5xx for invalid pm but got {response.status_code}: {response.text}"
        print("PASS: confirm-setup-intent correctly rejects invalid payment_method_id")

    def test_confirm_setup_intent_without_payment_method_id(self):
        """Test POST /api/confirm-setup-intent requires payment_method_id"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.post(
            f"{BASE_URL}/api/confirm-setup-intent",
            headers=self.get_headers(),
            json={}
        )
        
        # Should return 422 Unprocessable Entity (validation error)
        assert response.status_code == 422, f"Expected 422 but got {response.status_code}: {response.text}"
        print("PASS: confirm-setup-intent correctly requires payment_method_id field")

    def test_confirm_setup_intent_without_auth_fails(self):
        """Test POST /api/confirm-setup-intent requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/confirm-setup-intent",
            headers={"Content-Type": "application/json"},
            json={"payment_method_id": "pm_test_12345"}
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401, f"Expected 401 but got {response.status_code}"
        print("PASS: confirm-setup-intent correctly requires authentication")

    def test_get_payment_method_endpoint_still_works(self):
        """Test GET /api/payment-method still returns correct structure"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(
            f"{BASE_URL}/api/payment-method",
            headers=self.get_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "has_payment_method" in data
        assert isinstance(data["has_payment_method"], bool)
        
        if data["has_payment_method"]:
            assert "payment_method" in data
            pm = data["payment_method"]
            assert "brand" in pm
            assert "last4" in pm
            assert "exp_month" in pm
            assert "exp_year" in pm
            print(f"PASS: Payment method found: {pm['brand']} ending in {pm['last4']}")
        else:
            print("PASS: No payment method configured (expected for test account)")

    def test_subscription_endpoint_works(self):
        """Test GET /api/subscription returns subscription details"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscription",
            headers=self.get_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify subscription structure
        assert "plan_id" in data or "status" in data
        print(f"PASS: Subscription status: {data.get('status', 'N/A')}, Plan: {data.get('plan_id', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
