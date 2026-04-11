"""
Test FortexaERP sync-status endpoint and ERP indicator feature
Tests: GET /api/fortexaerp/sync-status/{period_id}
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFortexaERPSyncStatus:
    """Tests for FortexaERP sync status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_refactor@fortexa.com", "password": "test123"}
        )
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed - skipping tests")
    
    def test_sync_status_endpoint_exists(self):
        """Test that GET /api/fortexaerp/sync-status/{period_id} endpoint exists"""
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-status/2025-01")
        # Should return 200 with synced status (not 404 or 405)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_sync_status_returns_correct_structure(self):
        """Test that sync-status returns {synced: bool, erp_entry_id, synced_at}"""
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-status/2025-01")
        assert response.status_code == 200
        
        data = response.json()
        # Must have 'synced' field
        assert "synced" in data, f"Response missing 'synced' field: {data}"
        assert isinstance(data["synced"], bool), f"'synced' should be boolean: {data}"
        
        # If synced is True, should have erp_entry_id and synced_at
        if data["synced"]:
            assert "erp_entry_id" in data, f"Synced entry missing 'erp_entry_id': {data}"
            assert "synced_at" in data, f"Synced entry missing 'synced_at': {data}"
    
    def test_sync_status_unsynced_period(self):
        """Test sync-status for a period that hasn't been synced"""
        # Use a period that likely doesn't exist
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-status/1999-01")
        assert response.status_code == 200
        
        data = response.json()
        assert data["synced"] == False, f"Non-existent period should return synced=False: {data}"
    
    def test_sync_status_requires_auth(self):
        """Test that sync-status endpoint requires authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        response = unauth_session.get(f"{BASE_URL}/api/fortexaerp/sync-status/2025-01")
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
    
    def test_erp_config_endpoint(self):
        """Test GET /api/fortexaerp/config returns configuration status"""
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data, f"Response missing 'configured' field: {data}"
        assert isinstance(data["configured"], bool)
        
        # If configured, should have additional fields
        if data["configured"]:
            assert "api_url" in data
            assert "email" in data


class TestFortexaERPLogoAsset:
    """Test that FortexaERP logo static asset is accessible"""
    
    def test_fortexaerp_logo_accessible(self):
        """Test that /fortexaerp-logo.png is accessible from frontend"""
        response = requests.get(f"{BASE_URL}/fortexaerp-logo.png")
        assert response.status_code == 200, f"FortexaERP logo not accessible: {response.status_code}"
        assert "image" in response.headers.get("Content-Type", ""), "Logo should be an image"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
