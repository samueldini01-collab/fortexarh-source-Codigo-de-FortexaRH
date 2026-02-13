"""
Test Payment Method and Subscription Features - FortexaRH
Tests for: GET /payment-method, POST /update-payment-method, GET /invoices
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPaymentMethodFeatures:
    """Tests for payment method management features"""
    
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
        print(f"Login successful for {self.email}")
    
    def test_get_payment_method_endpoint(self):
        """Test GET /api/payment-method returns correct structure"""
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
            print(f"Payment method found: {pm['brand']} ending in {pm['last4']}")
        else:
            print("No payment method configured (expected for test account)")
    
    def test_update_payment_method_returns_checkout_url(self):
        """Test POST /api/update-payment-method returns Stripe checkout URL"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.post(
            f"{BASE_URL}/api/update-payment-method",
            headers=self.get_headers(),
            json={"origin_url": "https://fortexa-portal.preview.emergentagent.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "checkout_url" in data
        assert "session_id" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
        print(f"Stripe checkout URL generated successfully")
    
    def test_get_invoices_endpoint(self):
        """Test GET /api/invoices returns list"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=self.get_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        
        if len(data) > 0:
            invoice = data[0]
            # Verify invoice structure
            assert "invoice_id" in invoice or "invoice_number" in invoice
            print(f"Found {len(data)} invoices")
        else:
            print("No invoices found (expected for test account)")
    
    def test_get_subscription_endpoint(self):
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
        print(f"Subscription status: {data.get('status', 'N/A')}, Plan: {data.get('plan_id', 'N/A')}")
    
    def test_get_plans_endpoint(self):
        """Test GET /api/plans returns available plans"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(
            f"{BASE_URL}/api/plans",
            headers=self.get_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a list of plans
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify plan structure
        plan = data[0]
        assert "plan_id" in plan or "name" in plan
        print(f"Found {len(data)} subscription plans")


class TestLandingPageLoad:
    """Tests for landing page loading (no blank page issue)"""
    
    def test_landing_page_loads(self):
        """Test that landing page loads without blank screen"""
        response = requests.get(f"{BASE_URL}/")
        
        # Should return HTML content
        assert response.status_code == 200
        assert len(response.text) > 100
        print("Landing page loads successfully")
    
    def test_api_auth_endpoint_exists(self):
        """Test API auth endpoint is responsive"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "invalid"}
        )
        
        # Should return 401 for invalid credentials (not 500 or 404)
        assert response.status_code in [401, 400]
        print("API auth endpoint is responsive")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
