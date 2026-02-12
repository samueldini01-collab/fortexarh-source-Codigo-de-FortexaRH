"""
ISR (Impuesto Sobre la Renta) Calculation Tests - Dominican Republic DGII Tables
Tests for ISR calculation in POST /api/payroll-calculator endpoint

ISR Calculation Method:
1. Subtract TSS (5.94%) from gross salary to get taxable base
2. Annualize the taxable base (x12)
3. Apply progressive tax brackets:
   - Exento: up to RD$416,220 annual (0%)
   - 15%: RD$416,220.01 - RD$624,329
   - 20%: RD$624,329.01 - RD$867,123
   - 25%: above RD$867,123.01
4. Divide annual ISR by 12 to get monthly ISR
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fortexa-hr-1.preview.emergentagent.com')

# TSS Rates
TSS_EMPLOYEE_TOTAL = 0.0594  # 5.94% (SFS 3.07% + AFP 2.87%)

# ISR Annual Thresholds (DGII 2024/2025)
ISR_ANNUAL_EXEMPT = 416220.00
ISR_ANNUAL_BRACKET_1 = 624329.00
ISR_ANNUAL_BRACKET_2 = 867123.00


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
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


class TestISRExemptBracket:
    """Tests for ISR Exempt bracket (0%) - Annual taxable base <= RD$416,220"""
    
    def test_isr_exempt_salary_30000(self, api_client):
        """
        Test ISR for RD$30,000 salary - should be EXEMPT
        Calculation:
        - Gross: 30,000
        - TSS: 30,000 * 5.94% = 1,782
        - Taxable base monthly: 30,000 - 1,782 = 28,218
        - Annual taxable: 28,218 * 12 = 338,616
        - 338,616 < 416,220 = EXEMPT
        """
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_Exempt_30k",
                "base_salary": 30000,
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
        
        # Verify ISR fields exist
        assert "isr_monthly" in data, "Response should contain isr_monthly"
        assert "isr_bracket" in data, "Response should contain isr_bracket"
        assert "isr_annual_taxable" in data, "Response should contain isr_annual_taxable"
        
        # Verify ISR is exempt (0)
        assert data["isr_monthly"] == 0, f"ISR monthly should be 0 (exempt), got {data['isr_monthly']}"
        assert "Exento" in data["isr_bracket"] or "0%" in data["isr_bracket"], f"ISR bracket should be Exento, got {data['isr_bracket']}"
        
        # Verify annual taxable base is below exempt threshold
        assert data["isr_annual_taxable"] < ISR_ANNUAL_EXEMPT, f"Annual taxable {data['isr_annual_taxable']} should be < {ISR_ANNUAL_EXEMPT}"
        
        # Verify total_deductions includes TSS but no ISR
        expected_tss = round(30000 * TSS_EMPLOYEE_TOTAL, 2)
        assert abs(data["total_tss_employee"] - expected_tss) < 1, f"TSS should be ~{expected_tss}, got {data['total_tss_employee']}"
        
        # total_employee_deductions should equal TSS (no ISR)
        assert data["total_employee_deductions"] == data["total_tss_employee"], \
            f"Total employee deductions should equal TSS when ISR is 0"
    
    def test_isr_exempt_salary_34000(self, api_client):
        """
        Test ISR for RD$34,000 salary - should be EXEMPT (edge case near threshold)
        Annual taxable: ~384,000 < 416,220
        """
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_Exempt_34k",
                "base_salary": 34000,
                "days_worked": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["isr_monthly"] == 0, f"ISR should be 0 (exempt), got {data['isr_monthly']}"
        assert "Exento" in data["isr_bracket"], f"Should be Exento bracket, got {data['isr_bracket']}"


class TestISR15PercentBracket:
    """Tests for ISR 15% bracket - Annual taxable RD$416,220.01 - RD$624,329"""
    
    def test_isr_15_percent_salary_50000(self, api_client):
        """
        Test ISR for RD$50,000 salary - should be in 15% bracket
        Calculation:
        - Gross: 50,000
        - TSS: 50,000 * 5.94% = 2,970
        - Taxable base monthly: 50,000 - 2,970 = 47,030
        - Annual taxable: 47,030 * 12 = 564,360
        - 416,220 < 564,360 < 624,329 = 15% bracket
        - Excess over exempt: 564,360 - 416,220 = 148,140
        - ISR annual: 148,140 * 15% = 22,221
        - ISR monthly: 22,221 / 12 = 1,851.75
        """
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_15pct_50k",
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
        
        # Verify ISR fields exist
        assert "isr_monthly" in data, "Response should contain isr_monthly"
        assert "isr_bracket" in data, "Response should contain isr_bracket"
        assert "isr_annual_taxable" in data, "Response should contain isr_annual_taxable"
        assert "isr_annual" in data, "Response should contain isr_annual"
        
        # Verify bracket is 15%
        assert "15%" in data["isr_bracket"], f"ISR bracket should be 15%, got {data['isr_bracket']}"
        
        # Verify annual taxable is in 15% range
        assert ISR_ANNUAL_EXEMPT < data["isr_annual_taxable"] < ISR_ANNUAL_BRACKET_1, \
            f"Annual taxable {data['isr_annual_taxable']} should be between {ISR_ANNUAL_EXEMPT} and {ISR_ANNUAL_BRACKET_1}"
        
        # Verify ISR is positive
        assert data["isr_monthly"] > 0, f"ISR monthly should be > 0, got {data['isr_monthly']}"
        
        # Verify ISR calculation (approximate)
        # Annual taxable ~564,360, excess ~148,140, ISR annual ~22,221, monthly ~1,851
        assert 1500 < data["isr_monthly"] < 2200, f"ISR monthly should be ~1,851, got {data['isr_monthly']}"
        
        # Verify total_employee_deductions = TSS + ISR
        expected_total = data["total_tss_employee"] + data["isr_monthly"]
        assert abs(data["total_employee_deductions"] - expected_total) < 1, \
            f"Total employee deductions should be TSS + ISR = {expected_total}, got {data['total_employee_deductions']}"
    
    def test_isr_15_percent_salary_45000(self, api_client):
        """
        Test ISR for RD$45,000 salary - should be in 15% bracket
        Annual taxable: ~507,924 (in 15% range)
        """
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_15pct_45k",
                "base_salary": 45000,
                "days_worked": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "15%" in data["isr_bracket"], f"Should be 15% bracket, got {data['isr_bracket']}"
        assert data["isr_monthly"] > 0, f"ISR should be > 0, got {data['isr_monthly']}"


class TestISR20PercentBracket:
    """Tests for ISR 20% bracket - Annual taxable RD$624,329.01 - RD$867,123"""
    
    def test_isr_20_percent_salary_60000(self, api_client):
        """
        Test ISR for RD$60,000 salary - should be in 20% bracket
        Calculation:
        - Gross: 60,000
        - TSS: 60,000 * 5.94% = 3,564
        - Taxable base monthly: 60,000 - 3,564 = 56,436
        - Annual taxable: 56,436 * 12 = 677,232
        - 624,329 < 677,232 < 867,123 = 20% bracket
        """
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_20pct_60k",
                "base_salary": 60000,
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
        
        # Verify bracket is 20%
        assert "20%" in data["isr_bracket"], f"ISR bracket should be 20%, got {data['isr_bracket']}"
        
        # Verify annual taxable is in 20% range
        assert ISR_ANNUAL_BRACKET_1 < data["isr_annual_taxable"] < ISR_ANNUAL_BRACKET_2, \
            f"Annual taxable {data['isr_annual_taxable']} should be between {ISR_ANNUAL_BRACKET_1} and {ISR_ANNUAL_BRACKET_2}"
        
        # Verify ISR is positive and higher than 15% bracket
        assert data["isr_monthly"] > 2000, f"ISR monthly should be > 2000 for 20% bracket, got {data['isr_monthly']}"


class TestISR25PercentBracket:
    """Tests for ISR 25% bracket - Annual taxable > RD$867,123"""
    
    def test_isr_25_percent_salary_80000(self, api_client):
        """
        Test ISR for RD$80,000 salary - should be in 25% bracket
        Calculation:
        - Gross: 80,000
        - TSS: 80,000 * 5.94% = 4,752
        - Taxable base monthly: 80,000 - 4,752 = 75,248
        - Annual taxable: 75,248 * 12 = 902,976
        - 902,976 > 867,123 = 25% bracket
        """
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_25pct_80k",
                "base_salary": 80000,
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
        
        # Verify bracket is 25%
        assert "25%" in data["isr_bracket"], f"ISR bracket should be 25%, got {data['isr_bracket']}"
        
        # Verify annual taxable is above 25% threshold
        assert data["isr_annual_taxable"] > ISR_ANNUAL_BRACKET_2, \
            f"Annual taxable {data['isr_annual_taxable']} should be > {ISR_ANNUAL_BRACKET_2}"
        
        # Verify ISR is positive and significant
        assert data["isr_monthly"] > 3000, f"ISR monthly should be > 3000 for 25% bracket, got {data['isr_monthly']}"
    
    def test_isr_25_percent_salary_100000(self, api_client):
        """
        Test ISR for RD$100,000 salary - should be in 25% bracket
        Annual taxable: ~1,128,720 (well above 867,123)
        """
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_25pct_100k",
                "base_salary": 100000,
                "days_worked": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "25%" in data["isr_bracket"], f"Should be 25% bracket, got {data['isr_bracket']}"
        assert data["isr_monthly"] > 5000, f"ISR should be > 5000 for 100k salary, got {data['isr_monthly']}"


class TestISRResponseStructure:
    """Tests for ISR fields in API response"""
    
    def test_isr_fields_exist_in_response(self, api_client):
        """Verify all ISR-related fields exist in response"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_Fields",
                "base_salary": 50000,
                "days_worked": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Required ISR fields
        isr_fields = [
            "isr_taxable_base",      # Base gravable mensual
            "isr_annual_taxable",    # Base gravable anualizada
            "isr_annual",            # ISR anual calculado
            "isr_monthly",           # ISR mensual a retener
            "isr_bracket"            # Tramo de impuesto aplicado
        ]
        
        for field in isr_fields:
            assert field in data, f"Missing ISR field: {field}"
    
    def test_total_deductions_includes_isr(self, api_client):
        """Verify total_deductions = TSS + ISR + other deductions"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Total_Deductions",
                "base_salary": 50000,
                "days_worked": 30,
                "loan_deduction": 1000,
                "other_deductions": 500
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # total_deductions = total_employee_deductions + total_other_deductions
        # total_employee_deductions = TSS + ISR
        expected_total = data["total_employee_deductions"] + data["total_other_deductions"]
        assert abs(data["total_deductions"] - expected_total) < 1, \
            f"total_deductions should be {expected_total}, got {data['total_deductions']}"
        
        # Verify TSS + ISR = total_employee_deductions
        expected_employee = data["total_tss_employee"] + data["isr_monthly"]
        assert abs(data["total_employee_deductions"] - expected_employee) < 1, \
            f"total_employee_deductions should be TSS + ISR = {expected_employee}, got {data['total_employee_deductions']}"


class TestISRCalculationAccuracy:
    """Tests for ISR calculation accuracy"""
    
    def test_isr_taxable_base_calculation(self, api_client):
        """Verify taxable base = gross - TSS"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Taxable_Base",
                "base_salary": 50000,
                "days_worked": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Taxable base = total_earnings - total_tss_employee
        expected_taxable_base = data["total_earnings"] - data["total_tss_employee"]
        assert abs(data["isr_taxable_base"] - expected_taxable_base) < 1, \
            f"Taxable base should be {expected_taxable_base}, got {data['isr_taxable_base']}"
    
    def test_isr_annual_taxable_is_monthly_times_12(self, api_client):
        """Verify annual taxable = monthly taxable base * 12"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Annual_Taxable",
                "base_salary": 50000,
                "days_worked": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_annual = data["isr_taxable_base"] * 12
        assert abs(data["isr_annual_taxable"] - expected_annual) < 1, \
            f"Annual taxable should be {expected_annual}, got {data['isr_annual_taxable']}"
    
    def test_isr_monthly_is_annual_divided_by_12(self, api_client):
        """Verify monthly ISR = annual ISR / 12"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_Monthly_ISR",
                "base_salary": 50000,
                "days_worked": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_monthly = round(data["isr_annual"] / 12, 2)
        assert abs(data["isr_monthly"] - expected_monthly) < 1, \
            f"Monthly ISR should be {expected_monthly}, got {data['isr_monthly']}"


class TestISRWithBonusesAndCommissions:
    """Tests for ISR calculation with additional income"""
    
    def test_isr_with_bonuses_pushes_to_higher_bracket(self, api_client):
        """Test that bonuses can push salary into higher ISR bracket"""
        # Base salary 35000 would be exempt
        # With 20000 bonus, total 55000 should be in 15% bracket
        response = api_client.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "employee_name": "TEST_ISR_Bonus",
                "base_salary": 35000,
                "days_worked": 30,
                "bonuses": 20000,
                "commissions": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Total earnings should be 55000
        assert data["total_earnings"] == 55000, f"Total earnings should be 55000, got {data['total_earnings']}"
        
        # Should be in 15% bracket (not exempt)
        assert "15%" in data["isr_bracket"], f"Should be 15% bracket with bonus, got {data['isr_bracket']}"
        assert data["isr_monthly"] > 0, f"ISR should be > 0 with bonus, got {data['isr_monthly']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
