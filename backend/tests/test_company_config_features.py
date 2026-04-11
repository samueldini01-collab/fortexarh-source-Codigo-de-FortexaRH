"""
Test Company Config Features - Iteration 219
Tests for:
1. Company ID field in company settings
2. FortexaERP auto-sync toggle endpoint
3. SAP/Oracle logo static assets
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCompanyConfigFeatures:
    """Tests for Company Config page features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        # Login to get auth token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_refactor@fortexa.com", "password": "test123"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # ========== Company ID Tests ==========
    
    def test_company_settings_returns_company_id(self):
        """GET /api/company/settings should return company_id in company object"""
        response = requests.get(
            f"{BASE_URL}/api/company/settings",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify company object exists
        assert "company" in data, "Response missing 'company' object"
        
        # Verify company_id field exists
        company = data["company"]
        assert "company_id" in company, "Company object missing 'company_id' field"
        
        # Verify company_id has expected format
        company_id = company["company_id"]
        assert company_id.startswith("comp_"), f"Company ID should start with 'comp_', got: {company_id}"
        print(f"✓ Company ID returned: {company_id}")
    
    # ========== FortexaERP Auto-Sync Tests ==========
    
    def test_fortexaerp_config_returns_auto_sync_field(self):
        """GET /api/fortexaerp/config should return auto_sync field"""
        response = requests.get(
            f"{BASE_URL}/api/fortexaerp/config",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # auto_sync field should exist (either true or false)
        assert "auto_sync" in data, "Response missing 'auto_sync' field"
        assert isinstance(data["auto_sync"], bool), "auto_sync should be boolean"
        print(f"✓ auto_sync field returned: {data['auto_sync']}")
    
    def test_fortexaerp_auto_sync_toggle_enable(self):
        """PUT /api/fortexaerp/auto-sync should enable auto_sync"""
        response = requests.put(
            f"{BASE_URL}/api/fortexaerp/auto-sync",
            headers=self.headers,
            json={"enabled": True}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("ok") == True, "Response should have ok=true"
        assert data.get("auto_sync") == True, "auto_sync should be true"
        print("✓ Auto-sync enabled successfully")
        
        # Verify it was persisted
        config_response = requests.get(
            f"{BASE_URL}/api/fortexaerp/config",
            headers=self.headers
        )
        assert config_response.status_code == 200
        assert config_response.json().get("auto_sync") == True, "auto_sync not persisted"
        print("✓ Auto-sync=true persisted in config")
    
    def test_fortexaerp_auto_sync_toggle_disable(self):
        """PUT /api/fortexaerp/auto-sync should disable auto_sync"""
        response = requests.put(
            f"{BASE_URL}/api/fortexaerp/auto-sync",
            headers=self.headers,
            json={"enabled": False}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("ok") == True, "Response should have ok=true"
        assert data.get("auto_sync") == False, "auto_sync should be false"
        print("✓ Auto-sync disabled successfully")
        
        # Verify it was persisted
        config_response = requests.get(
            f"{BASE_URL}/api/fortexaerp/config",
            headers=self.headers
        )
        assert config_response.status_code == 200
        assert config_response.json().get("auto_sync") == False, "auto_sync not persisted"
        print("✓ Auto-sync=false persisted in config")
    
    def test_fortexaerp_auto_sync_requires_auth(self):
        """PUT /api/fortexaerp/auto-sync should require authentication"""
        response = requests.put(
            f"{BASE_URL}/api/fortexaerp/auto-sync",
            json={"enabled": True}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Auto-sync endpoint requires authentication")
    
    # ========== Static Asset Tests ==========
    
    def test_sap_logo_accessible(self):
        """SAP logo static asset should be accessible"""
        response = requests.get(f"{BASE_URL}/sap-logo.png")
        assert response.status_code == 200, f"SAP logo not accessible: {response.status_code}"
        assert "image" in response.headers.get("content-type", ""), "SAP logo should be an image"
        print("✓ SAP logo accessible at /sap-logo.png")
    
    def test_oracle_logo_accessible(self):
        """Oracle logo static asset should be accessible"""
        response = requests.get(f"{BASE_URL}/oracle-logo.png")
        assert response.status_code == 200, f"Oracle logo not accessible: {response.status_code}"
        assert "image" in response.headers.get("content-type", ""), "Oracle logo should be an image"
        print("✓ Oracle logo accessible at /oracle-logo.png")
    
    def test_fortexaerp_logo_accessible(self):
        """FortexaERP logo static asset should be accessible"""
        response = requests.get(f"{BASE_URL}/fortexaerp-logo.png")
        assert response.status_code == 200, f"FortexaERP logo not accessible: {response.status_code}"
        assert "image" in response.headers.get("content-type", ""), "FortexaERP logo should be an image"
        print("✓ FortexaERP logo accessible at /fortexaerp-logo.png")
    
    def test_quickbooks_logo_accessible(self):
        """QuickBooks logo static asset should be accessible"""
        response = requests.get(f"{BASE_URL}/quickbooks-logo.jpg")
        assert response.status_code == 200, f"QuickBooks logo not accessible: {response.status_code}"
        assert "image" in response.headers.get("content-type", ""), "QuickBooks logo should be an image"
        print("✓ QuickBooks logo accessible at /quickbooks-logo.jpg")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
