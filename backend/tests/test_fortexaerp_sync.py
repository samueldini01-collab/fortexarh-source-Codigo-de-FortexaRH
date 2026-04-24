"""
FortexaERP Sync Integration Tests
Tests for the new FortexaERP sync button in Accounting module
- POST /api/fortexaerp/sync-journal-entries
- GET /api/fortexaerp/sync-status/{period_id}
- GET /api/fortexaerp/config
- PUT /api/fortexaerp/config
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
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def auth_headers(auth_token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestFortexaERPConfig:
    """Tests for FortexaERP configuration endpoints"""
    
    def test_get_config_returns_configured_status(self, auth_headers):
        """GET /api/fortexaerp/config returns configured status"""
        response = requests.get(
            f"{BASE_URL}/api/fortexaerp/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert isinstance(data["configured"], bool)
        print(f"FortexaERP config status: configured={data['configured']}")
    
    def test_put_config_saves_settings(self, auth_headers):
        """PUT /api/fortexaerp/config saves API URL, email, password, company_id"""
        config_data = {
            "api_url": "https://fortexarh.com",
            "email": "test@fortexaerp.com",
            "password": "testpassword123",
            "company_id": "test-company-123"
        }
        response = requests.put(
            f"{BASE_URL}/api/fortexaerp/config",
            headers=auth_headers,
            json=config_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True
        print("FortexaERP config saved successfully")
    
    def test_get_config_after_save_returns_configured_true(self, auth_headers):
        """GET /api/fortexaerp/config after save returns configured=true"""
        response = requests.get(
            f"{BASE_URL}/api/fortexaerp/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] == True
        assert data.get("api_url") == "https://fortexarh.com"
        assert data.get("email") == "test@fortexaerp.com"
        assert data.get("company_id") == "test-company-123"
        print(f"FortexaERP config verified: {data}")
    
    def test_get_config_unauthenticated_returns_401(self):
        """GET /api/fortexaerp/config without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/fortexaerp/config")
        assert response.status_code == 401
        print("Unauthenticated request correctly rejected")


class TestFortexaERPSyncJournalEntries:
    """Tests for sync-journal-entries endpoint"""
    
    def test_sync_journal_entries_endpoint_exists(self, auth_headers):
        """POST /api/fortexaerp/sync-journal-entries endpoint accepts period_id"""
        # This will fail with external API error since credentials are not real
        # but we verify the endpoint exists and validates input
        response = requests.post(
            f"{BASE_URL}/api/fortexaerp/sync-journal-entries",
            headers=auth_headers,
            json={"period_id": "2025-01"}
        )
        # Expected: 404 (no journal entry for period) or 401/500 (external API error)
        # NOT 422 (validation error) or 405 (method not allowed)
        assert response.status_code in [200, 201, 400, 401, 404, 500, 502]
        print(f"sync-journal-entries response: {response.status_code} - {response.text[:200]}")
    
    def test_sync_journal_entries_requires_period_id(self, auth_headers):
        """POST /api/fortexaerp/sync-journal-entries requires period_id"""
        response = requests.post(
            f"{BASE_URL}/api/fortexaerp/sync-journal-entries",
            headers=auth_headers,
            json={}
        )
        # Should return 422 for missing required field
        assert response.status_code == 422
        print("Missing period_id correctly rejected with 422")
    
    def test_sync_journal_entries_returns_error_when_no_je(self, auth_headers):
        """POST /api/fortexaerp/sync-journal-entries returns error when no JE for period"""
        response = requests.post(
            f"{BASE_URL}/api/fortexaerp/sync-journal-entries",
            headers=auth_headers,
            json={"period_id": "1999-01"}  # Non-existent period
        )
        # Should return 404 for no journal entry found
        assert response.status_code in [400, 404]
        print(f"Non-existent period correctly handled: {response.status_code}")


class TestFortexaERPSyncStatus:
    """Tests for sync-status endpoint"""
    
    def test_sync_status_endpoint_exists(self, auth_headers):
        """GET /api/fortexaerp/sync-status/{period_id} returns sync status"""
        response = requests.get(
            f"{BASE_URL}/api/fortexaerp/sync-status/2025-01",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "synced" in data
        assert isinstance(data["synced"], bool)
        print(f"Sync status for 2025-01: {data}")
    
    def test_sync_status_returns_false_for_unsynced_period(self, auth_headers):
        """GET /api/fortexaerp/sync-status/{period_id} returns synced=false for unsynced period"""
        response = requests.get(
            f"{BASE_URL}/api/fortexaerp/sync-status/1999-12",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["synced"] == False
        print("Unsynced period correctly returns synced=false")


class TestFortexaERPTestConnection:
    """Tests for test-connection endpoint"""
    
    def test_test_connection_endpoint_exists(self, auth_headers):
        """POST /api/fortexaerp/test-connection endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/fortexaerp/test-connection",
            headers=auth_headers
        )
        # Expected: 401 (auth failed with external API) or 400 (not configured)
        # NOT 404 (endpoint not found) or 405 (method not allowed)
        assert response.status_code in [200, 400, 401, 500, 502]
        print(f"test-connection response: {response.status_code}")


class TestHealthCheck:
    """Basic health check"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("Health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
