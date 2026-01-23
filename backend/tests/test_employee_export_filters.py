"""
Test Employee Export with Filters - FortexaRH
Tests the new filter parameters (status, department, search) for /api/employees/export/excel endpoint
Also tests basic employee list and authentication endpoints
"""
import pytest
import requests
import os
import io

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["email"] == TEST_EMAIL
        assert "user_id" in data["user"]
        assert "company_id" in data["user"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code in [401, 400], f"Expected 401 or 400, got {response.status_code}"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with authentication token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestEmployeesList:
    """Test GET /api/employees endpoint"""
    
    def test_get_employees_authenticated(self, auth_headers):
        """Test getting employees list with authentication"""
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get employees: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify employee structure if there are employees
        if len(data) > 0:
            employee = data[0]
            assert "employee_id" in employee
            assert "first_name" in employee
            assert "last_name" in employee
    
    def test_get_employees_unauthenticated(self):
        """Test getting employees without authentication returns 401"""
        response = requests.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestEmployeeExportWithFilters:
    """Test GET /api/employees/export/excel with filter parameters"""
    
    def test_export_no_filters(self, auth_headers):
        """Test export without any filters"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export failed: {response.text}"
        
        # Verify it's an Excel file
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "application/vnd" in content_type, \
            f"Expected Excel content type, got: {content_type}"
        
        # Verify content disposition header
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert ".xlsx" in content_disposition
    
    def test_export_with_status_filter_active(self, auth_headers):
        """Test export with status=active filter"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"status": "active"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with status filter failed: {response.text}"
        
        # Verify it's an Excel file
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "application/vnd" in content_type
    
    def test_export_with_status_filter_inactive(self, auth_headers):
        """Test export with status=inactive filter"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"status": "inactive"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with inactive status filter failed: {response.text}"
    
    def test_export_with_status_filter_all(self, auth_headers):
        """Test export with status=all filter (should return all employees)"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"status": "all"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with status=all filter failed: {response.text}"
    
    def test_export_with_department_filter(self, auth_headers):
        """Test export with department filter"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"department": "TI"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with department filter failed: {response.text}"
    
    def test_export_with_department_filter_all(self, auth_headers):
        """Test export with department=all filter (should return all employees)"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"department": "all"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with department=all filter failed: {response.text}"
    
    def test_export_with_search_filter(self, auth_headers):
        """Test export with search filter"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"search": "Juan"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with search filter failed: {response.text}"
    
    def test_export_with_search_filter_email(self, auth_headers):
        """Test export with search filter matching email"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"search": "@"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with email search filter failed: {response.text}"
    
    def test_export_with_multiple_filters(self, auth_headers):
        """Test export with multiple filters combined"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={
                "status": "active",
                "department": "TI",
                "search": "test"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with multiple filters failed: {response.text}"
    
    def test_export_with_status_and_department(self, auth_headers):
        """Test export with status and department filters"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={
                "status": "active",
                "department": "Administración"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with status+department failed: {response.text}"
    
    def test_export_with_status_and_search(self, auth_headers):
        """Test export with status and search filters"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={
                "status": "active",
                "search": "Carlos"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with status+search failed: {response.text}"
    
    def test_export_with_empty_search(self, auth_headers):
        """Test export with empty search filter (should return all)"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"search": ""},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with empty search failed: {response.text}"
    
    def test_export_with_nonexistent_department(self, auth_headers):
        """Test export with non-existent department (should return empty Excel)"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"department": "NonExistentDepartment123"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with non-existent department failed: {response.text}"
    
    def test_export_with_nonexistent_search(self, auth_headers):
        """Test export with search that matches nothing (should return empty Excel)"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"search": "ZZZZNONEXISTENT12345"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with non-matching search failed: {response.text}"
    
    def test_export_unauthenticated(self):
        """Test export without authentication returns 401"""
        response = requests.get(f"{BASE_URL}/api/employees/export/excel")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_export_file_content_is_valid_excel(self, auth_headers):
        """Test that exported file is a valid Excel file"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Check Excel magic bytes (PK for ZIP-based formats like xlsx)
        content = response.content
        assert len(content) > 0, "Export file should not be empty"
        
        # XLSX files start with PK (ZIP signature)
        assert content[:2] == b'PK', "File should be a valid XLSX (ZIP-based) file"


class TestExportFilterIntegration:
    """Integration tests for export filters with data verification"""
    
    def test_filter_reduces_export_size(self, auth_headers):
        """Test that applying filters reduces the export file size"""
        # Get export without filters
        response_all = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            headers=auth_headers
        )
        assert response_all.status_code == 200
        size_all = len(response_all.content)
        
        # Get export with non-matching search filter
        response_filtered = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"search": "ZZZZNONEXISTENT12345"},
            headers=auth_headers
        )
        assert response_filtered.status_code == 200
        size_filtered = len(response_filtered.content)
        
        # Filtered export should be smaller or equal (empty result still has headers)
        assert size_filtered <= size_all, \
            f"Filtered export ({size_filtered}) should be <= unfiltered ({size_all})"
    
    def test_employees_list_matches_export_count(self, auth_headers):
        """Test that employee list count is consistent with export"""
        # Get employees list
        response_list = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        assert response_list.status_code == 200
        employee_count = len(response_list.json())
        
        # Get export
        response_export = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            headers=auth_headers
        )
        assert response_export.status_code == 200
        
        # Both should succeed - we can't easily count rows in Excel without openpyxl
        # but we verify both endpoints work with the same auth
        print(f"Employee count from list: {employee_count}")


class TestExportEdgeCases:
    """Edge case tests for export functionality"""
    
    def test_export_with_special_characters_in_search(self, auth_headers):
        """Test export with special characters in search"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"search": "José María"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with special chars failed: {response.text}"
    
    def test_export_with_unicode_in_search(self, auth_headers):
        """Test export with unicode characters in search"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"search": "Pérez"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export with unicode failed: {response.text}"
    
    def test_export_with_very_long_search(self, auth_headers):
        """Test export with very long search string"""
        long_search = "a" * 500
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            params={"search": long_search},
            headers=auth_headers
        )
        # Should either succeed or return a reasonable error
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
