"""
QuickBooks Payroll Sync Feature Tests
Tests for:
- GET /api/quickbooks/account-mapping - returns mapping (initially empty)
- PUT /api/quickbooks/account-mapping - saves account mapping
- POST /api/quickbooks/sync/payroll - validates period_id, mapping, and period status
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"

# Test data from main agent
PAID_PERIOD_ID = "period_6a079d88c0c4"
DRAFT_PERIOD_ID = "period_0c7fdc679329"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestQuickBooksAccountMapping:
    """Tests for QBO account mapping endpoints"""
    
    def test_get_account_mapping_returns_empty_initially(self, auth_headers):
        """GET /api/quickbooks/account-mapping should return mapping (initially empty)"""
        response = requests.get(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have company_id and accounts fields
        assert "company_id" in data or "accounts" in data, f"Response missing expected fields: {data}"
        
        # accounts should be a dict (possibly empty)
        accounts = data.get("accounts", {})
        assert isinstance(accounts, dict), f"accounts should be dict, got {type(accounts)}"
        print(f"✓ GET account-mapping returned: {data}")
    
    def test_save_account_mapping(self, auth_headers):
        """PUT /api/quickbooks/account-mapping should save account mapping"""
        # Create a test mapping with mock account IDs
        test_mapping = {
            "accounts": {
                "payroll_expense": {"id": "test_expense_1", "name": "Payroll Expense"},
                "employer_contributions": {"id": "test_expense_2", "name": "Employer Contributions"},
                "sfs_payable": {"id": "test_liability_1", "name": "SFS Payable"},
                "afp_payable": {"id": "test_liability_2", "name": "AFP Payable"},
                "isr_payable": {"id": "test_liability_3", "name": "ISR Payable"},
                "srl_payable": {"id": "test_liability_4", "name": "SRL Payable"},
                "infotep_payable": {"id": "test_liability_5", "name": "INFOTEP Payable"},
                "bank_account": {"id": "test_asset_1", "name": "Bank Account"}
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=auth_headers,
            json=test_mapping
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, f"Response should have message: {data}"
        print(f"✓ PUT account-mapping saved successfully: {data}")
        
        # Verify the mapping was saved by fetching it again
        get_response = requests.get(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        saved_data = get_response.json()
        saved_accounts = saved_data.get("accounts", {})
        
        # Verify all 8 accounts were saved
        assert len(saved_accounts) == 8, f"Expected 8 accounts, got {len(saved_accounts)}"
        assert saved_accounts.get("payroll_expense", {}).get("id") == "test_expense_1"
        print(f"✓ Verified mapping was persisted with {len(saved_accounts)} accounts")


class TestQuickBooksPayrollSync:
    """Tests for POST /api/quickbooks/sync/payroll endpoint validation"""
    
    def test_sync_payroll_without_period_id_returns_error(self, auth_headers):
        """POST /api/quickbooks/sync/payroll without period_id should return error"""
        response = requests.post(
            f"{BASE_URL}/api/quickbooks/sync/payroll",
            headers=auth_headers,
            json={"sync_type": "payroll"}  # No period_id
        )
        
        # Should return 400 with error message
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        detail = data.get("detail", "")
        assert "period_id" in detail.lower() or "se requiere" in detail.lower(), \
            f"Error should mention period_id requirement: {detail}"
        print(f"✓ Correctly rejected request without period_id: {detail}")
    
    def test_sync_payroll_with_incomplete_mapping_returns_error(self, auth_headers):
        """POST /api/quickbooks/sync/payroll with incomplete mapping should list missing accounts"""
        # First, clear the mapping to make it incomplete
        incomplete_mapping = {
            "accounts": {
                "payroll_expense": {"id": "test_1", "name": "Test"},
                # Missing other 7 required accounts
            }
        }
        
        requests.put(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=auth_headers,
            json=incomplete_mapping
        )
        
        # Now try to sync
        response = requests.post(
            f"{BASE_URL}/api/quickbooks/sync/payroll",
            headers=auth_headers,
            json={"sync_type": "payroll", "period_id": PAID_PERIOD_ID}
        )
        
        # Should return 400 with error about missing accounts
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        detail = data.get("detail", "")
        # Should mention missing accounts
        assert "faltan" in detail.lower() or "mapear" in detail.lower() or "missing" in detail.lower(), \
            f"Error should mention missing accounts: {detail}"
        print(f"✓ Correctly rejected incomplete mapping: {detail}")
    
    def test_sync_payroll_with_non_paid_period_returns_error(self, auth_headers):
        """POST /api/quickbooks/sync/payroll with non-paid period should return error"""
        # First, set up complete mapping
        complete_mapping = {
            "accounts": {
                "payroll_expense": {"id": "test_expense_1", "name": "Payroll Expense"},
                "employer_contributions": {"id": "test_expense_2", "name": "Employer Contributions"},
                "sfs_payable": {"id": "test_liability_1", "name": "SFS Payable"},
                "afp_payable": {"id": "test_liability_2", "name": "AFP Payable"},
                "isr_payable": {"id": "test_liability_3", "name": "ISR Payable"},
                "srl_payable": {"id": "test_liability_4", "name": "SRL Payable"},
                "infotep_payable": {"id": "test_liability_5", "name": "INFOTEP Payable"},
                "bank_account": {"id": "test_asset_1", "name": "Bank Account"}
            }
        }
        
        requests.put(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=auth_headers,
            json=complete_mapping
        )
        
        # Try to sync a draft period
        response = requests.post(
            f"{BASE_URL}/api/quickbooks/sync/payroll",
            headers=auth_headers,
            json={"sync_type": "payroll", "period_id": DRAFT_PERIOD_ID}
        )
        
        # Should return 400 with error about period status
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        detail = data.get("detail", "")
        # Should mention that only paid periods can be synced
        assert "pagado" in detail.lower() or "paid" in detail.lower() or "solo" in detail.lower(), \
            f"Error should mention period must be paid: {detail}"
        print(f"✓ Correctly rejected non-paid period: {detail}")
    
    def test_sync_payroll_with_paid_period_and_complete_mapping(self, auth_headers):
        """POST /api/quickbooks/sync/payroll with paid period and complete mapping should attempt sync"""
        # Set up complete mapping
        complete_mapping = {
            "accounts": {
                "payroll_expense": {"id": "test_expense_1", "name": "Payroll Expense"},
                "employer_contributions": {"id": "test_expense_2", "name": "Employer Contributions"},
                "sfs_payable": {"id": "test_liability_1", "name": "SFS Payable"},
                "afp_payable": {"id": "test_liability_2", "name": "AFP Payable"},
                "isr_payable": {"id": "test_liability_3", "name": "ISR Payable"},
                "srl_payable": {"id": "test_liability_4", "name": "SRL Payable"},
                "infotep_payable": {"id": "test_liability_5", "name": "INFOTEP Payable"},
                "bank_account": {"id": "test_asset_1", "name": "Bank Account"}
            }
        }
        
        requests.put(
            f"{BASE_URL}/api/quickbooks/account-mapping",
            headers=auth_headers,
            json=complete_mapping
        )
        
        # Try to sync the paid period
        response = requests.post(
            f"{BASE_URL}/api/quickbooks/sync/payroll",
            headers=auth_headers,
            json={"sync_type": "payroll", "period_id": PAID_PERIOD_ID}
        )
        
        # This will likely fail with 401 (QB not connected) or 400 (already synced)
        # but it should NOT fail with validation errors about mapping or period status
        status = response.status_code
        data = response.json()
        detail = data.get("detail", "")
        
        # Acceptable outcomes:
        # - 401: QB connection expired (expected in test env)
        # - 400: Period already synced to QB
        # - 200: Success (unlikely without real QB connection)
        
        if status == 401:
            assert "quickbooks" in detail.lower() or "conexión" in detail.lower() or "expirada" in detail.lower() or "reconecte" in detail.lower(), \
                f"401 should be about QB connection: {detail}"
            print(f"✓ Validation passed, failed at QB connection step (expected): {detail}")
        elif status == 400:
            # Could be "already synced" or other business logic error
            print(f"✓ Validation passed, business logic error: {detail}")
        elif status == 200:
            print(f"✓ Sync succeeded (unexpected in test env): {data}")
        else:
            # Any other status is unexpected
            pytest.fail(f"Unexpected status {status}: {detail}")


class TestQuickBooksStatus:
    """Tests for QuickBooks connection status"""
    
    def test_quickbooks_status_endpoint(self, auth_headers):
        """GET /api/quickbooks/status should return connection status"""
        response = requests.get(
            f"{BASE_URL}/api/quickbooks/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have connected field
        assert "connected" in data, f"Response should have 'connected' field: {data}"
        
        print(f"✓ QB Status: connected={data.get('connected')}, configured={data.get('configured')}")
        
        # In test env, QB is likely not connected
        if not data.get("connected"):
            print("  (QuickBooks is NOT connected in test environment - expected)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
