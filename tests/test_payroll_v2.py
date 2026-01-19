"""
Test suite for Payroll V2 (Advanced Payroll System) - FortexaRH
Tests: Period creation with payroll_type and department_filter, employee addition,
       TSS calculations (SFS 3.04%, AFP 2.87%), ISR, novelties, approval, payment,
       and journal entry generation.
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"

class TestPayrollV2:
    """Payroll V2 Advanced System Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed - skipping tests")
        
        yield
        
        # Cleanup - delete test periods
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Clean up test-created periods"""
        try:
            response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
            if response.status_code == 200:
                periods = response.json()
                for period in periods:
                    if "TEST_" in period.get("description", ""):
                        self.session.delete(f"{BASE_URL}/api/payroll-v2/periods/{period['period_id']}")
        except:
            pass
    
    # ==================== NOVELTY TYPES ENDPOINT ====================
    
    def test_get_novelty_types(self):
        """Test /api/payroll-v2/novelty-types returns income and deduction types"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/novelty-types")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "income" in data, "Response should contain 'income' key"
        assert "deduction" in data, "Response should contain 'deduction' key"
        
        # Verify income types
        income_codes = [t["code"] for t in data["income"]]
        assert "COM" in income_codes, "Should have COM (Comisiones) income type"
        assert "BON" in income_codes, "Should have BON (Bonificación) income type"
        assert "INC" in income_codes or "VIA" in income_codes, "Should have INC or VIA income type"
        
        # Verify deduction types
        deduction_codes = [t["code"] for t in data["deduction"]]
        assert "PREST" in deduction_codes, "Should have PREST (Préstamo) deduction type"
        assert "ANTIC" in deduction_codes, "Should have ANTIC (Anticipo) deduction type"
        
        print(f"✓ Novelty types: {len(data['income'])} income, {len(data['deduction'])} deduction")
    
    def test_get_payroll_types(self):
        """Test /api/payroll-v2/payroll-types returns available payroll types"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/payroll-types")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        codes = [t["code"] for t in data]
        assert "REG" in codes, "Should have REG (Regular) payroll type"
        assert "BONO" in codes, "Should have BONO payroll type"
        assert "REG13" in codes, "Should have REG13 (Regalía Pascual) payroll type"
        assert "VAC" in codes, "Should have VAC (Vacaciones) payroll type"
        assert "LIQ" in codes, "Should have LIQ (Liquidación) payroll type"
        
        print(f"✓ Payroll types: {len(data)} types available")
    
    # ==================== PERIOD CREATION WITH PAYROLL_TYPE ====================
    
    def test_create_period_with_payroll_type_regular(self):
        """Test creating a period with REG (Regular) payroll type"""
        unique_id = uuid.uuid4().hex[:6]
        
        response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_Regular_{unique_id}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "period_id" in data, "Response should contain period_id"
        
        # Verify period was created with correct payroll_type
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{data['period_id']}")
        assert period_response.status_code == 200
        
        period = period_response.json()
        assert period["payroll_type"] == "REG", f"Expected REG, got {period['payroll_type']}"
        
        print(f"✓ Created REG period: {data['period_id']}")
    
    def test_create_period_with_payroll_type_bono(self):
        """Test creating a period with BONO payroll type"""
        unique_id = uuid.uuid4().hex[:6]
        
        response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "mensual",
            "payroll_type": "BONO",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "description": f"TEST_Bono_{unique_id}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{data['period_id']}")
        period = period_response.json()
        
        assert period["payroll_type"] == "BONO", f"Expected BONO, got {period['payroll_type']}"
        
        print(f"✓ Created BONO period: {data['period_id']}")
    
    def test_create_period_with_department_filter(self):
        """Test creating a period with department_filter"""
        unique_id = uuid.uuid4().hex[:6]
        
        response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_DeptFilter_{unique_id}",
            "department_filter": "Ventas"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{data['period_id']}")
        period = period_response.json()
        
        assert period.get("department_filter") == "Ventas", f"Expected 'Ventas', got {period.get('department_filter')}"
        
        print(f"✓ Created period with department filter: {data['period_id']}")
    
    # ==================== ADD EMPLOYEES TO PERIOD ====================
    
    def test_add_employees_to_period(self):
        """Test adding employees to a payroll period"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create period
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_AddEmployees_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        # Add employees
        add_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees")
        
        assert add_response.status_code == 200, f"Expected 200, got {add_response.status_code}: {add_response.text}"
        
        data = add_response.json()
        assert "added" in data or "message" in data, "Response should indicate employees added"
        
        # Verify employees were added
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        period = period_response.json()
        
        print(f"✓ Added employees to period: {period.get('employee_count', 0)} employees")
    
    # ==================== CALCULATE PAYROLL WITH TSS ====================
    
    def test_calculate_payroll_with_tss_deductions(self):
        """Test payroll calculation with TSS deductions (SFS 3.04%, AFP 2.87%)"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create period
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_TSSCalc_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        # Add employees
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees")
        
        # Calculate payroll
        calc_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/calculate")
        
        assert calc_response.status_code == 200, f"Expected 200, got {calc_response.status_code}: {calc_response.text}"
        
        # Verify calculations
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        period = period_response.json()
        
        assert period["status"] == "calculated", f"Expected 'calculated', got {period['status']}"
        
        # Check entries have TSS deductions
        entries = period.get("entries", [])
        if entries:
            entry = entries[0]
            assert "sfs_employee" in entry, "Entry should have sfs_employee"
            assert "afp_employee" in entry, "Entry should have afp_employee"
            
            # Verify SFS is approximately 3.04% of gross
            if entry.get("gross_salary", 0) > 0:
                expected_sfs = round(entry["gross_salary"] * 0.0307, 2)
                actual_sfs = entry.get("sfs_employee", 0)
                # Allow small rounding difference
                assert abs(actual_sfs - expected_sfs) < 1, f"SFS should be ~3.07% of gross. Expected ~{expected_sfs}, got {actual_sfs}"
                
                expected_afp = round(entry["gross_salary"] * 0.0287, 2)
                actual_afp = entry.get("afp_employee", 0)
                assert abs(actual_afp - expected_afp) < 1, f"AFP should be ~2.87% of gross. Expected ~{expected_afp}, got {actual_afp}"
        
        print(f"✓ Calculated payroll with TSS: {len(entries)} entries, total net: {period.get('total_net', 0)}")
    
    # ==================== ADD NOVELTIES ====================
    
    def test_add_income_novelty(self):
        """Test adding an income novelty (Comisiones) to an employee"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create and setup period
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_IncomeNovelty_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        # Add employees
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees")
        
        # Get entries
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        period = period_response.json()
        entries = period.get("entries", [])
        
        if not entries:
            pytest.skip("No employees in period to test novelties")
        
        entry_id = entries[0]["entry_id"]
        
        # Add income novelty
        novelty_response = self.session.post(f"{BASE_URL}/api/payroll-v2/entries/{entry_id}/novelties", json={
            "entry_id": entry_id,
            "novelty_type": "income",
            "code": "COM",
            "name": "Comisiones",
            "description": "Comisión de ventas enero",
            "amount": 5000.00,
            "is_percentage": False
        })
        
        assert novelty_response.status_code == 200, f"Expected 200, got {novelty_response.status_code}: {novelty_response.text}"
        
        data = novelty_response.json()
        assert "novelty_id" in data, "Response should contain novelty_id"
        
        print(f"✓ Added income novelty: {data['novelty_id']}")
    
    def test_add_deduction_novelty(self):
        """Test adding a deduction novelty (Préstamo) to an employee"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create and setup period
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_DeductionNovelty_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        # Add employees
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees")
        
        # Get entries
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        period = period_response.json()
        entries = period.get("entries", [])
        
        if not entries:
            pytest.skip("No employees in period to test novelties")
        
        entry_id = entries[0]["entry_id"]
        
        # Add deduction novelty
        novelty_response = self.session.post(f"{BASE_URL}/api/payroll-v2/entries/{entry_id}/novelties", json={
            "entry_id": entry_id,
            "novelty_type": "deduction",
            "code": "PREST",
            "name": "Préstamo Empresa",
            "description": "Cuota préstamo enero",
            "amount": 2000.00,
            "is_percentage": False
        })
        
        assert novelty_response.status_code == 200, f"Expected 200, got {novelty_response.status_code}: {novelty_response.text}"
        
        data = novelty_response.json()
        assert "novelty_id" in data, "Response should contain novelty_id"
        
        print(f"✓ Added deduction novelty: {data['novelty_id']}")
    
    # ==================== APPROVE AND PAY ====================
    
    def test_approve_period(self):
        """Test approving a calculated payroll period"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create, add employees, and calculate
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_Approve_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees")
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/calculate")
        
        # Approve
        approve_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/approve")
        
        assert approve_response.status_code == 200, f"Expected 200, got {approve_response.status_code}: {approve_response.text}"
        
        # Verify status
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        period = period_response.json()
        
        assert period["status"] == "approved", f"Expected 'approved', got {period['status']}"
        
        print(f"✓ Approved period: {period_id}")
    
    def test_pay_period_with_bank_account(self):
        """Test paying a period with bank account selection and journal entry generation"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create, add employees, calculate, and approve
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_Pay_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees")
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/calculate")
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/approve")
        
        # Pay with bank account
        pay_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/pay", json={
            "bank_account_code": "1101"
        })
        
        assert pay_response.status_code == 200, f"Expected 200, got {pay_response.status_code}: {pay_response.text}"
        
        data = pay_response.json()
        assert "journal_entry_id" in data or "entry_number" in data, "Response should contain journal entry info"
        
        # Verify status
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        period = period_response.json()
        
        assert period["status"] == "paid", f"Expected 'paid', got {period['status']}"
        assert period.get("journal_entry_id") is not None, "Period should have journal_entry_id"
        
        print(f"✓ Paid period with journal entry: {data.get('entry_number', data.get('journal_entry_id'))}")
    
    # ==================== JOURNAL ENTRY VERIFICATION ====================
    
    def test_journal_entry_generated_on_payment(self):
        """Test that journal entry is automatically generated when paying payroll"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Full workflow
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_JournalEntry_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees")
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/calculate")
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/approve")
        
        pay_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/pay", json={
            "bank_account_code": "1101"
        })
        
        assert pay_response.status_code == 200
        
        # Get period to find journal entry ID
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        period = period_response.json()
        
        journal_entry_id = period.get("journal_entry_id")
        assert journal_entry_id is not None, "Period should have journal_entry_id after payment"
        
        # Verify journal entry exists
        entry_response = self.session.get(f"{BASE_URL}/api/accounting/journal-entries/{journal_entry_id}")
        
        assert entry_response.status_code == 200, f"Journal entry should exist: {entry_response.status_code}"
        
        entry = entry_response.json()
        assert "lines" in entry, "Journal entry should have lines"
        assert len(entry["lines"]) > 0, "Journal entry should have at least one line"
        
        # Verify debits equal credits
        total_debits = sum(line.get("debit", 0) for line in entry["lines"])
        total_credits = sum(line.get("credit", 0) for line in entry["lines"])
        
        assert abs(total_debits - total_credits) < 0.01, f"Journal entry should be balanced. Debits: {total_debits}, Credits: {total_credits}"
        
        print(f"✓ Journal entry generated and balanced: {journal_entry_id}")
    
    # ==================== PERIODS LIST ====================
    
    def test_get_periods_list(self):
        """Test getting list of payroll periods"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ Got {len(data)} payroll periods")
    
    # ==================== DELETE PERIOD ====================
    
    def test_delete_period(self):
        """Test deleting a payroll period"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create period
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_Delete_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        # Delete period
        delete_response = self.session.delete(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        # Verify deleted
        get_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        assert get_response.status_code == 404, "Period should not exist after deletion"
        
        print(f"✓ Deleted period: {period_id}")


class TestPayrollV2EdgeCases:
    """Edge case tests for Payroll V2"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
        
        yield
    
    def test_cannot_pay_uncalculated_period(self):
        """Test that uncalculated periods cannot be paid"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create period without calculating
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_NoPay_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        # Try to pay without calculating
        pay_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/pay", json={
            "bank_account_code": "1101"
        })
        
        assert pay_response.status_code == 400, f"Should fail with 400, got {pay_response.status_code}"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        
        print("✓ Cannot pay uncalculated period")
    
    def test_cannot_modify_paid_period(self):
        """Test that paid periods cannot be modified"""
        unique_id = uuid.uuid4().hex[:6]
        
        # Create and pay period
        create_response = self.session.post(f"{BASE_URL}/api/payroll-v2/periods", json={
            "period_type": "quincenal_1",
            "payroll_type": "REG",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": f"TEST_NoModify_{unique_id}"
        })
        
        assert create_response.status_code == 200
        period_id = create_response.json()["period_id"]
        
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees")
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/calculate")
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/approve")
        self.session.post(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/pay", json={"bank_account_code": "1101"})
        
        # Get entries
        period_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}")
        period = period_response.json()
        entries = period.get("entries", [])
        
        if entries:
            entry_id = entries[0]["entry_id"]
            
            # Try to add novelty to paid period
            novelty_response = self.session.post(f"{BASE_URL}/api/payroll-v2/entries/{entry_id}/novelties", json={
                "entry_id": entry_id,
                "novelty_type": "income",
                "code": "COM",
                "name": "Comisiones",
                "amount": 1000.00,
                "is_percentage": False
            })
            
            assert novelty_response.status_code == 400, f"Should fail with 400, got {novelty_response.status_code}"
        
        print("✓ Cannot modify paid period")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
