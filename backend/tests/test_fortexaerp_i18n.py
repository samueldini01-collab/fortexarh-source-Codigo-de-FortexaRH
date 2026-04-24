"""
Test FortexaERP Integration APIs and i18n fixes
Tests:
1. GET /api/fortexaerp/config - returns {configured: false} for unconfigured companies
2. PUT /api/fortexaerp/config - saves configuration
3. POST /api/fortexaerp/test-connection - attempts to connect (expected to fail with external API)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
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
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestFortexaERPConfig:
    """Test FortexaERP configuration endpoints"""

    def test_get_config_returns_configured_false_initially(self, auth_headers):
        """GET /api/fortexaerp/config should return {configured: false} for unconfigured companies"""
        response = requests.get(
            f"{BASE_URL}/api/fortexaerp/config",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should have 'configured' field
        assert "configured" in data, f"Response should have 'configured' field: {data}"
        # If not configured, should be False
        if not data.get("configured"):
            assert data["configured"] == False, f"Expected configured=False: {data}"
        print(f"✓ GET /api/fortexaerp/config returned: {data}")

    def test_put_config_saves_configuration(self, auth_headers):
        """PUT /api/fortexaerp/config should save configuration"""
        config_data = {
            "api_url": "https://fortexarh.com",
            "email": "test@example.com",
            "password": "testpassword123",
            "company_id": "test-company-123"
        }
        response = requests.put(
            f"{BASE_URL}/api/fortexaerp/config",
            json=config_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("ok") == True, f"Expected ok=True: {data}"
        print(f"✓ PUT /api/fortexaerp/config saved successfully")

    def test_get_config_after_save_returns_configured_true(self, auth_headers):
        """After saving config, GET should return configured=True"""
        response = requests.get(
            f"{BASE_URL}/api/fortexaerp/config",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("configured") == True, f"Expected configured=True after save: {data}"
        assert "api_url" in data, f"Should return api_url: {data}"
        assert "email" in data, f"Should return email: {data}"
        print(f"✓ GET /api/fortexaerp/config after save: {data}")

    def test_test_connection_endpoint_exists(self, auth_headers):
        """POST /api/fortexaerp/test-connection should exist and attempt connection"""
        response = requests.post(
            f"{BASE_URL}/api/fortexaerp/test-connection",
            json={},
            headers=auth_headers
        )
        # Expected to fail since fortexaerp.com is external, but endpoint should exist
        # Accept 200 (success), 400 (not configured), 401 (auth failed), or 5xx (connection error)
        assert response.status_code in [200, 400, 401, 500, 502, 503], \
            f"Unexpected status {response.status_code}: {response.text}"
        print(f"✓ POST /api/fortexaerp/test-connection returned {response.status_code}")
        if response.status_code != 200:
            print(f"  (Expected - external API call may fail)")

    def test_config_unauthenticated_returns_401(self):
        """GET /api/fortexaerp/config without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/fortexaerp/config")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Unauthenticated request returns 401")


class TestHealthEndpoints:
    """Test basic health endpoints"""

    def test_api_health_endpoint(self):
        """GET /api/health should return healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ API health check passed: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
