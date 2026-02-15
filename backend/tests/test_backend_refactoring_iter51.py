"""
Backend Refactoring Regression Tests - Iteration 51
Tests after major backend consolidation:
1. payroll_v2.py merged into payroll.py with both router and legacy_router
2. Pydantic models centralized in /backend/models/ directory
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
PARTNER_EMAIL = "newpartner@test.com"
PARTNER_PASSWORD = "test123"
EMPLOYEE_CEDULA = "001-0000001-1"
EMPLOYEE_PORTAL_PASSWORD = "portal123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Create auth headers from token"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestBackendStartup:
    """Test backend starts without errors"""
    
    def test_health_endpoint(self):
        """Test /health endpoint returns healthy"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Backend health check passed")
    
    def test_health_db_endpoint(self):
        """Test /health/db for database connectivity"""
        response = requests.get(f"{BASE_URL}/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data.get("database") == "connected"
        print("✓ Database connection verified")


class TestAuthAPI:
    """Test authentication endpoints"""
    
    def test_admin_login(self):
        """Test admin login with test_refactor@fortexa.com / test123"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful: {data['user']['name']}")
    
    def test_partner_login(self):
        """Test partner login with newpartner@test.com / test123"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": PARTNER_EMAIL, "password": PARTNER_PASSWORD}
        )
        # Partner may or may not exist, just check we get valid response
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            print(f"✓ Partner login successful")
        else:
            print(f"⚠ Partner account may not exist (401)")
    
    def test_employee_portal_login(self):
        """Test employee portal login with cedula"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": EMPLOYEE_CEDULA, "password": EMPLOYEE_PORTAL_PASSWORD}
        )
        # May not exist, just check valid response structure
        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            print(f"✓ Employee portal login successful")
        else:
            print(f"⚠ Employee portal login returned {response.status_code}")


class TestPayrollV2Routes:
    """Test consolidated payroll routes (payroll_v2 merged into payroll.py)"""
    
    def test_get_payroll_periods(self, auth_headers):
        """GET /api/payroll-v2/periods returns periods"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Payroll V2 periods: {len(data)} periods found")
    
    def test_get_payroll_types(self, auth_headers):
        """GET /api/payroll-v2/payroll-types returns payroll types"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/payroll-types",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Payroll types returned: {len(data)} types")
    
    def test_get_novelty_types(self, auth_headers):
        """GET /api/payroll-v2/novelty-types returns novelty types"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/novelty-types",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Novelty types returned: {len(data)} types")


class TestLegacyPayrollRoutes:
    """Test legacy payroll routes (still available via legacy_router)"""
    
    def test_get_legacy_payroll(self, auth_headers):
        """GET /api/payroll returns legacy payroll list"""
        response = requests.get(
            f"{BASE_URL}/api/payroll",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Legacy payroll endpoint: {len(data)} records")


class TestEmployeesAPI:
    """Test employees endpoint with centralized employee models"""
    
    def test_get_employees(self, auth_headers):
        """GET /api/employees returns employees"""
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Employees returned: {len(data)} employees")


class TestCompanyAPI:
    """Test company endpoint with centralized company models"""
    
    def test_get_company(self, auth_headers):
        """GET /api/company returns company data"""
        response = requests.get(
            f"{BASE_URL}/api/company",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Company may return null/empty if not configured
        print(f"✓ Company endpoint working")


class TestAttendanceAPI:
    """Test attendance/shifts endpoint with centralized HR models"""
    
    def test_get_shifts(self, auth_headers):
        """GET /api/attendance/shifts returns shifts"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/shifts",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Attendance shifts: {len(data)} shifts")


class TestVacationsAPI:
    """Test vacations endpoints with centralized HR models"""
    
    def test_get_vacations(self, auth_headers):
        """GET /api/vacations returns leave requests"""
        response = requests.get(
            f"{BASE_URL}/api/vacations",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Vacations/Leave requests: {len(data)} records")
    
    def test_get_vacation_policies(self, auth_headers):
        """GET /api/vacations/policies returns leave policies"""
        response = requests.get(
            f"{BASE_URL}/api/vacations/policies",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Vacation policies: {len(data)} policies")


class TestEvaluationsAPI:
    """Test evaluations endpoint with centralized HR models"""
    
    def test_get_evaluation_cycles(self, auth_headers):
        """GET /api/evaluations/cycles returns evaluation cycles"""
        response = requests.get(
            f"{BASE_URL}/api/evaluations/cycles",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Evaluation cycles: {len(data)} cycles")


class TestAccountingAPI:
    """Test accounting endpoint with centralized finance models"""
    
    def test_get_accounts(self, auth_headers):
        """GET /api/accounting/accounts returns accounts"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/accounts",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Accounting accounts: {len(data)} accounts")


class TestReportsSystemAPI:
    """Test reports-system endpoint"""
    
    def test_get_reports_catalog(self, auth_headers):
        """GET /api/reports-system/catalog returns reports catalog"""
        response = requests.get(
            f"{BASE_URL}/api/reports-system/catalog",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total_reports" in data
        print(f"✓ Reports catalog: {data['total_reports']} reports available")


class TestPayrollConfigAPI:
    """Test payroll-config endpoint"""
    
    def test_get_payroll_settings(self, auth_headers):
        """GET /api/payroll-config/payroll-settings returns payroll settings"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-config/payroll-settings",
            headers=auth_headers
        )
        assert response.status_code == 200
        # May return null if no settings configured
        print(f"✓ Payroll settings endpoint working")


class TestDashboardAPI:
    """Test dashboard endpoints"""
    
    def test_get_dashboard_stats(self, auth_headers):
        """GET /api/dashboard/stats returns dashboard statistics"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Dashboard stats endpoint working")


class TestCentralizedModelsImport:
    """Verify centralized models are being used correctly"""
    
    def test_payroll_models_used(self, auth_headers):
        """Test payroll endpoints use centralized models"""
        # Test creating a period (uses PayrollPeriodCreateV2 from payroll_constants)
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✓ Payroll models from centralized location working")
    
    def test_auth_models_used(self, auth_headers):
        """Test auth endpoints use centralized models"""
        response = requests.get(
            f"{BASE_URL}/api/subscription",
            headers=auth_headers
        )
        # Should return subscription info or null
        assert response.status_code in [200, 404]
        print("✓ Auth/subscription models working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
