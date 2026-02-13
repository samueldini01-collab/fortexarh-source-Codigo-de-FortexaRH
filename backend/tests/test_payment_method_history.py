"""
Test Payment Method History Feature - FortexaRH
Tests the new GET /api/payment-method/history endpoint and confirm-setup-intent logging
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and get token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPaymentMethodHistoryEndpoint:
    """Tests for GET /api/payment-method/history"""

    def test_history_endpoint_requires_auth(self):
        """Test that history endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/payment-method/history")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422 without auth, got {response.status_code}"
        print("✅ History endpoint correctly requires authentication")

    def test_history_endpoint_returns_array(self, auth_headers):
        """Test that history endpoint returns an array (empty or with records)"""
        response = requests.get(
            f"{BASE_URL}/api/payment-method/history",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✅ History endpoint returns array with {len(data)} records")

    def test_history_record_structure(self, auth_headers):
        """Test that history records have expected structure if any exist"""
        response = requests.get(
            f"{BASE_URL}/api/payment-method/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            record = data[0]
            # Check expected fields
            expected_fields = ['company_id', 'change_type', 'new_card', 'changed_at']
            for field in expected_fields:
                assert field in record, f"Missing field: {field}"
            
            # Check change_type is valid
            assert record['change_type'] in ['added', 'updated'], f"Invalid change_type: {record['change_type']}"
            
            # Check new_card structure
            if record.get('new_card'):
                new_card = record['new_card']
                assert 'brand' in new_card
                assert 'last4' in new_card
            
            print(f"✅ History record has correct structure: change_type={record['change_type']}")
        else:
            print("✅ History endpoint works (no records yet - expected for fresh account)")


class TestConfirmSetupIntentLogging:
    """Tests for POST /api/confirm-setup-intent logging behavior"""

    def test_confirm_setup_intent_requires_auth(self):
        """Test that confirm-setup-intent requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/confirm-setup-intent",
            json={"payment_method_id": "pm_test_123"}
        )
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print("✅ confirm-setup-intent correctly requires authentication")

    def test_confirm_setup_intent_requires_payment_method_id(self, auth_headers):
        """Test that confirm-setup-intent requires payment_method_id"""
        response = requests.post(
            f"{BASE_URL}/api/confirm-setup-intent",
            headers=auth_headers,
            json={}
        )
        # Should fail validation without payment_method_id
        assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
        print("✅ confirm-setup-intent correctly requires payment_method_id")

    def test_confirm_setup_intent_with_invalid_pm(self, auth_headers):
        """Test confirm-setup-intent with invalid payment method ID"""
        response = requests.post(
            f"{BASE_URL}/api/confirm-setup-intent",
            headers=auth_headers,
            json={"payment_method_id": "pm_invalid_test_123456"}
        )
        # Should fail when trying to use invalid payment method
        # Stripe will return an error which will result in 500 (or 520 from Cloudflare)
        assert response.status_code in [400, 404, 500, 520], f"Expected error for invalid PM, got {response.status_code}"
        print(f"✅ confirm-setup-intent correctly handles invalid payment method (status: {response.status_code})")


class TestPaymentMethodEndpoint:
    """Tests for existing GET /api/payment-method"""

    def test_payment_method_requires_auth(self):
        """Test that payment-method endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/payment-method")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print("✅ payment-method endpoint correctly requires authentication")

    def test_payment_method_returns_correct_structure(self, auth_headers):
        """Test that payment-method returns expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/payment-method",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'has_payment_method' in data, "Missing has_payment_method field"
        assert 'payment_method' in data, "Missing payment_method field"
        
        if data['has_payment_method'] and data['payment_method']:
            pm = data['payment_method']
            assert 'brand' in pm, "Missing brand in payment_method"
            assert 'last4' in pm, "Missing last4 in payment_method"
            assert 'exp_month' in pm, "Missing exp_month in payment_method"
            assert 'exp_year' in pm, "Missing exp_year in payment_method"
            print(f"✅ Payment method found: {pm['brand']} ****{pm['last4']}")
        else:
            print("✅ No payment method configured (expected for test account)")


class TestCreateSetupIntent:
    """Tests for POST /api/create-setup-intent"""

    def test_create_setup_intent_requires_auth(self):
        """Test that create-setup-intent requires authentication"""
        response = requests.post(f"{BASE_URL}/api/create-setup-intent")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print("✅ create-setup-intent correctly requires authentication")

    def test_create_setup_intent_returns_client_secret(self, auth_headers):
        """Test that create-setup-intent returns client_secret and customer_id"""
        response = requests.post(
            f"{BASE_URL}/api/create-setup-intent",
            headers=auth_headers
        )
        # May fail if no subscription exists, which is acceptable
        if response.status_code == 404:
            print("✅ create-setup-intent returns 404 (no subscription - expected for test account)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'client_secret' in data, "Missing client_secret"
        assert 'customer_id' in data, "Missing customer_id"
        assert data['client_secret'].startswith('seti_'), f"client_secret should start with 'seti_', got: {data['client_secret'][:20]}..."
        assert data['customer_id'].startswith('cus_'), f"customer_id should start with 'cus_', got: {data['customer_id']}"
        
        print(f"✅ create-setup-intent returns valid client_secret and customer_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
