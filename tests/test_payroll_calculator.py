"""
Payroll Calculator API Tests - Dominican Republic TSS & ISR Calculations
Tests for POST /api/payroll-calculator and POST /api/payroll-calculator/save endpoints
TSS Rates:
- Employee: SFS 3.07%, AFP 2.87%
- Employer: SFS 7.09%, AFP 7.10%, SRL 1%, INFOTEP 1%
ISR (DGII Tables):
- Exento: up to RD$416,220 annual
- 15%: RD$416,220.01 - RD$624,329
- 20%: RD$624,329.01 - RD$867,123
- 25%: above RD$867,123.01
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://staffpulse-30.preview.emergentagent.com')

# TSS Rates for Dominican Republic
SFS_EMPLOYEE_RATE = 0.0307  # 3.07%
AFP_EMPLOYEE_RATE = 0.0287  # 2.87%
TSS_EMPLOYEE_TOTAL = SFS_EMPLOYEE_RATE + AFP_EMPLOYEE_RATE  # 5.94%
SFS_EMPLOYER_RATE = 0.0709  # 7.09%
AFP_EMPLOYER_RATE = 0.0710  # 7.10%
SRL_EMPLOYER_RATE = 0.01    # 1%
INFOTEP_EMPLOYER_RATE = 0.01  # 1%

# ISR Thresholds
ISR_ANNUAL_EXEMPT = 416220.00


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    # Try to login first
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test_calc@fortexarh.com", "password": "test123456"}
    )
    
    if login_response.status_code == 200:
        return login_response.json().get("token")
    
    # If login fails, try to register
    register_response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "email": "test_calc@fortexarh.com",
            "password": "test123456",
            "name": "Test Calculator User",
            "company_name": "Test Company"
        }
    )
    
    if register_response.status_code == 200:
        return register_response.json().get("token")
    
    pytest.skip("Could not authenticate - skipping tests")


@pytest.fixture
def api_client(auth_token):
    """Create authenticated API client"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestPayrollCalculatorEndpoint:
    """Tests for POST /api/payroll-calculator endpoint"""
    
    def test_basic_calculation_50000_salary(self, api_client):
        """Test basic calculation with 50000 base salary - verify TSS rates and ISR"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Basic Employee",
                "base_salary": 50000,
                "days_worked": 30,
                "hours_extra": 0,
                "hour_rate": 0,
                "bonuses": 0,
                "commissions": 0,
                "loan_deduction": 0,
                "other_deductions": 0
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify employee deductions (TSS)
        assert data["sfs_employee"] == 1535.0, f"SFS Employee should be 1535 (3.07% of 50000), got {data['sfs_employee']}"
        assert data["afp_employee"] == 1435.0, f"AFP Employee should be 1435 (2.87% of 50000), got {data['afp_employee']}"
        assert data["total_tss_employee"] == 2970.0, f"Total TSS employee should be 2970, got {data['total_tss_employee']}"
        
        # Verify ISR is calculated (50000 salary is in 15% bracket)
        assert "isr_monthly" in data, "Response should contain isr_monthly"
        assert "isr_bracket" in data, "Response should contain isr_bracket"
        assert data["isr_monthly"] > 0, f"ISR should be > 0 for 50000 salary, got {data['isr_monthly']}"
        assert "15%" in data["isr_bracket"], f"Should be 15% bracket, got {data['isr_bracket']}"
        
        # Verify total_employee_deductions = TSS + ISR
        expected_employee_deductions = data["total_tss_employee"] + data["isr_monthly"]
        assert abs(data["total_employee_deductions"] - expected_employee_deductions) < 1, \
            f"Total employee deductions should be TSS + ISR = {expected_employee_deductions}, got {data['total_employee_deductions']}"
        
        # Verify employer contributions
        assert data["sfs_employer"] == 3545.0, f"SFS Employer should be 3545 (7.09% of 50000), got {data['sfs_employer']}"
        assert data["afp_employer"] == 3550.0, f"AFP Employer should be 3550 (7.10% of 50000), got {data['afp_employer']}"
        assert data["srl_employer"] == 500.0, f"SRL should be 500 (1% of 50000), got {data['srl_employer']}"
        assert data["infotep_employer"] == 500.0, f"INFOTEP should be 500 (1% of 50000), got {data['infotep_employer']}"
        assert data["total_employer_contributions"] == 8095.0, f"Total employer contributions should be 8095, got {data['total_employer_contributions']}"
        
        # Verify net salary = total_earnings - total_deductions
        expected_net = data["total_earnings"] - data["total_deductions"]
        assert abs(data["net_salary"] - expected_net) < 1, f"Net salary should be {expected_net}, got {data['net_salary']}"
        
        # Verify breakdown structure exists
        assert "breakdown" in data
        assert "ingresos" in data["breakdown"]
        assert "deducciones_empleado" in data["breakdown"]
        assert "aportes_empleador" in data["breakdown"]
        assert "resumen" in data["breakdown"]
    
    def test_calculation_with_extra_hours(self, api_client):
        """Test calculation with extra hours"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Extra Hours Employee",
                "base_salary": 30000,
                "days_worked": 30,
                "hours_extra": 10,
                "hour_rate": 200,
                "bonuses": 0,
                "commissions": 0,
                "loan_deduction": 0,
                "other_deductions": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Extra hours pay = 10 * 200 = 2000
        assert data["extra_hours_pay"] == 2000.0
        
        # Total earnings = 30000 + 2000 = 32000
        assert data["total_earnings"] == 32000.0
        
        # TSS calculated on total earnings
        expected_sfs = round(32000 * SFS_EMPLOYEE_RATE, 2)
        expected_afp = round(32000 * AFP_EMPLOYEE_RATE, 2)
        assert data["sfs_employee"] == expected_sfs
        assert data["afp_employee"] == expected_afp
    
    def test_calculation_with_bonuses_and_commissions(self, api_client):
        """Test calculation with bonuses and commissions"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Bonus Employee",
                "base_salary": 40000,
                "days_worked": 30,
                "hours_extra": 0,
                "hour_rate": 0,
                "bonuses": 5000,
                "commissions": 3000,
                "loan_deduction": 0,
                "other_deductions": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Total earnings = 40000 + 5000 + 3000 = 48000
        assert data["total_earnings"] == 48000.0
        assert data["bonuses"] == 5000.0
        assert data["commissions"] == 3000.0
    
    def test_calculation_with_deductions(self, api_client):
        """Test calculation with loan and other deductions"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Deductions Employee",
                "base_salary": 60000,
                "days_worked": 30,
                "hours_extra": 0,
                "hour_rate": 0,
                "bonuses": 0,
                "commissions": 0,
                "loan_deduction": 2000,
                "other_deductions": 1000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify other deductions
        assert data["loan_deduction"] == 2000.0
        assert data["other_deductions"] == 1000.0
        assert data["total_other_deductions"] == 3000.0
        
        # TSS deductions on 60000
        tss_deductions = round(60000 * (SFS_EMPLOYEE_RATE + AFP_EMPLOYEE_RATE), 2)
        total_deductions = tss_deductions + 3000
        
        assert data["total_deductions"] == total_deductions
        
        # Net salary
        expected_net = 60000 - total_deductions
        assert data["net_salary"] == expected_net
    
    def test_calculation_partial_month(self, api_client):
        """Test calculation with partial month (15 days worked)"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Partial Month Employee",
                "base_salary": 60000,
                "days_worked": 15,
                "hours_extra": 0,
                "hour_rate": 0,
                "bonuses": 0,
                "commissions": 0,
                "loan_deduction": 0,
                "other_deductions": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Proportional salary = (60000 / 30) * 15 = 30000
        assert data["proportional_salary"] == 30000.0
        assert data["total_earnings"] == 30000.0
        
        # TSS calculated on proportional salary
        expected_sfs = round(30000 * SFS_EMPLOYEE_RATE, 2)
        expected_afp = round(30000 * AFP_EMPLOYEE_RATE, 2)
        assert data["sfs_employee"] == expected_sfs
        assert data["afp_employee"] == expected_afp
    
    def test_calculation_without_employee_name(self, api_client):
        """Test calculation without employee name (should default to 'Sin asignar')"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "base_salary": 25000,
                "days_worked": 30,
                "hours_extra": 0,
                "hour_rate": 0,
                "bonuses": 0,
                "commissions": 0,
                "loan_deduction": 0,
                "other_deductions": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still calculate correctly
        assert data["base_salary"] == 25000.0
        assert data["total_earnings"] == 25000.0
    
    def test_calculation_invalid_salary(self, api_client):
        """Test calculation with invalid (negative) salary"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Invalid",
                "base_salary": -1000,
                "days_worked": 30
            }
        )
        
        # API should either reject or handle gracefully
        # Based on implementation, it may accept negative values
        # This test documents current behavior
        assert response.status_code in [200, 400, 422]
    
    def test_calculation_response_structure(self, api_client):
        """Test that response contains all required fields"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Structure",
                "base_salary": 50000,
                "days_worked": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        required_fields = [
            "base_salary", "days_worked", "proportional_salary", "total_earnings",
            "sfs_employee", "afp_employee", "total_employee_deductions",
            "total_deductions", "net_salary",
            "sfs_employer", "afp_employer", "srl_employer", "infotep_employer",
            "total_employer_contributions", "breakdown"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestPayrollCalculatorSaveEndpoint:
    """Tests for POST /api/payroll-calculator/save endpoint"""
    
    def test_save_calculation(self, api_client):
        """Test saving a payroll calculation"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator/save",
            json={
                "employee_name": "TEST_Save Employee",
                "base_salary": 45000,
                "days_worked": 30,
                "hours_extra": 0,
                "hour_rate": 0,
                "bonuses": 0,
                "commissions": 0,
                "loan_deduction": 0,
                "other_deductions": 0
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert "calculation_id" in data, "Response should contain calculation_id"
        assert "message" in data, "Response should contain message"
        assert "net_salary" in data, "Response should contain net_salary"
        
        # Verify calculation_id format
        assert data["calculation_id"].startswith("calc_"), f"calculation_id should start with 'calc_', got {data['calculation_id']}"
        
        # Verify net salary calculation
        expected_tss = round(45000 * (SFS_EMPLOYEE_RATE + AFP_EMPLOYEE_RATE), 2)
        expected_net = round(45000 - expected_tss, 2)
        assert abs(data["net_salary"] - expected_net) < 0.01, f"Net salary should be ~{expected_net}, got {data['net_salary']}"
    
    def test_save_calculation_with_all_fields(self, api_client):
        """Test saving calculation with all fields populated"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator/save",
            json={
                "employee_name": "TEST_Full Save Employee",
                "base_salary": 80000,
                "days_worked": 25,
                "hours_extra": 8,
                "hour_rate": 400,
                "bonuses": 10000,
                "commissions": 5000,
                "loan_deduction": 3000,
                "other_deductions": 1500
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "calculation_id" in data
        assert data["net_salary"] > 0


class TestPayrollCalculatorAuthentication:
    """Tests for authentication requirements"""
    
    def test_calculator_requires_auth(self):
        """Test that calculator endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={"base_salary": 50000, "days_worked": 30}
        )
        
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"
    
    def test_save_requires_auth(self):
        """Test that save endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator/save",
            json={"base_salary": 50000, "days_worked": 30}
        )
        
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"


class TestTSSRatesAccuracy:
    """Tests to verify TSS rates are correctly applied"""
    
    def test_sfs_employee_rate_3_07_percent(self, api_client):
        """Verify SFS employee rate is exactly 3.07%"""
        test_salary = 100000  # Use round number for easy verification
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={"base_salary": test_salary, "days_worked": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_sfs = round(test_salary * 0.0307, 2)  # 3070.0
        assert data["sfs_employee"] == expected_sfs, f"SFS should be {expected_sfs} (3.07%), got {data['sfs_employee']}"
    
    def test_afp_employee_rate_2_87_percent(self, api_client):
        """Verify AFP employee rate is exactly 2.87%"""
        test_salary = 100000
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={"base_salary": test_salary, "days_worked": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_afp = round(test_salary * 0.0287, 2)  # 2870.0
        assert data["afp_employee"] == expected_afp, f"AFP should be {expected_afp} (2.87%), got {data['afp_employee']}"
    
    def test_sfs_employer_rate_7_09_percent(self, api_client):
        """Verify SFS employer rate is exactly 7.09%"""
        test_salary = 100000
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={"base_salary": test_salary, "days_worked": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_sfs = round(test_salary * 0.0709, 2)  # 7090.0
        assert data["sfs_employer"] == expected_sfs, f"SFS Employer should be {expected_sfs} (7.09%), got {data['sfs_employer']}"
    
    def test_afp_employer_rate_7_10_percent(self, api_client):
        """Verify AFP employer rate is exactly 7.10%"""
        test_salary = 100000
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={"base_salary": test_salary, "days_worked": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_afp = round(test_salary * 0.0710, 2)  # 7100.0
        assert data["afp_employer"] == expected_afp, f"AFP Employer should be {expected_afp} (7.10%), got {data['afp_employer']}"
    
    def test_srl_employer_rate_1_percent(self, api_client):
        """Verify SRL employer rate is exactly 1%"""
        test_salary = 100000
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={"base_salary": test_salary, "days_worked": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_srl = round(test_salary * 0.01, 2)  # 1000.0
        assert data["srl_employer"] == expected_srl, f"SRL should be {expected_srl} (1%), got {data['srl_employer']}"
    
    def test_infotep_employer_rate_1_percent(self, api_client):
        """Verify INFOTEP employer rate is exactly 1%"""
        test_salary = 100000
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={"base_salary": test_salary, "days_worked": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_infotep = round(test_salary * 0.01, 2)  # 1000.0
        assert data["infotep_employer"] == expected_infotep, f"INFOTEP should be {expected_infotep} (1%), got {data['infotep_employer']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
