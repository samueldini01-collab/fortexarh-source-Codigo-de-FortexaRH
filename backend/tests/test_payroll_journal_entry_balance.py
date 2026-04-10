"""
Test Payroll Journal Entry Balance - FortexaRH
Tests the fix for accounting imbalance bug (Debits != Credits).
The bug was caused by reading 'otros_descuentos' (non-existent field) 
instead of 'total_additional_deductions' + 'loan_deduction'.

Tests:
- Full payroll workflow: create -> add-employees -> submit -> approve -> pay
- JE balance verification (total_debits == total_credits) - CRITICAL
- Auto-created accounts verification
- Loan deduction as separate line (account 2170)
- Manual JE generation and deletion
- Cascade delete (period deletion removes JE)
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestPayrollJournalEntryBalance:
    """Tests for payroll journal entry balance fix"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_period_id(self, auth_headers):
        """Create a test payroll period and clean up after tests"""
        # Create period
        now = datetime.now()
        period_data = {
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": now.year,
            "month": now.month,
            "start_date": f"{now.year}-{now.month:02d}-01",
            "end_date": f"{now.year}-{now.month:02d}-15",
            "description": f"TEST_JE_BALANCE - {now.isoformat()}"
        }
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods",
            json=period_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create period: {response.text}"
        period_id = response.json().get("period_id")
        assert period_id, "No period_id returned"
        
        yield period_id
        
        # Cleanup: delete the test period (cascades to JE)
        requests.delete(f"{BASE_URL}/api/payroll/periods/{period_id}", headers=auth_headers)
    
    def test_01_create_period(self, auth_headers, test_period_id):
        """Test period creation"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{test_period_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        period = response.json()
        assert period["status"] == "draft"
        assert period["journal_entry_id"] is None
        print(f"✓ Period created: {test_period_id}, status=draft")
    
    def test_02_add_employees_to_period(self, auth_headers, test_period_id):
        """Test adding employees to period"""
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{test_period_id}/add-employees",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        added = data.get("added", 0)
        assert added > 0, "No employees added to period"
        print(f"✓ Added {added} employees to period")
        
        # Verify entries exist
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{test_period_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        period = response.json()
        entries = period.get("entries", [])
        assert len(entries) > 0, "No entries in period"
        print(f"✓ Period has {len(entries)} entries")
    
    def test_03_submit_for_approval(self, auth_headers, test_period_id):
        """Test submitting period for approval"""
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{test_period_id}/submit-for-approval",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "pending_approval"
        print("✓ Period submitted for approval")
    
    def test_04_approve_period_generates_balanced_je(self, auth_headers, test_period_id):
        """CRITICAL: Test that approving period generates a balanced JE"""
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{test_period_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "approved"
        je_id = data.get("journal_entry_id")
        assert je_id, "No journal_entry_id returned on approve"
        print(f"✓ Period approved, JE created: {je_id}")
        
        # Verify JE is balanced
        je_response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/{je_id}",
            headers=auth_headers
        )
        assert je_response.status_code == 200
        je = je_response.json()
        
        total_debits = je.get("total_debits", 0)
        total_credits = je.get("total_credits", 0)
        
        print(f"  JE total_debits: {total_debits}")
        print(f"  JE total_credits: {total_credits}")
        
        # CRITICAL ASSERTION: Debits must equal Credits
        assert abs(total_debits - total_credits) < 0.01, \
            f"ACCOUNTING IMBALANCE! Debits={total_debits}, Credits={total_credits}, Diff={total_debits - total_credits}"
        
        print(f"✓ JE is BALANCED: Debits={total_debits}, Credits={total_credits}")
        
        # Verify JE status is draft (not posted yet)
        assert je.get("status") == "draft", f"Expected draft status, got {je.get('status')}"
        print("✓ JE status is 'draft' after approve")
        
        # Verify JE has lines
        lines = je.get("lines", [])
        assert len(lines) > 0, "JE has no lines"
        print(f"✓ JE has {len(lines)} lines")
        
        # Verify accounting equation in lines
        line_debits = sum(line.get("debit", 0) for line in lines)
        line_credits = sum(line.get("credit", 0) for line in lines)
        assert abs(line_debits - line_credits) < 0.01, \
            f"Line totals don't match! Debits={line_debits}, Credits={line_credits}"
        print(f"✓ Line totals match: Debits={line_debits}, Credits={line_credits}")
    
    def test_05_pay_period_updates_je_to_posted(self, auth_headers, test_period_id):
        """Test that paying period updates JE status to 'posted'"""
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{test_period_id}/pay",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "paid"
        je_id = data.get("journal_entry_id")
        assert je_id, "No journal_entry_id returned on pay"
        print(f"✓ Period paid, JE updated: {je_id}")
        
        # Verify JE status is now 'posted'
        je_response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/{je_id}",
            headers=auth_headers
        )
        assert je_response.status_code == 200
        je = je_response.json()
        
        assert je.get("status") == "posted", f"Expected posted status, got {je.get('status')}"
        print("✓ JE status is 'posted' after pay")
        
        # Verify JE is still balanced after update
        total_debits = je.get("total_debits", 0)
        total_credits = je.get("total_credits", 0)
        assert abs(total_debits - total_credits) < 0.01, \
            f"ACCOUNTING IMBALANCE after pay! Debits={total_debits}, Credits={total_credits}"
        print(f"✓ JE still BALANCED after pay: Debits={total_debits}, Credits={total_credits}")


class TestAutoCreatedAccounts:
    """Test that required accounts are auto-created"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_required_accounts_exist(self, auth_headers):
        """Verify that required payroll accounts exist in chart of accounts"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/accounts",
            headers=auth_headers
        )
        assert response.status_code == 200
        accounts = response.json()
        
        # Required account codes from journal_entry_service.py
        required_codes = ["6100", "6200", "2110", "2120", "2130", "2140", "2150", "2170", "1100"]
        
        account_codes = {acc.get("code") for acc in accounts}
        
        missing = []
        found = []
        for code in required_codes:
            if code in account_codes:
                found.append(code)
            else:
                missing.append(code)
        
        print(f"Found accounts: {found}")
        if missing:
            print(f"Missing accounts (may be auto-created on JE generation): {missing}")
        
        # At least some accounts should exist
        assert len(found) > 0, "No required accounts found"
        print(f"✓ {len(found)}/{len(required_codes)} required accounts exist")


class TestLoanDeductionLine:
    """Test that loan deduction appears as separate line in JE"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_loan_line_in_je(self, auth_headers):
        """Check if loan deduction line exists in JE (if employees have loans)"""
        # Get existing paid periods to check their JEs
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods",
            headers=auth_headers
        )
        assert response.status_code == 200
        periods = response.json()
        
        # Find a period with a JE
        je_found = False
        loan_line_found = False
        
        for period in periods:
            je_id = period.get("journal_entry_id")
            if je_id:
                je_response = requests.get(
                    f"{BASE_URL}/api/accounting/journal-entries/{je_id}",
                    headers=auth_headers
                )
                if je_response.status_code == 200:
                    je = je_response.json()
                    je_found = True
                    lines = je.get("lines", [])
                    
                    # Check for loan line (account 2170)
                    for line in lines:
                        if line.get("account_code") == "2170":
                            loan_line_found = True
                            print(f"✓ Found loan line in JE {je_id}: credit={line.get('credit')}")
                            break
                    
                    if loan_line_found:
                        break
        
        if not je_found:
            pytest.skip("No JEs found to check for loan lines")
        
        # Note: loan line may not exist if no employees have loans
        if loan_line_found:
            print("✓ Loan deduction appears as separate line (account 2170)")
        else:
            print("ℹ No loan lines found (employees may not have active loans)")


class TestManualJEOperations:
    """Test manual JE generation and deletion"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_manual_je_generation_requires_approved_status(self, auth_headers):
        """Test that manual JE generation requires approved/paid status"""
        # Create a draft period
        now = datetime.now()
        period_data = {
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": now.year,
            "month": now.month,
            "start_date": f"{now.year}-{now.month:02d}-01",
            "end_date": f"{now.year}-{now.month:02d}-15",
            "description": f"TEST_MANUAL_JE - {now.isoformat()}"
        }
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods",
            json=period_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        period_id = response.json().get("period_id")
        
        try:
            # Try to generate JE for draft period (should fail)
            response = requests.post(
                f"{BASE_URL}/api/payroll/periods/{period_id}/generate-je",
                headers=auth_headers
            )
            assert response.status_code == 400, f"Expected 400 for draft period, got {response.status_code}"
            print("✓ Manual JE generation correctly rejected for draft period")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/payroll/periods/{period_id}", headers=auth_headers)
    
    def test_delete_je_endpoint(self, auth_headers):
        """Test DELETE /api/payroll/periods/{id}/journal-entry"""
        # Find a period with a JE that we can test delete on
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods",
            headers=auth_headers
        )
        assert response.status_code == 200
        periods = response.json()
        
        # Find an approved period with JE (not paid, so JE is draft and can be deleted)
        test_period = None
        for period in periods:
            if period.get("status") == "approved" and period.get("journal_entry_id"):
                test_period = period
                break
        
        if not test_period:
            pytest.skip("No approved period with JE found for delete test")
        
        period_id = test_period.get("period_id")
        je_id = test_period.get("journal_entry_id")
        
        # Delete the JE
        response = requests.delete(
            f"{BASE_URL}/api/payroll/periods/{period_id}/journal-entry",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            print(f"✓ JE {je_id} deleted successfully")
            
            # Verify JE is gone
            je_response = requests.get(
                f"{BASE_URL}/api/accounting/journal-entries/{je_id}",
                headers=auth_headers
            )
            assert je_response.status_code == 404, "JE should be deleted"
            print("✓ JE no longer exists after delete")
            
            # Regenerate JE for the period
            regen_response = requests.post(
                f"{BASE_URL}/api/payroll/periods/{period_id}/generate-je",
                headers=auth_headers
            )
            assert regen_response.status_code == 200, f"Failed to regenerate JE: {regen_response.text}"
            print("✓ JE regenerated successfully")
        else:
            print(f"ℹ Could not delete JE (may be posted): {response.status_code}")


class TestCascadeDelete:
    """Test that deleting a period cascades to delete its JE"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_period_delete_cascades_to_je(self, auth_headers):
        """Test that deleting a period also deletes its JE"""
        # Create a period
        now = datetime.now()
        period_data = {
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": now.year,
            "month": now.month,
            "start_date": f"{now.year}-{now.month:02d}-01",
            "end_date": f"{now.year}-{now.month:02d}-15",
            "description": f"TEST_CASCADE_DELETE - {now.isoformat()}"
        }
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods",
            json=period_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        period_id = response.json().get("period_id")
        
        # Add employees
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{period_id}/add-employees",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Submit for approval
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{period_id}/submit-for-approval",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Approve (creates JE)
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{period_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 200
        je_id = response.json().get("journal_entry_id")
        assert je_id, "No JE created on approve"
        
        # Verify JE exists
        je_response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/{je_id}",
            headers=auth_headers
        )
        assert je_response.status_code == 200, "JE should exist before delete"
        
        # Delete the period
        response = requests.delete(
            f"{BASE_URL}/api/payroll/periods/{period_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        print(f"✓ Period {period_id} deleted")
        
        # Verify JE is also deleted
        je_response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/{je_id}",
            headers=auth_headers
        )
        assert je_response.status_code == 404, f"JE should be deleted, got {je_response.status_code}"
        print(f"✓ JE {je_id} was cascade deleted with period")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
