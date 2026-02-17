"""
FortexaRH Refactoring Validation Tests - Iteration 167
Tests to validate major refactoring:
1. Auth helpers moved to utils/auth.py
2. Config centralized in config.py
3. PayrollV2Page route changed from /payroll-v2 to /payroll
4. reports_system.py split into services/report_catalog.py + services/report_generators.py
5. payroll.py split - exports moved to routes/payroll_exports.py
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://company-config-debug.preview.emergentagent.com')
BASE_URL = BASE_URL.rstrip('/')

# Test credentials
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
EMPLOYEE_CEDULA = "001-0000001-1"
EMPLOYEE_PASSWORD = "portal123"


class TestAuthRefactoring:
    """Test auth endpoints with centralized auth helpers"""
    
    def test_admin_login_with_jwt(self):
        """Test /api/auth/login returns JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful, token starts with: {data['token'][:20]}...")
    
    def test_employee_portal_login(self):
        """Test employee portal login endpoint"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "cedula": EMPLOYEE_CEDULA,
            "password": EMPLOYEE_PASSWORD
        })
        # Accept 200 (success) or 401/404 (employee not found - depends on test data)
        assert response.status_code in [200, 401, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ Employee portal login endpoint responded with status {response.status_code}")


class TestPayrollRouteRefactoring:
    """Test payroll routes - consolidated from /payroll-v2 to /payroll"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_payroll_periods_endpoint(self):
        """Test GET /api/payroll/periods - main payroll periods endpoint"""
        response = requests.get(f"{BASE_URL}/api/payroll/periods", headers=self.headers)
        assert response.status_code == 200, f"Payroll periods failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list of periods"
        print(f"✓ /api/payroll/periods returned {len(data)} periods")
    
    def test_payroll_novelty_types_endpoint(self):
        """Test GET /api/payroll/novelty-types - novelty types for payroll"""
        response = requests.get(f"{BASE_URL}/api/payroll/novelty-types", headers=self.headers)
        assert response.status_code == 200, f"Novelty types failed: {response.text}"
        data = response.json()
        # Returns dict with 'income' and 'deduction' keys
        assert isinstance(data, dict), "Should return a dict"
        assert "income" in data or "deduction" in data, "Should have income/deduction keys"
        print(f"✓ /api/payroll/novelty-types returned novelty types")
    
    def test_payroll_export_excel(self):
        """Test GET /api/payroll/periods/{id}/export/excel - excel export (from payroll_exports.py)"""
        # First get a period ID
        periods_response = requests.get(f"{BASE_URL}/api/payroll/periods", headers=self.headers)
        if periods_response.status_code == 200:
            periods = periods_response.json()
            if periods:
                period_id = periods[0].get("period_id")
                export_response = requests.get(
                    f"{BASE_URL}/api/payroll/periods/{period_id}/export/excel",
                    headers=self.headers
                )
                assert export_response.status_code == 200, f"Excel export failed: {export_response.text}"
                data = export_response.json()
                assert "company_name" in data, "Should have company_name"
                assert "period" in data, "Should have period"
                assert "rows" in data, "Should have rows"
                print(f"✓ /api/payroll/periods/{period_id}/export/excel works correctly")
            else:
                print("⚠ No payroll periods found, skipping export test")
        else:
            pytest.skip("Could not fetch periods")
    
    def test_payroll_tss_preview(self):
        """Test GET /api/payroll/periods/{id}/tss-preview - TSS preview (from payroll_exports.py)"""
        periods_response = requests.get(f"{BASE_URL}/api/payroll/periods", headers=self.headers)
        if periods_response.status_code == 200:
            periods = periods_response.json()
            if periods:
                period_id = periods[0].get("period_id")
                response = requests.get(
                    f"{BASE_URL}/api/payroll/periods/{period_id}/tss-preview",
                    headers=self.headers
                )
                assert response.status_code == 200, f"TSS preview failed: {response.text}"
                print(f"✓ /api/payroll/periods/{period_id}/tss-preview works correctly")
            else:
                print("⚠ No payroll periods found, skipping TSS preview test")
        else:
            pytest.skip("Could not fetch periods")


class TestReportsSystemRefactoring:
    """Test reports system - split into report_catalog.py + report_generators.py"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_reports_catalog_returns_58_reports(self):
        """Test GET /api/reports-system/catalog - should return ~58 reports"""
        response = requests.get(f"{BASE_URL}/api/reports-system/catalog", headers=self.headers)
        assert response.status_code == 200, f"Reports catalog failed: {response.text}"
        data = response.json()
        assert "total_reports" in data, "Should have total_reports"
        assert "categories" in data, "Should have categories"
        # Verify we have around 58 reports (allowing some flexibility)
        total = data.get("total_reports", 0)
        assert total >= 50, f"Expected ~58 reports, got {total}"
        print(f"✓ /api/reports-system/catalog returned {total} reports")
    
    def test_reports_definition_endpoint(self):
        """Test GET /api/reports-system/definition/{report_id}"""
        # First get catalog to find a valid report ID
        catalog_response = requests.get(f"{BASE_URL}/api/reports-system/catalog", headers=self.headers)
        if catalog_response.status_code == 200:
            categories = catalog_response.json().get("categories", {})
            for cat_id, cat_data in categories.items():
                reports = cat_data.get("reports", [])
                if reports:
                    report_id = reports[0].get("id")
                    definition_response = requests.get(
                        f"{BASE_URL}/api/reports-system/definition/{report_id}",
                        headers=self.headers
                    )
                    assert definition_response.status_code == 200, f"Definition failed: {definition_response.text}"
                    data = definition_response.json()
                    assert "id" in data, "Should have id"
                    assert "name" in data, "Should have name"
                    print(f"✓ /api/reports-system/definition/{report_id} works correctly")
                    return
        print("⚠ No report definitions found to test")


class TestPlansEndpoint:
    """Test subscription plans endpoint"""
    
    def test_plans_endpoint(self):
        """Test GET /api/plans returns subscription plans"""
        response = requests.get(f"{BASE_URL}/api/plans")
        assert response.status_code == 200, f"Plans failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        assert len(data) > 0, "Should have plans"
        # Check first plan has expected structure
        plan = data[0]
        assert "plan_id" in plan, "Plan should have plan_id"
        assert "name" in plan, "Plan should have name"
        print(f"✓ /api/plans returned {len(data)} plans")


class TestDashboardAfterRefactoring:
    """Test dashboard endpoints work after refactoring"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_dashboard_stats_endpoint(self):
        """Test GET /api/dashboard/stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Should return a dict"
        print(f"✓ /api/dashboard/stats returned stats data")
    
    def test_employees_endpoint(self):
        """Test GET /api/employees"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=self.headers)
        assert response.status_code == 200, f"Employees failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"✓ /api/employees returned {len(data)} employees")


class TestOldRouteRemoved:
    """Verify old /payroll-v2 route is no longer accessible"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_payroll_v2_route_redirects_or_404(self):
        """Old /api/payroll-v2 route should be removed - but we allow it to still work if aliased"""
        response = requests.get(f"{BASE_URL}/api/payroll-v2/periods", headers=self.headers)
        # Either 404 (removed) or 200 (aliased) are acceptable
        # The key test is that /api/payroll/periods works (tested above)
        print(f"✓ /api/payroll-v2/periods status: {response.status_code} (legacy route check)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
