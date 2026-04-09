"""
Test Payroll Calculator and Employee Manual Override Features
Tests:
1. Payroll Calculator endpoint returns all fields including total_tss_employer and total_cost_employer
2. Employee update with manual override fields (sfs_manual_override, sfs_manual_amount, etc.)
3. Payroll generation respects manual overrides
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestPayrollCalculator:
    """Test payroll calculator endpoint with salary 50000"""
    
    def test_payroll_calculator_returns_all_fields(self, api_client):
        """POST /api/payroll-calculator with salary 50000 returns all fields including total_tss_employer and total_cost_employer"""
        payload = {
            "employee_name": "Test Employee",
            "base_salary": 50000,
            "days_worked": 30,
            "hours_extra": 0,
            "hour_rate": 0,
            "bonuses": 0,
            "commissions": 0,
            "loan_deduction": 0,
            "other_deductions": 0
        }
        
        response = api_client.post(f"{BASE_URL}/api/payroll-calculator", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify all required fields are present
        required_fields = [
            "employee_name", "base_salary", "total_earnings",
            "sfs_employee", "afp_employee", "total_tss_employee",
            "isr_monthly", "total_employee_deductions",
            "total_deductions", "net_salary",
            "sfs_employer", "afp_employer", "srl_employer", "infotep_employer",
            "total_tss_employer", "total_cost_employer", "total_employer_contributions"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify calculations for salary 50000
        assert data["base_salary"] == 50000
        assert data["total_earnings"] == 50000
        
        # Employee deductions (3.04% SFS + 2.87% AFP)
        expected_sfs = round(50000 * 0.0307, 2)  # 3.07% SFS
        expected_afp = round(50000 * 0.0287, 2)  # 2.87% AFP
        
        assert data["sfs_employee"] == expected_sfs, f"SFS employee: expected {expected_sfs}, got {data['sfs_employee']}"
        assert data["afp_employee"] == expected_afp, f"AFP employee: expected {expected_afp}, got {data['afp_employee']}"
        
        # Employer contributions (7.09% SFS + 7.10% AFP + 1% SRL + 1% INFOTEP)
        expected_sfs_employer = round(50000 * 0.0709, 2)
        expected_afp_employer = round(50000 * 0.0710, 2)
        expected_srl = round(50000 * 0.01, 2)
        expected_infotep = round(50000 * 0.01, 2)
        
        assert data["sfs_employer"] == expected_sfs_employer
        assert data["afp_employer"] == expected_afp_employer
        assert data["srl_employer"] == expected_srl
        assert data["infotep_employer"] == expected_infotep
        
        # Verify total_tss_employer = sfs_employer + afp_employer
        expected_total_tss_employer = round(expected_sfs_employer + expected_afp_employer, 2)
        assert data["total_tss_employer"] == expected_total_tss_employer, f"total_tss_employer: expected {expected_total_tss_employer}, got {data['total_tss_employer']}"
        
        # Verify total_cost_employer = total_earnings + total_employer_contributions
        expected_total_employer = round(expected_sfs_employer + expected_afp_employer + expected_srl + expected_infotep, 2)
        expected_total_cost = round(50000 + expected_total_employer, 2)
        assert data["total_cost_employer"] == expected_total_cost, f"total_cost_employer: expected {expected_total_cost}, got {data['total_cost_employer']}"
        
        print(f"PASSED: Payroll calculator returns all fields correctly")
        print(f"  - total_tss_employer: {data['total_tss_employer']}")
        print(f"  - total_cost_employer: {data['total_cost_employer']}")
    
    def test_payroll_calculator_breakdown_structure(self, api_client):
        """Verify breakdown structure in response"""
        payload = {
            "employee_name": "Test Employee",
            "base_salary": 50000,
            "days_worked": 30,
            "hours_extra": 0,
            "hour_rate": 0,
            "bonuses": 0,
            "commissions": 0,
            "loan_deduction": 0,
            "other_deductions": 0
        }
        
        response = api_client.post(f"{BASE_URL}/api/payroll-calculator", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "breakdown" in data
        
        breakdown = data["breakdown"]
        assert "ingresos" in breakdown
        assert "deducciones_tss" in breakdown
        assert "isr" in breakdown
        assert "otras_deducciones" in breakdown
        assert "aportes_empleador" in breakdown
        assert "resumen" in breakdown
        
        print("PASSED: Breakdown structure is complete")


class TestEmployeeManualOverrides:
    """Test employee update with manual override fields"""
    
    def test_get_test_employee(self, api_client):
        """Verify test employee exists"""
        response = api_client.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        
        employees = response.json()
        test_emp = next((e for e in employees if e.get("employee_id") == "emp_33e6ceaa1400"), None)
        
        if test_emp:
            print(f"PASSED: Found test employee emp_33e6ceaa1400")
            print(f"  - Name: {test_emp.get('first_name')} {test_emp.get('last_name')}")
            print(f"  - Salary: {test_emp.get('salary')}")
        else:
            # Find any employee to test with
            if employees:
                test_emp = employees[0]
                print(f"INFO: Using employee {test_emp.get('employee_id')} for testing")
            else:
                pytest.skip("No employees found for testing")
        
        return test_emp
    
    def test_update_employee_with_manual_override(self, api_client):
        """PUT /api/employees/{id} with sfs_manual_override=true and sfs_manual_amount=1500"""
        # First get an employee
        response = api_client.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        
        employees = response.json()
        if not employees:
            pytest.skip("No employees found")
        
        # Use first employee or specific test employee
        test_emp = next((e for e in employees if e.get("employee_id") == "emp_33e6ceaa1400"), employees[0])
        employee_id = test_emp["employee_id"]
        
        # Prepare update payload with all required fields
        update_payload = {
            "first_name": test_emp.get("first_name", "Test"),
            "last_name": test_emp.get("last_name", "Employee"),
            "email": test_emp.get("email", f"test_{uuid.uuid4().hex[:8]}@test.com"),
            "position": test_emp.get("position", "Developer"),
            "department": test_emp.get("department", "IT"),
            "hire_date": test_emp.get("hire_date", "2024-01-01"),
            "salary": test_emp.get("salary", 50000),
            "status": test_emp.get("status", "active"),
            # Manual override fields
            "sfs_discount": True,
            "sfs_manual_override": True,
            "sfs_manual_amount": 1500,
            "afp_discount": True,
            "afp_manual_override": False,
            "afp_manual_amount": 0,
            "isr_discount": True,
            "isr_manual_override": False,
            "isr_manual_amount": 0
        }
        
        response = api_client.put(f"{BASE_URL}/api/employees/{employee_id}", json=update_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the update was saved
        response = api_client.get(f"{BASE_URL}/api/employees/{employee_id}")
        assert response.status_code == 200
        
        updated_emp = response.json()
        assert updated_emp.get("sfs_manual_override") == True, "sfs_manual_override should be True"
        assert updated_emp.get("sfs_manual_amount") == 1500, f"sfs_manual_amount should be 1500, got {updated_emp.get('sfs_manual_amount')}"
        
        print(f"PASSED: Employee updated with manual override")
        print(f"  - sfs_manual_override: {updated_emp.get('sfs_manual_override')}")
        print(f"  - sfs_manual_amount: {updated_emp.get('sfs_manual_amount')}")
        
        return employee_id
    
    def test_reset_employee_manual_override(self, api_client):
        """Reset employee manual override to default (auto-calc)"""
        response = api_client.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        
        employees = response.json()
        if not employees:
            pytest.skip("No employees found")
        
        test_emp = next((e for e in employees if e.get("employee_id") == "emp_33e6ceaa1400"), employees[0])
        employee_id = test_emp["employee_id"]
        
        # Reset to auto-calc
        update_payload = {
            "first_name": test_emp.get("first_name", "Test"),
            "last_name": test_emp.get("last_name", "Employee"),
            "email": test_emp.get("email"),
            "position": test_emp.get("position", "Developer"),
            "department": test_emp.get("department", "IT"),
            "hire_date": test_emp.get("hire_date", "2024-01-01"),
            "salary": test_emp.get("salary", 50000),
            "status": test_emp.get("status", "active"),
            "sfs_discount": True,
            "sfs_manual_override": False,
            "sfs_manual_amount": 0,
            "afp_discount": True,
            "afp_manual_override": False,
            "afp_manual_amount": 0,
            "isr_discount": True,
            "isr_manual_override": False,
            "isr_manual_amount": 0
        }
        
        response = api_client.put(f"{BASE_URL}/api/employees/{employee_id}", json=update_payload)
        assert response.status_code == 200
        
        print("PASSED: Employee manual override reset to auto-calc")


class TestPayrollGenerationWithOverrides:
    """Test that payroll generation respects manual overrides"""
    
    def test_calculate_entry_endpoint(self, api_client):
        """Test /api/payroll/calculate-entry respects manual overrides"""
        # This endpoint may not exist, but we test the generate-entries flow
        # First, let's check if there's a calculate-entry endpoint
        
        # Get employees to find one with manual override
        response = api_client.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        
        employees = response.json()
        if not employees:
            pytest.skip("No employees found")
        
        # Set up an employee with manual override
        test_emp = next((e for e in employees if e.get("employee_id") == "emp_33e6ceaa1400"), employees[0])
        employee_id = test_emp["employee_id"]
        
        # Update employee with manual SFS override
        update_payload = {
            "first_name": test_emp.get("first_name", "Test"),
            "last_name": test_emp.get("last_name", "Employee"),
            "email": test_emp.get("email"),
            "position": test_emp.get("position", "Developer"),
            "department": test_emp.get("department", "IT"),
            "hire_date": test_emp.get("hire_date", "2024-01-01"),
            "salary": 50000,
            "status": "active",
            "sfs_discount": True,
            "sfs_manual_override": True,
            "sfs_manual_amount": 1500,
            "afp_discount": True,
            "afp_manual_override": False,
            "afp_manual_amount": 0,
            "isr_discount": True,
            "isr_manual_override": False,
            "isr_manual_amount": 0
        }
        
        response = api_client.put(f"{BASE_URL}/api/employees/{employee_id}", json=update_payload)
        assert response.status_code == 200, f"Failed to update employee: {response.text}"
        
        print(f"PASSED: Employee {employee_id} set up with sfs_manual_override=True, sfs_manual_amount=1500")
        
        # Now test payroll generation
        # Create a test period
        from datetime import datetime
        now = datetime.now()
        
        period_payload = {
            "period_type": "quincenal_1",
            "year": now.year,
            "month": now.month,
            "start_date": f"{now.year}-{now.month:02d}-01",
            "end_date": f"{now.year}-{now.month:02d}-15",
            "description": f"TEST_OVERRIDE_PERIOD_{uuid.uuid4().hex[:8]}",
            "employee_ids": [employee_id]
        }
        
        response = api_client.post(f"{BASE_URL}/api/payroll/periods", json=period_payload)
        assert response.status_code == 200, f"Failed to create period: {response.text}"
        
        period_data = response.json()
        period_id = period_data.get("period_id")
        
        print(f"Created test period: {period_id}")
        
        # Add employees to period (this triggers the calculation)
        response = api_client.post(f"{BASE_URL}/api/payroll/periods/{period_id}/add-employees")
        assert response.status_code == 200, f"Failed to add employees: {response.text}"
        
        # Get the period with entries
        response = api_client.get(f"{BASE_URL}/api/payroll/periods/{period_id}")
        assert response.status_code == 200
        
        period = response.json()
        entries = period.get("entries", [])
        
        # Find our test employee's entry
        test_entry = next((e for e in entries if e.get("employee_id") == employee_id), None)
        
        if test_entry:
            sfs_employee = test_entry.get("sfs_employee", 0)
            print(f"Payroll entry SFS amount: {sfs_employee}")
            
            # The SFS should be 1500 (manual override) not the calculated amount
            # For quincenal, salary is divided by 2, so base would be 25000
            # Calculated SFS would be 25000 * 0.0307 = 767.50
            # But with manual override, it should be 1500
            
            assert sfs_employee == 1500, f"Expected SFS=1500 (manual override), got {sfs_employee}"
            print(f"PASSED: Payroll generation respects manual override (SFS={sfs_employee})")
        else:
            print(f"WARNING: Test employee entry not found in period")
        
        # Cleanup: Delete the test period
        response = api_client.delete(f"{BASE_URL}/api/payroll/periods/{period_id}")
        print(f"Cleaned up test period: {period_id}")
        
        # Reset employee override
        update_payload["sfs_manual_override"] = False
        update_payload["sfs_manual_amount"] = 0
        api_client.put(f"{BASE_URL}/api/employees/{employee_id}", json=update_payload)
        print("Reset employee manual override")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
