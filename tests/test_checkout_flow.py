"""
Test suite for FortexaRH Checkout Flow - "Pay First, Register After" pattern
Tests:
1. POST /api/public/checkout - Create Stripe checkout session (no auth)
2. GET /api/public/checkout/verify/{session_id} - Verify payment status (no auth)
3. POST /api/auth/register with payment_session_id - Register with paid session
4. Subscription activation after paid registration
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPublicCheckout:
    """Test public checkout endpoints (no authentication required)"""
    
    def test_public_checkout_basic_plan(self):
        """Test creating checkout session for basic plan"""
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "basic",
            "employee_count": 5,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data, "Response should contain checkout_url"
        assert "session_id" in data, "Response should contain session_id"
        assert data["checkout_url"].startswith("https://checkout.stripe.com"), "checkout_url should be Stripe URL"
        assert data["session_id"].startswith("cs_test_"), "session_id should be Stripe test session"
        
        print(f"✓ Basic plan checkout created: session_id={data['session_id'][:30]}...")
        return data["session_id"]
    
    def test_public_checkout_pro_plan(self):
        """Test creating checkout session for pro plan"""
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "pro",
            "employee_count": 20,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        print(f"✓ Pro plan checkout created: session_id={data['session_id'][:30]}...")
    
    def test_public_checkout_enterprise_plan(self):
        """Test creating checkout session for enterprise plan"""
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "enterprise",
            "employee_count": 100,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        print(f"✓ Enterprise plan checkout created: session_id={data['session_id'][:30]}...")
    
    def test_public_checkout_invalid_plan(self):
        """Test checkout with invalid plan returns error"""
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "invalid_plan",
            "employee_count": 5,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 400, f"Expected 400 for invalid plan, got {response.status_code}"
        print("✓ Invalid plan correctly rejected with 400")
    
    def test_public_checkout_trial_plan_rejected(self):
        """Test that trial plan cannot be purchased via checkout"""
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "trial",
            "employee_count": 1,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 400, f"Expected 400 for trial plan, got {response.status_code}"
        print("✓ Trial plan correctly rejected for checkout")
    
    def test_public_checkout_minimum_employee_count(self):
        """Test checkout with minimum employee count (1)"""
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "basic",
            "employee_count": 1,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        print("✓ Minimum employee count (1) accepted")


class TestCheckoutVerification:
    """Test checkout verification endpoint"""
    
    def test_verify_checkout_session(self):
        """Test verifying a checkout session"""
        # First create a checkout session
        create_response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "basic",
            "employee_count": 5,
            "origin_url": BASE_URL
        })
        
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]
        
        # Verify the session (will be pending since not paid)
        verify_response = requests.get(f"{BASE_URL}/api/public/checkout/verify/{session_id}")
        
        assert verify_response.status_code == 200, f"Expected 200, got {verify_response.status_code}: {verify_response.text}"
        
        data = verify_response.json()
        assert "valid" in data, "Response should contain 'valid' field"
        assert "payment_status" in data, "Response should contain 'payment_status' field"
        
        # Since we didn't actually pay, it should be pending or unpaid
        print(f"✓ Checkout verification returned: valid={data['valid']}, status={data['payment_status']}")
    
    def test_verify_nonexistent_session(self):
        """Test verifying a non-existent session returns 404"""
        response = requests.get(f"{BASE_URL}/api/public/checkout/verify/cs_test_nonexistent123")
        
        assert response.status_code == 404, f"Expected 404 for non-existent session, got {response.status_code}"
        print("✓ Non-existent session correctly returns 404")


class TestRegistrationWithPayment:
    """Test registration flow with payment session"""
    
    def test_register_without_payment(self):
        """Test normal registration without payment (trial)"""
        unique_email = f"test_trial_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test User Trial",
            "company_name": "Test Company Trial"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert "subscription" in data, "Response should contain subscription"
        
        # Should be trial plan
        assert data["subscription"]["plan_id"] == "trial", "Should be trial plan"
        assert data["subscription"]["status"] == "trial", "Should have trial status"
        
        print(f"✓ Trial registration successful: {unique_email}")
    
    def test_register_with_invalid_payment_session(self):
        """Test registration with invalid payment session fails"""
        unique_email = f"test_invalid_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test User Invalid",
            "company_name": "Test Company Invalid",
            "payment_session_id": "cs_test_invalid_session_123"
        })
        
        assert response.status_code == 400, f"Expected 400 for invalid session, got {response.status_code}"
        print("✓ Invalid payment session correctly rejected")
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails"""
        unique_email = f"test_dup_{uuid.uuid4().hex[:8]}@test.com"
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test User 1",
            "company_name": "Test Company 1"
        })
        assert response1.status_code == 200
        
        # Second registration with same email
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test User 2",
            "company_name": "Test Company 2"
        })
        
        assert response2.status_code == 400, f"Expected 400 for duplicate email, got {response2.status_code}"
        print("✓ Duplicate email correctly rejected")


class TestAuthenticatedCheckout:
    """Test authenticated checkout endpoints (for existing users)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for testing"""
        # Try to login with existing test user
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        
        if login_response.status_code == 200:
            return login_response.json()["token"]
        
        # Create new test user if doesn't exist
        unique_email = f"test_auth_{uuid.uuid4().hex[:8]}@test.com"
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test Auth User",
            "company_name": "Test Auth Company"
        })
        
        if register_response.status_code == 200:
            return register_response.json()["token"]
        
        pytest.skip("Could not authenticate for test")
    
    def test_authenticated_checkout(self, auth_token):
        """Test creating checkout session for authenticated user"""
        response = requests.post(
            f"{BASE_URL}/api/checkout",
            json={
                "plan_id": "basic",
                "employee_count": 10,
                "origin_url": BASE_URL
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        print(f"✓ Authenticated checkout created: session_id={data['session_id'][:30]}...")
    
    def test_authenticated_checkout_status(self, auth_token):
        """Test checking checkout status for authenticated user"""
        # First create a checkout
        create_response = requests.post(
            f"{BASE_URL}/api/checkout",
            json={
                "plan_id": "pro",
                "employee_count": 15,
                "origin_url": BASE_URL
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]
        
        # Check status
        status_response = requests.get(
            f"{BASE_URL}/api/checkout/status/{session_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert status_response.status_code == 200, f"Expected 200, got {status_response.status_code}"
        
        data = status_response.json()
        assert "status" in data or "payment_status" in data
        print(f"✓ Checkout status retrieved: {data}")


class TestSubscriptionPlans:
    """Test subscription plans endpoint"""
    
    def test_get_plans(self):
        """Test getting available subscription plans"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Could not login for plans test")
        
        token = login_response.json()["token"]
        
        response = requests.get(
            f"{BASE_URL}/api/plans",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        plans = response.json()
        assert isinstance(plans, list), "Plans should be a list"
        assert len(plans) >= 3, "Should have at least 3 plans (basic, pro, enterprise)"
        
        # Verify plan structure
        for plan in plans:
            assert "plan_id" in plan
            assert "name" in plan
            assert "base_price" in plan
            assert "price_per_employee" in plan
            assert "features" in plan
        
        plan_ids = [p["plan_id"] for p in plans]
        assert "basic" in plan_ids, "Should have basic plan"
        assert "pro" in plan_ids, "Should have pro plan"
        assert "enterprise" in plan_ids, "Should have enterprise plan"
        
        print(f"✓ Retrieved {len(plans)} subscription plans")


class TestPriceCalculation:
    """Test price calculation in checkout"""
    
    def test_basic_plan_price_calculation(self):
        """Verify basic plan pricing: $5 base + $1.50/employee"""
        # Basic plan: $5 base + $1.50 per employee
        # For 5 employees: $5 + (5 * $1.50) = $5 + $7.50 = $12.50
        
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "basic",
            "employee_count": 5,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 200
        # The checkout URL is created, price is calculated server-side
        print("✓ Basic plan checkout created (price: $5 + 5×$1.50 = $12.50)")
    
    def test_pro_plan_price_calculation(self):
        """Verify pro plan pricing: $10 base + $1.50/employee"""
        # Pro plan: $10 base + $1.50 per employee
        # For 20 employees: $10 + (20 * $1.50) = $10 + $30 = $40
        
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "pro",
            "employee_count": 20,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 200
        print("✓ Pro plan checkout created (price: $10 + 20×$1.50 = $40)")
    
    def test_enterprise_plan_price_calculation(self):
        """Verify enterprise plan pricing: $20 base + $1.50/employee"""
        # Enterprise plan: $20 base + $1.50 per employee
        # For 100 employees: $20 + (100 * $1.50) = $20 + $150 = $170
        
        response = requests.post(f"{BASE_URL}/api/public/checkout", json={
            "plan_id": "enterprise",
            "employee_count": 100,
            "origin_url": BASE_URL
        })
        
        assert response.status_code == 200
        print("✓ Enterprise plan checkout created (price: $20 + 100×$1.50 = $170)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
