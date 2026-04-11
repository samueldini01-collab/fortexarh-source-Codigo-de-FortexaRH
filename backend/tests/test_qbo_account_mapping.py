"""
QBO Account Mapping Tests
Tests for QuickBooks Online account caching, auto-match, and mapping features
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestQBOAccountMapping:
    """Tests for QBO Account Mapping features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_01_quickbooks_connection_status(self):
        """GET /api/quickbooks/status should return connection info"""
        response = requests.get(
            f"{BASE_URL}/api/quickbooks/status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Status check failed: {response.text}"
        
        data = response.json()
        assert "connected" in data
        # In preview, QBO is connected but token is expired
        assert data["connected"] == True
        assert "company_name" in data
        print(f"QBO Status: connected={data['connected']}, company={data.get('company_name')}")
    
    def test_02_get_cached_accounts(self):
        """GET /api/quickbooks/accounts should return cached accounts when token expired"""
        response = requests.get(
            f"{BASE_URL}/api/quickbooks/accounts",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get accounts failed: {response.text}"
        
        data = response.json()
        assert "accounts" in data
        assert "source" in data
        # Should be from cache since token is expired
        assert data["source"] == "cache", f"Expected source='cache', got '{data['source']}'"
        assert len(data["accounts"]) > 0, "No accounts returned"
        
        # Verify account structure
        first_account = data["accounts"][0]
        assert "id" in first_account
        assert "name" in first_account
        assert "type" in first_account
        
        print(f"Accounts source: {data['source']}, count: {len(data['accounts'])}")
    
    def test_03_auto_match_accounts(self):
        """POST /api/quickbooks/auto-match should return suggestions with matched_count > 0"""
        response = requests.post(
            f"{BASE_URL}/api/quickbooks/auto-match",
            headers=self.headers,
            json={}
        )
        assert response.status_code == 200, f"Auto-match failed: {response.text}"
        
        data = response.json()
        assert "suggestions" in data
        assert "matched_count" in data
        assert "total_concepts" in data
        
        # Should match at least some accounts
        assert data["matched_count"] > 0, "No accounts were auto-matched"
        assert data["total_concepts"] == 10, f"Expected 10 concepts, got {data['total_concepts']}"
        
        # Verify all 10 concepts are matched
        assert data["matched_count"] == 10, f"Expected 10 matched, got {data['matched_count']}"
        
        # Verify suggestion structure
        for key, suggestion in data["suggestions"].items():
            assert "id" in suggestion, f"Missing 'id' in suggestion for {key}"
            assert "name" in suggestion, f"Missing 'name' in suggestion for {key}"
            assert "score" in suggestion, f"Missing 'score' in suggestion for {key}"
        
        print(f"Auto-match: {data['matched_count']} of {data['total_concepts']} concepts matched")
    
    def test_04_get_account_mapping(self):
        """GET /api/quickbooks/account-mapping should return saved mapping"""
        response = requests.get(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get mapping failed: {response.text}"
        
        data = response.json()
        assert "company_id" in data or "accounts" in data
        print(f"Current mapping: {len(data.get('accounts', {}))} accounts configured")
    
    def test_05_save_account_mapping(self):
        """PUT /api/quickbooks/account-mapping should save mapping"""
        # First get auto-match suggestions
        auto_match_response = requests.post(
            f"{BASE_URL}/api/quickbooks/auto-match",
            headers=self.headers,
            json={}
        )
        suggestions = auto_match_response.json().get("suggestions", {})
        
        # Convert suggestions to mapping format
        mapping = {}
        for key, suggestion in suggestions.items():
            mapping[key] = {"id": suggestion["id"], "name": suggestion["name"]}
        
        # Save the mapping
        response = requests.put(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=self.headers,
            json={"accounts": mapping}
        )
        assert response.status_code == 200, f"Save mapping failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        print(f"Mapping saved: {data.get('message')}")
        
        # Verify mapping was saved
        verify_response = requests.get(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=self.headers
        )
        verify_data = verify_response.json()
        assert len(verify_data.get("accounts", {})) == len(mapping), "Mapping not saved correctly"
    
    def test_06_accounts_have_required_fields(self):
        """Verify cached accounts have all required fields for mapping UI"""
        response = requests.get(
            f"{BASE_URL}/api/quickbooks/accounts",
            headers=self.headers
        )
        data = response.json()
        
        required_fields = ["id", "name", "full_name", "type", "classification"]
        
        for account in data["accounts"]:
            for field in required_fields:
                assert field in account, f"Account missing required field: {field}"
        
        # Verify we have accounts of different classifications for mapping
        classifications = set(a["classification"] for a in data["accounts"])
        assert "Expense" in classifications, "No Expense accounts for payroll mapping"
        assert "Liability" in classifications, "No Liability accounts for TSS mapping"
        assert "Asset" in classifications, "No Asset accounts for bank mapping"
        
        print(f"Account classifications: {classifications}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
