"""
Test Payroll Export Excel and Company Name Bug Fixes
Tests:
1. GET /api/payroll-v2/periods/{period_id}/export/excel - returns JSON with company_name
2. GET /api/auth/me - includes company_name in response
3. GET /api/company/settings - returns company name
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"
TEST_PERIOD_ID = "period_02989e9e3331"  # Nómina Mensual Enero 2026


class TestPayrollExportAndCompanyName:
    """Tests for payroll export Excel and company name bug fixes"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in login response"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    # ==================== AUTH/ME TESTS ====================
    
    def test_auth_me_returns_company_name(self, auth_headers):
        """Test GET /api/auth/me includes company_name"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        data = response.json()
        
        # Verify company_name is present
        assert "company_name" in data, "company_name not in /auth/me response"
        print(f"✓ /auth/me returns company_name: {data.get('company_name')}")
        
        # Verify it's not the default placeholder
        company_name = data.get("company_name")
        assert company_name is not None, "company_name is None"
        assert company_name != "NOMBRE DE LA EMPRESA", f"company_name is still placeholder: {company_name}"
        print(f"✓ company_name is not placeholder: {company_name}")
    
    # ==================== COMPANY SETTINGS TESTS ====================
    
    def test_company_settings_returns_name(self, auth_headers):
        """Test GET /api/company/settings returns company name"""
        response = requests.get(
            f"{BASE_URL}/api/company/settings",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Company settings failed: {response.text}"
        data = response.json()
        
        # Verify company object exists with name
        assert "company" in data, "company not in settings response"
        company = data.get("company", {})
        assert "name" in company, "name not in company object"
        
        company_name = company.get("name")
        print(f"✓ /company/settings returns company name: {company_name}")
        
        # Verify it's not empty
        assert company_name, "company name is empty"
        print(f"✓ company name is not empty: {company_name}")
    
    # ==================== PAYROLL EXPORT EXCEL TESTS ====================
    
    def test_payroll_export_excel_returns_json(self, auth_headers):
        """Test GET /api/payroll-v2/periods/{period_id}/export/excel returns JSON"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods/{TEST_PERIOD_ID}/export/excel",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export excel failed: {response.text}"
        
        # Verify response is JSON
        try:
            data = response.json()
        except Exception as e:
            pytest.fail(f"Response is not JSON: {e}")
        
        print(f"✓ /export/excel returns JSON response")
        
        # Verify required fields
        required_fields = ["company_name", "period", "columns", "rows", "totals"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        print(f"✓ All required fields present: {required_fields}")
    
    def test_payroll_export_excel_has_company_name(self, auth_headers):
        """Test export/excel response includes company_name"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods/{TEST_PERIOD_ID}/export/excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify company_name
        assert "company_name" in data, "company_name not in export response"
        company_name = data.get("company_name")
        assert company_name, "company_name is empty"
        assert company_name != "Sin Nombre", f"company_name is default: {company_name}"
        print(f"✓ Export includes company_name: {company_name}")
    
    def test_payroll_export_excel_has_period_info(self, auth_headers):
        """Test export/excel response includes period information"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods/{TEST_PERIOD_ID}/export/excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify period object
        assert "period" in data, "period not in export response"
        period = data.get("period", {})
        
        period_fields = ["period_id", "description", "start_date", "end_date"]
        for field in period_fields:
            assert field in period, f"Missing period field: {field}"
        
        print(f"✓ Period info: {period.get('description')}")
        print(f"✓ Period dates: {period.get('start_date')} - {period.get('end_date')}")
    
    def test_payroll_export_excel_has_columns_and_rows(self, auth_headers):
        """Test export/excel response includes columns and rows"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods/{TEST_PERIOD_ID}/export/excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify columns
        assert "columns" in data, "columns not in export response"
        columns = data.get("columns", [])
        assert len(columns) > 0, "columns is empty"
        print(f"✓ Columns count: {len(columns)}")
        
        # Verify rows
        assert "rows" in data, "rows not in export response"
        rows = data.get("rows", [])
        print(f"✓ Rows count: {len(rows)}")
        
        # Verify totals
        assert "totals" in data, "totals not in export response"
        totals = data.get("totals", {})
        assert "neto" in totals, "neto not in totals"
        print(f"✓ Total neto: {totals.get('neto')}")
    
    def test_payroll_export_excel_row_structure(self, auth_headers):
        """Test export/excel rows have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods/{TEST_PERIOD_ID}/export/excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        rows = data.get("rows", [])
        if len(rows) > 0:
            first_row = rows[0]
            expected_fields = ["no", "cedula", "nombre", "salario_base", "total_ingresos", 
                            "sfs", "afp", "isr", "total_descuentos", "neto"]
            for field in expected_fields:
                assert field in first_row, f"Missing row field: {field}"
            print(f"✓ Row structure verified with fields: {list(first_row.keys())}")
        else:
            print("⚠ No rows in export (period may be empty)")
    
    # ==================== PAYROLL PERIODS LIST TEST ====================
    
    def test_payroll_periods_list(self, auth_headers):
        """Test GET /api/payroll-v2/periods returns list"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Periods list failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response is not a list"
        print(f"✓ Found {len(data)} payroll periods")
        
        # Find our test period
        test_period = next((p for p in data if p.get("period_id") == TEST_PERIOD_ID), None)
        if test_period:
            print(f"✓ Test period found: {test_period.get('description')}")
            print(f"  Status: {test_period.get('status')}")
            print(f"  Employees: {test_period.get('employee_count')}")
        else:
            print(f"⚠ Test period {TEST_PERIOD_ID} not found in list")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
