"""
Test Partner PayPal Configuration and Payout Features
Tests for: PayPal configure, PayPal status, PayPal delete, Payout balance with paypal fields, Payout request with method
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PARTNER_EMAIL = "testpartner@test.com"
PARTNER_PASSWORD = "test123"


class TestPartnerPayPalAndPayouts:
    """Test PayPal configuration and payout endpoints for partners"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Login as partner user and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Partner login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        # Check if 2FA is required
        if data.get("requires_2fa"):
            pytest.skip("Partner user has 2FA enabled - cannot test without TOTP")
        
        token = data.get("access_token") or data.get("token")
        if not token:
            pytest.skip(f"No token in login response: {data}")
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, partner_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {partner_token}"}
    
    # === PayPal Status Tests ===
    
    def test_get_paypal_status(self, auth_headers):
        """GET /api/partners/paypal/status - Check PayPal configuration status"""
        response = requests.get(f"{BASE_URL}/api/partners/paypal/status", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "connected" in data, "Response should contain 'connected' field"
        assert "paypal_email" in data, "Response should contain 'paypal_email' field"
        print(f"PayPal Status: connected={data['connected']}, email={data.get('paypal_email')}")
    
    # === PayPal Configure Tests ===
    
    def test_configure_paypal_valid_email(self, auth_headers):
        """POST /api/partners/paypal/configure - Configure PayPal with valid email"""
        test_email = "partner_test@paypal.com"
        
        response = requests.post(
            f"{BASE_URL}/api/partners/paypal/configure",
            headers=auth_headers,
            json={"paypal_email": test_email}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert data.get("paypal_email") == test_email, f"Expected paypal_email={test_email}, got {data}"
        assert "message" in data, "Response should contain a message"
        print(f"PayPal configured successfully: {data}")
    
    def test_configure_paypal_verify_persistence(self, auth_headers):
        """Verify PayPal configuration persists after saving"""
        # Get status to verify the configuration was saved
        response = requests.get(f"{BASE_URL}/api/partners/paypal/status", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("connected") == True, "PayPal should be connected after configure"
        assert data.get("paypal_email") is not None, "paypal_email should not be None"
        print(f"PayPal verification: {data}")
    
    # === Payout Balance Tests ===
    
    def test_get_payout_balance_includes_paypal_fields(self, auth_headers):
        """GET /api/partners/payouts/balance - Should include paypal_connected and paypal_email"""
        response = requests.get(f"{BASE_URL}/api/partners/payouts/balance", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert "available_balance" in data, "Response should contain 'available_balance'"
        assert "total_earned" in data, "Response should contain 'total_earned'"
        assert "minimum_payout" in data, "Response should contain 'minimum_payout'"
        assert "can_withdraw" in data, "Response should contain 'can_withdraw'"
        
        # Verify PayPal fields
        assert "paypal_connected" in data, "Response should contain 'paypal_connected'"
        assert "paypal_email" in data, "Response should contain 'paypal_email'"
        assert "stripe_connected" in data, "Response should contain 'stripe_connected'"
        
        print(f"Payout Balance: available={data['available_balance']}, stripe_connected={data['stripe_connected']}, paypal_connected={data['paypal_connected']}")
    
    # === Connect Status Tests ===
    
    def test_get_connect_status_includes_paypal_fields(self, auth_headers):
        """GET /api/partners/connect/status - Should include paypal_email and paypal_connected"""
        response = requests.get(f"{BASE_URL}/api/partners/connect/status", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify Stripe fields
        assert "connected" in data, "Response should contain 'connected' (Stripe status)"
        assert "status" in data, "Response should contain 'status'"
        
        # Verify PayPal fields
        assert "paypal_email" in data, "Response should contain 'paypal_email'"
        assert "paypal_connected" in data, "Response should contain 'paypal_connected'"
        
        print(f"Connect Status: stripe={data.get('status')}, paypal_connected={data.get('paypal_connected')}")
    
    # === Payout Request Tests ===
    
    def test_payout_request_with_stripe_method(self, auth_headers):
        """POST /api/partners/payouts/request - Request payout via Stripe method"""
        response = requests.post(
            f"{BASE_URL}/api/partners/payouts/request",
            headers=auth_headers,
            json={"amount": 50.00, "method": "stripe"}
        )
        
        # Either 200 (success) or 400 (no balance or Stripe not active)
        if response.status_code == 200:
            data = response.json()
            assert data.get("method") == "stripe", "Method should be stripe"
            print(f"Stripe payout successful: {data}")
        elif response.status_code == 400:
            data = response.json()
            # Expected if balance < $50 or Stripe not configured
            print(f"Stripe payout rejected (expected if balance < $50 or Stripe not active): {data.get('detail')}")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")
    
    def test_payout_request_with_paypal_method(self, auth_headers):
        """POST /api/partners/payouts/request - Request payout via PayPal method"""
        response = requests.post(
            f"{BASE_URL}/api/partners/payouts/request",
            headers=auth_headers,
            json={"amount": 50.00, "method": "paypal"}
        )
        
        # Either 200 (success) or 400 (no balance)
        if response.status_code == 200:
            data = response.json()
            assert data.get("method") == "paypal", "Method should be paypal"
            assert "payout_id" in data, "Response should contain payout_id"
            print(f"PayPal payout successful: {data}")
        elif response.status_code == 400:
            data = response.json()
            # Expected if balance < $50
            print(f"PayPal payout rejected (expected if balance < $50): {data.get('detail')}")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")
    
    def test_payout_request_invalid_method(self, auth_headers):
        """POST /api/partners/payouts/request - Invalid method should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/partners/payouts/request",
            headers=auth_headers,
            json={"amount": 50.00, "method": "invalid_method"}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid method, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Should return error detail"
        print(f"Invalid method rejected correctly: {data.get('detail')}")
    
    def test_payout_request_default_method(self, auth_headers):
        """POST /api/partners/payouts/request - Default method should be stripe"""
        response = requests.post(
            f"{BASE_URL}/api/partners/payouts/request",
            headers=auth_headers,
            json={"amount": 50.00}  # No method specified
        )
        
        # Should default to stripe
        if response.status_code == 200:
            data = response.json()
            assert data.get("method") == "stripe", "Default method should be stripe"
        elif response.status_code == 400:
            # Expected if Stripe not configured or balance insufficient
            print(f"Default method (stripe) rejected: {response.json().get('detail')}")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")
    
    # === Payout History Tests ===
    
    def test_get_payout_history(self, auth_headers):
        """GET /api/partners/payouts/history - Should return payout history"""
        response = requests.get(f"{BASE_URL}/api/partners/payouts/history", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "payouts" in data, "Response should contain 'payouts' array"
        assert "summary" in data, "Response should contain 'summary'"
        
        # Check payout entries have method field if any exist
        for payout in data.get("payouts", [])[:3]:
            if "method" in payout:
                assert payout["method"] in ["stripe", "paypal"], f"Method should be stripe or paypal, got {payout['method']}"
        
        print(f"Payout history: {len(data.get('payouts', []))} entries")
    
    # === PayPal Remove Tests (run last) ===
    
    def test_remove_paypal_configuration(self, auth_headers):
        """DELETE /api/partners/paypal/configure - Remove PayPal configuration"""
        response = requests.delete(f"{BASE_URL}/api/partners/paypal/configure", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        print(f"PayPal removed: {data}")
    
    def test_verify_paypal_removed(self, auth_headers):
        """Verify PayPal is disconnected after removal"""
        response = requests.get(f"{BASE_URL}/api/partners/paypal/status", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("connected") == False, "PayPal should be disconnected after removal"
        assert data.get("paypal_email") is None, "paypal_email should be None after removal"
        print(f"PayPal removal verified: {data}")
    
    # === Restore PayPal for UI testing ===
    
    def test_restore_paypal_for_ui_testing(self, auth_headers):
        """Restore PayPal configuration for UI testing"""
        response = requests.post(
            f"{BASE_URL}/api/partners/paypal/configure",
            headers=auth_headers,
            json={"paypal_email": "partner@paypal.com"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PayPal restored for UI testing")


class TestPartnerDashboard:
    """Test partner dashboard endpoint"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Login as partner user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Partner login failed: {response.status_code}")
        
        data = response.json()
        if data.get("requires_2fa"):
            pytest.skip("Partner user has 2FA enabled")
        
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, partner_token):
        return {"Authorization": f"Bearer {partner_token}"}
    
    def test_get_dashboard_data(self, auth_headers):
        """GET /api/partners/dashboard - Get partner dashboard data"""
        response = requests.get(f"{BASE_URL}/api/partners/dashboard", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify expected fields for KPI cards
        assert "statistics" in data, "Dashboard should contain 'statistics'"
        assert "commissions" in data, "Dashboard should contain 'commissions'"
        assert "benefits" in data, "Dashboard should contain 'benefits'"
        assert "pricing" in data, "Dashboard should contain 'pricing'"
        
        stats = data.get("statistics", {})
        print(f"Dashboard Stats: active_clients={stats.get('active_clients')}, trial_clients={stats.get('trial_clients')}")
    
    def test_get_partner_clients(self, auth_headers):
        """GET /api/partners/clients - Get partner's clients"""
        response = requests.get(f"{BASE_URL}/api/partners/clients", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "clients" in data, "Response should contain 'clients' array"
        print(f"Partner has {len(data.get('clients', []))} clients")
    
    def test_get_commissions_summary(self, auth_headers):
        """GET /api/partners/commissions/summary - Get commissions summary"""
        response = requests.get(f"{BASE_URL}/api/partners/commissions/summary", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Commissions Summary: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
