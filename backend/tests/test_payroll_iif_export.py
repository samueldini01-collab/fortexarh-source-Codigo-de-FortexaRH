"""
Test Payroll IIF Export for QuickBooks Desktop
Tests the full payroll flow: create period -> add employees -> submit -> approve -> export IIF
Validates IIF format: headers, date format (MM/DD/YYYY), amounts (debit positive, credit negative), balance
"""
import pytest
import requests
import os
import re
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestPayrollIIFExport:
    """Test IIF export endpoint for payroll journal entries"""
    
    # Store test data for cleanup
    test_period_id = None
    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup: login and get auth token"""
        if not TestPayrollIIFExport.auth_token:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestPayrollIIFExport.auth_token = data.get("token") or data.get("access_token")
            else:
                pytest.skip(f"Login failed: {response.status_code} - {response.text}")
        
        yield
        
        # Cleanup after all tests in class
        if request.node.name == "test_99_cleanup_test_period":
            self._cleanup()
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {TestPayrollIIFExport.auth_token}",
            "Content-Type": "application/json"
        }
    
    def _cleanup(self):
        """Delete test period after tests"""
        if TestPayrollIIFExport.test_period_id:
            try:
                requests.delete(
                    f"{BASE_URL}/api/payroll/periods/{TestPayrollIIFExport.test_period_id}",
                    headers=self._get_headers()
                )
                print(f"Cleaned up test period: {TestPayrollIIFExport.test_period_id}")
            except Exception as e:
                print(f"Cleanup error: {e}")
    
    def test_01_login_success(self):
        """Verify login works and we have a token"""
        assert TestPayrollIIFExport.auth_token is not None
        assert len(TestPayrollIIFExport.auth_token) > 10
        print(f"Login successful, token length: {len(TestPayrollIIFExport.auth_token)}")
    
    def test_02_create_payroll_period(self):
        """Create a new payroll period for IIF export testing"""
        now = datetime.now()
        payload = {
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": now.year,
            "month": now.month,
            "start_date": f"{now.year}-{now.month:02d}-01",
            "end_date": f"{now.year}-{now.month:02d}-15",
            "description": f"TEST_IIF_Export_{now.strftime('%Y%m%d_%H%M%S')}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods",
            headers=self._get_headers(),
            json=payload
        )
        
        assert response.status_code == 200, f"Create period failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "period_id" in data
        
        TestPayrollIIFExport.test_period_id = data["period_id"]
        print(f"Created test period: {TestPayrollIIFExport.test_period_id}")
    
    def test_03_add_employees_to_period(self):
        """Add employees to the payroll period"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{period_id}/add-employees",
            headers=self._get_headers()
        )
        
        assert response.status_code == 200, f"Add employees failed: {response.status_code} - {response.text}"
        data = response.json()
        print(f"Added {data.get('added', 0)} employees to period")
        
        # Verify period has employees
        period_response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{period_id}",
            headers=self._get_headers()
        )
        assert period_response.status_code == 200
        period_data = period_response.json()
        
        # If no employees, we need at least one for the test
        if period_data.get("employee_count", 0) == 0:
            pytest.skip("No active employees in company - cannot test IIF export")
    
    def test_04_submit_period_for_approval(self):
        """Submit the period for approval"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{period_id}/submit-for-approval",
            headers=self._get_headers(),
            json={"comments": "Test IIF export submission"}
        )
        
        assert response.status_code == 200, f"Submit for approval failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("status") == "pending_approval"
        print("Period submitted for approval")
    
    def test_05_approve_period_generates_je(self):
        """Approve the period - this should generate the journal entry"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/periods/{period_id}/approve",
            headers=self._get_headers(),
            json={"comments": "Approved for IIF export test"}
        )
        
        assert response.status_code == 200, f"Approve failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("status") == "approved"
        
        # Verify journal entry was created
        je_id = data.get("journal_entry_id")
        print(f"Period approved, journal_entry_id: {je_id}")
        
        # Verify period has journal_entry_id
        period_response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{period_id}",
            headers=self._get_headers()
        )
        assert period_response.status_code == 200
        period_data = period_response.json()
        assert period_data.get("journal_entry_id") is not None, "Journal entry not linked to period"
    
    def test_06_export_iif_success(self):
        """Test IIF export returns valid content"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{period_id}/export/iif",
            headers=self._get_headers()
        )
        
        assert response.status_code == 200, f"IIF export failed: {response.status_code} - {response.text}"
        
        # Check Content-Disposition header
        content_disp = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp, "Missing attachment in Content-Disposition"
        assert ".iif" in content_disp, "Missing .iif extension in filename"
        print(f"Content-Disposition: {content_disp}")
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        assert "octet-stream" in content_type or "text" in content_type
        
        iif_content = response.text
        assert len(iif_content) > 0, "IIF content is empty"
        print(f"IIF content length: {len(iif_content)} bytes")
    
    def test_07_iif_has_correct_headers(self):
        """Verify IIF file has correct header rows"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{period_id}/export/iif",
            headers=self._get_headers()
        )
        assert response.status_code == 200
        
        iif_content = response.text
        lines = iif_content.strip().split('\r\n')
        
        # Check header rows
        assert len(lines) >= 4, f"IIF should have at least 4 lines, got {len(lines)}"
        
        # First line should be !TRNS header
        assert lines[0].startswith("!TRNS"), f"First line should start with !TRNS, got: {lines[0][:50]}"
        assert "TRNSID" in lines[0]
        assert "TRNSTYPE" in lines[0]
        assert "DATE" in lines[0]
        assert "ACCNT" in lines[0]
        assert "AMOUNT" in lines[0]
        assert "MEMO" in lines[0]
        
        # Second line should be !SPL header
        assert lines[1].startswith("!SPL"), f"Second line should start with !SPL, got: {lines[1][:50]}"
        
        # Third line should be !ENDTRNS header
        assert lines[2].startswith("!ENDTRNS"), f"Third line should start with !ENDTRNS, got: {lines[2][:50]}"
        
        # Last line should be ENDTRNS
        assert lines[-1].strip() == "ENDTRNS", f"Last line should be ENDTRNS, got: {lines[-1]}"
        
        print("IIF headers validated: !TRNS, !SPL, !ENDTRNS present")
    
    def test_08_iif_date_format_mm_dd_yyyy(self):
        """Verify IIF date is in MM/DD/YYYY format"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{period_id}/export/iif",
            headers=self._get_headers()
        )
        assert response.status_code == 200
        
        iif_content = response.text
        lines = iif_content.strip().split('\r\n')
        
        # Find first TRNS data line (after headers)
        trns_line = None
        for line in lines:
            if line.startswith("TRNS\t"):
                trns_line = line
                break
        
        assert trns_line is not None, "No TRNS data line found"
        
        # Parse the line - DATE is the 4th field (index 3)
        fields = trns_line.split('\t')
        assert len(fields) >= 4, f"TRNS line should have at least 4 fields, got {len(fields)}"
        
        date_field = fields[3]  # DATE field
        
        # Validate MM/DD/YYYY format
        date_pattern = r'^\d{2}/\d{2}/\d{4}$'
        assert re.match(date_pattern, date_field), f"Date should be MM/DD/YYYY format, got: {date_field}"
        
        # Validate it's a valid date
        try:
            parsed_date = datetime.strptime(date_field, "%m/%d/%Y")
            print(f"IIF date validated: {date_field} (parsed as {parsed_date.date()})")
        except ValueError:
            pytest.fail(f"Invalid date value: {date_field}")
    
    def test_09_iif_amounts_debit_positive_credit_negative(self):
        """Verify TRNS has positive amount (debit), SPL has negative amounts (credits)"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{period_id}/export/iif",
            headers=self._get_headers()
        )
        assert response.status_code == 200
        
        iif_content = response.text
        lines = iif_content.strip().split('\r\n')
        
        trns_amounts = []
        spl_amounts = []
        
        for line in lines:
            if line.startswith("TRNS\t"):
                fields = line.split('\t')
                if len(fields) >= 8:
                    amount = float(fields[7])  # AMOUNT is 8th field (index 7)
                    trns_amounts.append(amount)
            elif line.startswith("SPL\t"):
                fields = line.split('\t')
                if len(fields) >= 8:
                    amount = float(fields[7])
                    spl_amounts.append(amount)
        
        assert len(trns_amounts) > 0, "No TRNS amounts found"
        assert len(spl_amounts) > 0, "No SPL amounts found"
        
        # First TRNS line should have positive amount (debit)
        assert trns_amounts[0] > 0, f"First TRNS amount should be positive (debit), got: {trns_amounts[0]}"
        
        # SPL lines should have negative amounts (credits)
        negative_spl_count = sum(1 for a in spl_amounts if a < 0)
        print(f"TRNS amounts: {trns_amounts}")
        print(f"SPL amounts: {spl_amounts}")
        print(f"Negative SPL count: {negative_spl_count} of {len(spl_amounts)}")
        
        # Most SPL lines should be negative (credits), but some might be 0
        assert negative_spl_count > 0, "At least one SPL line should have negative amount (credit)"
    
    def test_10_iif_amounts_sum_to_zero(self):
        """Verify sum of all AMOUNT values equals 0 (balanced)"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{period_id}/export/iif",
            headers=self._get_headers()
        )
        assert response.status_code == 200
        
        iif_content = response.text
        lines = iif_content.strip().split('\r\n')
        
        all_amounts = []
        
        for line in lines:
            if line.startswith("TRNS\t") or line.startswith("SPL\t"):
                fields = line.split('\t')
                if len(fields) >= 8:
                    try:
                        amount = float(fields[7])
                        all_amounts.append(amount)
                    except ValueError:
                        pass
        
        total = sum(all_amounts)
        
        # Allow for small rounding differences (up to 0.05)
        assert abs(total) <= 0.05, f"IIF amounts should sum to 0 (balanced), got: {total}"
        print(f"IIF balance check: sum of {len(all_amounts)} amounts = {total} (balanced)")
    
    def test_11_iif_has_trns_type_general_journal(self):
        """Verify TRNSTYPE is GENERAL JOURNAL"""
        period_id = TestPayrollIIFExport.test_period_id
        assert period_id is not None, "No test period created"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{period_id}/export/iif",
            headers=self._get_headers()
        )
        assert response.status_code == 200
        
        iif_content = response.text
        lines = iif_content.strip().split('\r\n')
        
        for line in lines:
            if line.startswith("TRNS\t") or line.startswith("SPL\t"):
                fields = line.split('\t')
                if len(fields) >= 3:
                    trns_type = fields[2]  # TRNSTYPE is 3rd field (index 2)
                    assert trns_type == "GENERAL JOURNAL", f"TRNSTYPE should be 'GENERAL JOURNAL', got: {trns_type}"
        
        print("All data lines have TRNSTYPE = GENERAL JOURNAL")
    
    def test_12_export_iif_404_nonexistent_period(self):
        """Test IIF export returns 404 for non-existent period"""
        fake_period_id = "period_nonexistent_12345"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{fake_period_id}/export/iif",
            headers=self._get_headers()
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent period, got: {response.status_code}"
        print("404 returned for non-existent period")
    
    def test_13_export_iif_400_no_journal_entry(self):
        """Test IIF export returns 400 for period without journal entry"""
        # Create a new period but don't approve it (no JE)
        now = datetime.now()
        payload = {
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": now.year,
            "month": now.month,
            "start_date": f"{now.year}-{now.month:02d}-01",
            "end_date": f"{now.year}-{now.month:02d}-15",
            "description": f"TEST_IIF_NoJE_{now.strftime('%Y%m%d_%H%M%S')}"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/periods",
            headers=self._get_headers(),
            json=payload
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test period for 400 test")
        
        temp_period_id = create_response.json().get("period_id")
        
        try:
            # Try to export IIF without approving (no JE)
            response = requests.get(
                f"{BASE_URL}/api/payroll/periods/{temp_period_id}/export/iif",
                headers=self._get_headers()
            )
            
            assert response.status_code == 400, f"Expected 400 for period without JE, got: {response.status_code}"
            
            # Check error message
            error_data = response.json()
            assert "detail" in error_data
            print(f"400 returned for period without JE: {error_data.get('detail')}")
        finally:
            # Cleanup temp period
            requests.delete(
                f"{BASE_URL}/api/payroll/periods/{temp_period_id}",
                headers=self._get_headers()
            )
    
    def test_99_cleanup_test_period(self):
        """Cleanup: Delete the test period"""
        period_id = TestPayrollIIFExport.test_period_id
        if period_id:
            response = requests.delete(
                f"{BASE_URL}/api/payroll/periods/{period_id}",
                headers=self._get_headers()
            )
            
            # Accept 200 or 404 (already deleted)
            assert response.status_code in [200, 404], f"Cleanup failed: {response.status_code}"
            print(f"Test period {period_id} cleaned up")
            TestPayrollIIFExport.test_period_id = None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
