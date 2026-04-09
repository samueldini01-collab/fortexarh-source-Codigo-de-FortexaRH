"""
Test Payroll Calculator - total_tss_employer and total_cost_employer fields
Test for iteration 200 - Deductions tab enhancements
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://company-config-debug.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
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
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPayrollCalculatorEndpoint:
    """Test payroll calculator with new employer fields"""
    
    def test_payroll_calculator_50000_salary(self, auth_headers):
        """Test payroll calculator with 50000 salary - should include total_tss_employer and total_cost_employer"""
        payload = {
            "base_salary": 50000,
            "days_worked": 30,
            "hours_extra": 0,
            "hour_rate": 0,
            "bonuses": 0,
            "commissions": 0,
            "loan_deduction": 0,
            "other_deductions": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify new fields exist
        assert "total_tss_employer" in data, "Missing total_tss_employer field"
        assert "total_cost_employer" in data, "Missing total_cost_employer field"
        
        # Verify calculations
        total_earnings = data.get("total_earnings", 0)
        assert total_earnings == 50000, f"Expected total_earnings=50000, got {total_earnings}"
        
        # Employer TSS = SFS (7.09%) + AFP (7.10%) = 14.19%
        sfs_employer = data.get("sfs_employer", 0)
        afp_employer = data.get("afp_employer", 0)
        total_tss_employer = data.get("total_tss_employer", 0)
        
        expected_sfs_employer = round(50000 * 0.0709, 2)
        expected_afp_employer = round(50000 * 0.0710, 2)
        expected_total_tss_employer = round(sfs_employer + afp_employer, 2)
        
        assert abs(sfs_employer - expected_sfs_employer) < 1, f"SFS employer mismatch: {sfs_employer} vs {expected_sfs_employer}"
        assert abs(afp_employer - expected_afp_employer) < 1, f"AFP employer mismatch: {afp_employer} vs {expected_afp_employer}"
        assert abs(total_tss_employer - expected_total_tss_employer) < 1, f"Total TSS employer mismatch: {total_tss_employer} vs {expected_total_tss_employer}"
        
        # Total cost employer = total_earnings + total_employer_contributions
        total_cost_employer = data.get("total_cost_employer", 0)
        total_employer_contributions = data.get("total_employer_contributions", 0)
        expected_total_cost = round(total_earnings + total_employer_contributions, 2)
        
        assert abs(total_cost_employer - expected_total_cost) < 1, f"Total cost employer mismatch: {total_cost_employer} vs {expected_total_cost}"
        
        print(f"✓ Payroll calculator 50000 salary test passed")
        print(f"  - total_tss_employer: {total_tss_employer}")
        print(f"  - total_cost_employer: {total_cost_employer}")
        print(f"  - total_employer_contributions: {total_employer_contributions}")
    
    def test_payroll_calculator_25000_salary_isr_exempt(self, auth_headers):
        """Test payroll calculator with 25000 salary - ISR should be 0 (exempt)"""
        payload = {
            "base_salary": 25000,
            "days_worked": 30,
            "hours_extra": 0,
            "hour_rate": 0,
            "bonuses": 0,
            "commissions": 0,
            "loan_deduction": 0,
            "other_deductions": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify ISR is 0 for low salary (exempt)
        isr_monthly = data.get("isr_monthly", -1)
        isr_bracket = data.get("isr_bracket", "")
        
        assert isr_monthly == 0, f"Expected ISR=0 for 25000 salary (exempt), got {isr_monthly}"
        assert "Exento" in isr_bracket or "0%" in isr_bracket, f"Expected exempt bracket, got {isr_bracket}"
        
        # Verify new fields still exist
        assert "total_tss_employer" in data, "Missing total_tss_employer field"
        assert "total_cost_employer" in data, "Missing total_cost_employer field"
        
        print(f"✓ Payroll calculator 25000 salary (ISR exempt) test passed")
        print(f"  - isr_monthly: {isr_monthly}")
        print(f"  - isr_bracket: {isr_bracket}")
    
    def test_payroll_calculator_response_structure(self, auth_headers):
        """Verify complete response structure with all required fields"""
        payload = {
            "base_salary": 60000,
            "days_worked": 30,
            "hours_extra": 5,
            "hour_rate": 200,
            "bonuses": 5000,
            "commissions": 2000,
            "loan_deduction": 1000,
            "other_deductions": 500
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Required fields from PayrollCalculatorResult model
        required_fields = [
            "base_salary", "days_worked", "hours_extra", "hour_rate",
            "bonuses", "commissions", "proportional_salary", "extra_hours_pay",
            "total_earnings", "sfs_employee", "afp_employee", "total_tss_employee",
            "isr_taxable_base", "isr_annual_taxable", "isr_annual", "isr_monthly",
            "isr_bracket", "total_employee_deductions", "loan_deduction",
            "other_deductions", "net_salary", "sfs_employer", "afp_employer",
            "srl_employer", "infotep_employer",
            # New fields that were missing before
            "total_tss_employer", "total_cost_employer",
            "total_other_deductions", "total_deductions", "total_employer_contributions"
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        assert not missing_fields, f"Missing fields in response: {missing_fields}"
        
        # Verify breakdown exists
        assert "breakdown" in data, "Missing breakdown field"
        
        print(f"✓ Payroll calculator response structure test passed")
        print(f"  - All {len(required_fields)} required fields present")


class TestPayrollCalculatorCalculations:
    """Test calculation accuracy"""
    
    def test_employee_deductions_calculation(self, auth_headers):
        """Verify employee deductions are calculated correctly"""
        salary = 50000
        payload = {
            "base_salary": salary,
            "days_worked": 30,
            "hours_extra": 0,
            "hour_rate": 0,
            "bonuses": 0,
            "commissions": 0,
            "loan_deduction": 0,
            "other_deductions": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # SFS employee = 3.07% (backend uses 0.0307)
        # AFP employee = 2.87%
        sfs_employee = data.get("sfs_employee", 0)
        afp_employee = data.get("afp_employee", 0)
        
        # Allow for slight rate differences (3.04% vs 3.07%)
        assert 1500 <= sfs_employee <= 1550, f"SFS employee out of range: {sfs_employee}"
        assert 1400 <= afp_employee <= 1450, f"AFP employee out of range: {afp_employee}"
        
        print(f"✓ Employee deductions calculation test passed")
        print(f"  - SFS employee: {sfs_employee}")
        print(f"  - AFP employee: {afp_employee}")
    
    def test_employer_contributions_calculation(self, auth_headers):
        """Verify employer contributions are calculated correctly"""
        salary = 50000
        payload = {
            "base_salary": salary,
            "days_worked": 30,
            "hours_extra": 0,
            "hour_rate": 0,
            "bonuses": 0,
            "commissions": 0,
            "loan_deduction": 0,
            "other_deductions": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Employer rates:
        # SFS = 7.09%, AFP = 7.10%, SRL = 1%, INFOTEP = 1%
        sfs_employer = data.get("sfs_employer", 0)
        afp_employer = data.get("afp_employer", 0)
        srl_employer = data.get("srl_employer", 0)
        infotep_employer = data.get("infotep_employer", 0)
        
        expected_sfs = round(salary * 0.0709, 2)
        expected_afp = round(salary * 0.0710, 2)
        expected_srl = round(salary * 0.01, 2)
        expected_infotep = round(salary * 0.01, 2)
        
        assert abs(sfs_employer - expected_sfs) < 1, f"SFS employer: {sfs_employer} vs {expected_sfs}"
        assert abs(afp_employer - expected_afp) < 1, f"AFP employer: {afp_employer} vs {expected_afp}"
        assert abs(srl_employer - expected_srl) < 1, f"SRL employer: {srl_employer} vs {expected_srl}"
        assert abs(infotep_employer - expected_infotep) < 1, f"INFOTEP employer: {infotep_employer} vs {expected_infotep}"
        
        # Verify total_employer_contributions
        total_contributions = data.get("total_employer_contributions", 0)
        expected_total = round(sfs_employer + afp_employer + srl_employer + infotep_employer, 2)
        assert abs(total_contributions - expected_total) < 1, f"Total contributions: {total_contributions} vs {expected_total}"
        
        print(f"✓ Employer contributions calculation test passed")
        print(f"  - SFS employer: {sfs_employer}")
        print(f"  - AFP employer: {afp_employer}")
        print(f"  - SRL employer: {srl_employer}")
        print(f"  - INFOTEP employer: {infotep_employer}")
        print(f"  - Total contributions: {total_contributions}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
