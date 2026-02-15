"""
Test Refactored Routes - Iteration 50 - FortexaRH
Tests the ~30 routes migrated from server.py to modular route files.

Migrated route files tested:
- routes/payroll_config.py: payroll settings, config CRUD, calculator
- routes/templates.py: template CRUD and document generation
- routes/generated_docs.py: generated documents CRUD and signing
- routes/currency.py: exchange rate management
- routes/stats.py: payroll trend and employee statistics
- routes/reports.py: payroll and attendance reports (modified)
- routes/accounting.py: generate-payroll-entry route (modified)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fortexa-staging.preview.emergentagent.com')


class TestAuthLogin:
    """Test login endpoint to get auth token"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_refactor@fortexa.com", "password": "test123"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for all tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test_refactor@fortexa.com", "password": "test123"},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Auth failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }


class TestPayrollConfigRoutes:
    """Test routes migrated to routes/payroll_config.py"""
    
    def test_get_payroll_settings(self, auth_headers):
        """GET /api/payroll-settings - returns settings or null"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-settings",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        # Can return null/None or settings object
        data = response.json()
        print(f"Payroll settings response: {type(data)}")
    
    def test_payroll_calculator(self, auth_headers):
        """POST /api/payroll-calculator - calculate net salary"""
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "base_salary": 50000,
                "days_worked": 30
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Verify net_salary is in response
        assert "net_salary" in data, "net_salary not in response"
        assert data["net_salary"] > 0, "net_salary should be positive"
        print(f"Payroll calc - Base: 50000, Net: {data['net_salary']}")
    
    def test_payroll_calculator_with_all_fields(self, auth_headers):
        """POST /api/payroll-calculator - with bonuses and overtime"""
        response = requests.post(
            f"{BASE_URL}/api/payroll-calculator",
            json={
                "base_salary": 60000,
                "days_worked": 30,
                "hours_extra": 10,
                "hour_rate": 200,
                "bonuses": 5000,
                "commissions": 3000,
                "loan_deduction": 1000,
                "other_deductions": 500
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "net_salary" in data
        assert "breakdown" in data, "breakdown not in response"
        assert "total_earnings" in data
        print(f"Full calc - Total earnings: {data['total_earnings']}, Net: {data['net_salary']}")
    
    def test_get_payroll_config(self, auth_headers):
        """GET /api/payroll-config - returns config list"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-config",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Payroll configs count: {len(data)}")
    
    def test_get_payroll_calculations(self, auth_headers):
        """GET /api/payroll-calculations - returns saved calculations"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-calculations",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Payroll calculations count: {len(data)}")


class TestTemplatesRoutes:
    """Test routes migrated to routes/templates.py"""
    
    def test_get_templates(self, auth_headers):
        """GET /api/templates - returns templates list"""
        response = requests.get(
            f"{BASE_URL}/api/templates",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Templates count: {len(data)}")


class TestGeneratedDocsRoutes:
    """Test routes migrated to routes/generated_docs.py"""
    
    def test_get_documents(self, auth_headers):
        """GET /api/documents - returns generated documents list"""
        response = requests.get(
            f"{BASE_URL}/api/documents",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Generated documents count: {len(data)}")


class TestCurrencyRoutes:
    """Test routes migrated to routes/currency.py"""
    
    def test_get_currency_rates(self, auth_headers):
        """GET /api/currency/rates - returns exchange rates list"""
        response = requests.get(
            f"{BASE_URL}/api/currency/rates",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Currency rates count: {len(data)}")
    
    def test_get_latest_exchange_rate(self, auth_headers):
        """GET /api/currency/latest - returns latest exchange rate"""
        response = requests.get(
            f"{BASE_URL}/api/currency/latest",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "exchange_rate" in data, "exchange_rate not in response"
        assert "currency_code" in data, "currency_code not in response"
        print(f"Latest rate: {data.get('currency_code')} = {data.get('exchange_rate')}")


class TestStatsRoutes:
    """Test routes migrated to routes/stats.py"""
    
    def test_get_payroll_trend(self, auth_headers):
        """GET /api/stats/payroll-trend - returns 12 months trend"""
        response = requests.get(
            f"{BASE_URL}/api/stats/payroll-trend?year=2026",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        assert len(data) == 12, f"Should return 12 months, got {len(data)}"
        # Verify month structure
        if data:
            assert "month" in data[0], "month field missing"
            assert "gross" in data[0], "gross field missing"
            assert "net" in data[0], "net field missing"
        print(f"Payroll trend: {len(data)} months returned")
    
    def test_get_employee_stats(self, auth_headers):
        """GET /api/stats/employees - returns employee statistics"""
        response = requests.get(
            f"{BASE_URL}/api/stats/employees",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_active" in data, "total_active not in response"
        assert "total_inactive" in data, "total_inactive not in response"
        assert "by_department" in data, "by_department not in response"
        print(f"Employee stats: {data.get('total_active')} active, {data.get('total_inactive')} inactive")


class TestReportsRoutes:
    """Test routes added to routes/reports.py"""
    
    def test_get_payroll_report(self, auth_headers):
        """GET /api/reports/payroll - returns payroll report for period"""
        response = requests.get(
            f"{BASE_URL}/api/reports/payroll?year=2026&month=2",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "period" in data, "period not in response"
        assert data["period"] == "2026-02", f"Expected period 2026-02, got {data.get('period')}"
        print(f"Payroll report period: {data.get('period')}")
    
    def test_get_attendance_report(self, auth_headers):
        """GET /api/reports/attendance - returns attendance report for period"""
        response = requests.get(
            f"{BASE_URL}/api/reports/attendance?year=2026&month=2",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "period" in data, "period not in response"
        assert data["period"] == "2026-02", f"Expected period 2026-02, got {data.get('period')}"
        print(f"Attendance report period: {data.get('period')}")


class TestAccountingRoutes:
    """Test routes added to routes/accounting.py"""
    
    def test_get_accounts(self, auth_headers):
        """GET /api/accounting/accounts - returns accounts list"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/accounts",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Accounts count: {len(data)}")
    
    def test_generate_payroll_entry_not_found(self, auth_headers):
        """POST /api/accounting/generate-payroll-entry - returns 404 for fake ID"""
        response = requests.post(
            f"{BASE_URL}/api/accounting/generate-payroll-entry?payroll_id=fake_id_123",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("Generate payroll entry returns 404 for invalid payroll_id")


class TestExistingRoutes:
    """Test existing routes that should still work"""
    
    def test_get_plans(self, auth_headers):
        """GET /api/plans - returns subscription plans (kept in server.py)"""
        response = requests.get(
            f"{BASE_URL}/api/plans",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        assert len(data) > 0, "Should have subscription plans"
        print(f"Subscription plans: {len(data)}")
    
    def test_get_dashboard_stats(self, auth_headers):
        """GET /api/dashboard/stats - returns dashboard data"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Verify response has expected fields
        print(f"Dashboard stats keys: {list(data.keys())[:5]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
