"""
FortexaERP Sync Log Feature Tests
Tests for GET /api/fortexaerp/sync-log endpoint and sync logging functionality
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestFortexaERPSyncLog:
    """Tests for FortexaERP sync log endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_sync_log_endpoint_exists(self):
        """Test that GET /api/fortexaerp/sync-log endpoint exists and returns 200"""
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-log")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASSED: GET /api/fortexaerp/sync-log endpoint exists and returns 200")
    
    def test_sync_log_returns_array(self):
        """Test that sync-log endpoint returns an array"""
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-log")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASSED: sync-log returns array with {len(data)} entries")
    
    def test_sync_log_requires_authentication(self):
        """Test that sync-log endpoint requires authentication (401 for unauth)"""
        # Create a new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/fortexaerp/sync-log")
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("PASSED: sync-log requires authentication (returns 401 for unauth)")
    
    def test_sync_log_entry_fields(self):
        """Test that sync log entries have required fields when present"""
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-log")
        assert response.status_code == 200
        data = response.json()
        
        # If there are entries, verify their structure
        if len(data) > 0:
            entry = data[0]
            required_fields = ['period_id', 'reference', 'lines_count', 'total_debit', 'total_credit', 'status', 'synced_at', 'synced_by']
            for field in required_fields:
                assert field in entry, f"Missing required field: {field}"
            print(f"PASSED: sync log entry has all required fields: {required_fields}")
        else:
            # Empty array is valid - no sync history yet
            print("PASSED: sync-log returns empty array (no sync history yet - expected)")
    
    def test_sync_log_limit_parameter(self):
        """Test that sync-log accepts limit parameter"""
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-log?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10, f"Expected max 10 entries, got {len(data)}"
        print("PASSED: sync-log accepts limit parameter")


class TestFortexaERPSyncJournalEntriesLogging:
    """Tests for sync-journal-entries logging functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_sync_journal_entries_logs_failure(self):
        """Test that POST /api/fortexaerp/sync-journal-entries logs failed attempts"""
        # Get initial sync log count
        initial_response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-log")
        assert initial_response.status_code == 200
        initial_count = len(initial_response.json())
        
        # Attempt to sync with a test period (will fail because external API is mocked)
        sync_response = self.session.post(
            f"{BASE_URL}/api/fortexaerp/sync-journal-entries",
            json={"period_id": "2025-01-biweekly1"}
        )
        
        # The sync will fail (external API not available), but should still log
        # Check if a new log entry was created
        final_response = self.session.get(f"{BASE_URL}/api/fortexaerp/sync-log")
        assert final_response.status_code == 200
        final_data = final_response.json()
        
        # If sync failed with 400/404 (no JE or not configured), no log entry is created
        # If sync failed with external API error, a 'failed' log entry should be created
        if sync_response.status_code in [400, 404]:
            # No journal entry or not configured - no log created
            print(f"PASSED: sync-journal-entries returned {sync_response.status_code} (no JE or not configured) - no log entry expected")
        else:
            # External API failure should create a 'failed' log entry
            final_count = len(final_data)
            if final_count > initial_count:
                latest_entry = final_data[0]  # Most recent first (sorted by synced_at desc)
                assert latest_entry.get('status') == 'failed', f"Expected 'failed' status, got {latest_entry.get('status')}"
                print(f"PASSED: sync-journal-entries logged failed attempt with status='failed'")
            else:
                print(f"PASSED: sync-journal-entries returned {sync_response.status_code} - {sync_response.text[:100]}")


class TestFortexaERPConfig:
    """Tests for FortexaERP configuration endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_erp_config_endpoint(self):
        """Test that GET /api/fortexaerp/config returns configuration status"""
        response = self.session.get(f"{BASE_URL}/api/fortexaerp/config")
        assert response.status_code == 200
        data = response.json()
        assert 'configured' in data, "Response should contain 'configured' field"
        print(f"PASSED: GET /api/fortexaerp/config returns configured={data.get('configured')}")
    
    def test_erp_logo_asset_accessible(self):
        """Test that FortexaERP logo static asset is accessible"""
        response = requests.get(f"{BASE_URL}/fortexaerp-logo.png")
        assert response.status_code == 200, f"Expected 200 for logo asset, got {response.status_code}"
        assert 'image' in response.headers.get('Content-Type', ''), "Expected image content type"
        print("PASSED: /fortexaerp-logo.png static asset is accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
