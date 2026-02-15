"""
Partner API ObjectId Serialization Tests - FortexaRH
Tests that all partner endpoints return valid JSON without MongoDB ObjectId fields
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://payroll-refactor-lab.preview.emergentagent.com').rstrip('/')

class TestPartnerObjectIdSerialization:
    """Test that Partner API endpoints properly exclude _id fields"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Get partner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpartner@test.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Partner login failed: {response.text}"
        return response.json()["token"]
    
    def assert_no_objectid_in_response(self, data, path="root"):
        """Recursively check that no _id or ObjectId fields exist in response"""
        if isinstance(data, dict):
            for key, value in data.items():
                assert key != "_id", f"Found '_id' field at {path}.{key}"
                assert "ObjectId" not in str(value), f"Found ObjectId at {path}.{key}: {value}"
                self.assert_no_objectid_in_response(value, f"{path}.{key}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self.assert_no_objectid_in_response(item, f"{path}[{i}]")
    
    def test_partners_dashboard_no_objectid(self, partner_token):
        """GET /api/partners/dashboard should return valid JSON without _id"""
        response = requests.get(f"{BASE_URL}/api/partners/dashboard", 
            headers={"Authorization": f"Bearer {partner_token}"})
        
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "firm" in data
        assert "statistics" in data
        assert "commissions" in data
        assert "benefits" in data
        assert "pricing" in data
        assert "recent_clients" in data
        
        # Verify no ObjectId fields
        self.assert_no_objectid_in_response(data)
        print(f"SUCCESS: Dashboard response has {len(data.get('recent_clients', []))} recent clients")
    
    def test_partners_clients_no_objectid(self, partner_token):
        """GET /api/partners/clients should return valid JSON without _id"""
        response = requests.get(f"{BASE_URL}/api/partners/clients?limit=5", 
            headers={"Authorization": f"Bearer {partner_token}"})
        
        assert response.status_code == 200, f"Clients failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "clients" in data
        assert "total" in data
        
        # Verify no ObjectId fields
        self.assert_no_objectid_in_response(data)
        print(f"SUCCESS: Clients response has {len(data.get('clients', []))} clients")
    
    def test_partners_connect_status_no_objectid(self, partner_token):
        """GET /api/partners/connect/status should return valid JSON without _id"""
        response = requests.get(f"{BASE_URL}/api/partners/connect/status", 
            headers={"Authorization": f"Bearer {partner_token}"})
        
        assert response.status_code == 200, f"Connect status failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "connected" in data
        assert "status" in data
        assert "paypal_connected" in data
        
        # Verify no ObjectId fields
        self.assert_no_objectid_in_response(data)
        print(f"SUCCESS: Connect status - Stripe connected: {data.get('connected')}, PayPal: {data.get('paypal_connected')}")
    
    def test_partners_paypal_status_no_objectid(self, partner_token):
        """GET /api/partners/paypal/status should return valid JSON without _id"""
        response = requests.get(f"{BASE_URL}/api/partners/paypal/status", 
            headers={"Authorization": f"Bearer {partner_token}"})
        
        assert response.status_code == 200, f"PayPal status failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "connected" in data
        
        # Verify no ObjectId fields
        self.assert_no_objectid_in_response(data)
        print(f"SUCCESS: PayPal status - connected: {data.get('connected')}")
    
    def test_partners_payouts_balance_no_objectid(self, partner_token):
        """GET /api/partners/payouts/balance should return valid JSON without _id"""
        response = requests.get(f"{BASE_URL}/api/partners/payouts/balance", 
            headers={"Authorization": f"Bearer {partner_token}"})
        
        assert response.status_code == 200, f"Payout balance failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "available_balance" in data
        assert "total_earned" in data
        assert "minimum_payout" in data
        assert "can_withdraw" in data
        
        # Verify no ObjectId fields
        self.assert_no_objectid_in_response(data)
        print(f"SUCCESS: Payout balance - available: ${data.get('available_balance')}")
    
    def test_partners_payouts_history_no_objectid(self, partner_token):
        """GET /api/partners/payouts/history should return valid JSON without _id"""
        response = requests.get(f"{BASE_URL}/api/partners/payouts/history", 
            headers={"Authorization": f"Bearer {partner_token}"})
        
        assert response.status_code == 200, f"Payout history failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "payouts" in data
        assert "summary" in data
        assert "minimum_payout" in data
        
        # Verify no ObjectId fields
        self.assert_no_objectid_in_response(data)
        print(f"SUCCESS: Payout history - {len(data.get('payouts', []))} payouts")


class TestPartnerAuthentication:
    """Test partner and admin user authentication"""
    
    def test_partner_login_redirects_to_partner_dashboard(self):
        """Partner user should login successfully with correct user type"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpartner@test.com",
            "password": "test123"
        })
        
        assert response.status_code == 200, f"Partner login failed: {response.text}"
        data = response.json()
        
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_partner"] == True
        assert data["user"]["role"] == "partner_admin"
        assert data["user"]["partner_id"] is not None
        print(f"SUCCESS: Partner login - user_id: {data['user']['user_id']}, partner_id: {data['user']['partner_id']}")
    
    def test_admin_login_success(self):
        """Admin user should login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_partner"] == False
        assert data["user"]["role"] == "admin"
        print(f"SUCCESS: Admin login - user_id: {data['user']['user_id']}")
    
    def test_invalid_credentials_rejected(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("SUCCESS: Invalid credentials correctly rejected with 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
