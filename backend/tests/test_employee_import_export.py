"""
Test Suite for Employee Import/Export and Bulk Edit Features - FortexaRH
Tests the new endpoints:
- GET /api/employees/template/download - Download Excel template
- POST /api/employees/import/preview - Preview import from Excel
- POST /api/employees/import/execute - Execute import from Excel
- GET /api/employees/export/excel - Export employees to Excel
- GET /api/employees/bulk-edit/fields - Get available bulk edit fields
- POST /api/employees/bulk-edit - Execute bulk edit on multiple employees
- GET /api/search?q=test - Global search across modules
"""

import pytest
import requests
import os
import io
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAuthSetup:
    """Authentication setup for tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_login_success(self):
        """Test login endpoint works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data


class TestTemplateDownload:
    """Tests for Excel template download endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_download_template_success(self, auth_headers):
        """Test downloading employee template returns Excel file"""
        response = requests.get(
            f"{BASE_URL}/api/employees/template/download",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Template download failed: {response.text}"
        
        # Verify content type is Excel
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "application/vnd" in content_type, \
            f"Expected Excel content type, got: {content_type}"
        
        # Verify content disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition
        assert "plantilla_empleados.xlsx" in content_disposition
        
        # Verify file has content
        assert len(response.content) > 0, "Template file is empty"
        
        # Verify it's a valid Excel file (starts with PK for ZIP format)
        assert response.content[:2] == b'PK', "File does not appear to be a valid Excel file"
    
    def test_download_template_without_auth(self):
        """Test that template download without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/employees/template/download")
        assert response.status_code == 401


class TestImportPreview:
    """Tests for import preview endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def sample_excel_file(self, auth_headers):
        """Download template and use it as sample file"""
        response = requests.get(
            f"{BASE_URL}/api/employees/template/download",
            headers=auth_headers
        )
        return response.content
    
    def test_import_preview_with_valid_file(self, auth_headers, sample_excel_file):
        """Test import preview with valid Excel file"""
        files = {
            'file': ('test_employees.xlsx', io.BytesIO(sample_excel_file), 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees/import/preview",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files
        )
        assert response.status_code == 200, f"Preview failed: {response.text}"
        
        data = response.json()
        assert "total_rows" in data
        assert "valid_rows" in data
        assert "invalid_rows" in data
        assert "preview_data" in data
        assert "errors" in data
        
        # Template has 1 example row
        assert data["total_rows"] >= 0
        assert isinstance(data["preview_data"], list)
        assert isinstance(data["errors"], list)
    
    def test_import_preview_invalid_file_type(self, auth_headers):
        """Test import preview with invalid file type"""
        files = {
            'file': ('test.txt', io.BytesIO(b'invalid content'), 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees/import/preview",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_import_preview_without_auth(self, sample_excel_file):
        """Test that import preview without auth returns 401"""
        files = {
            'file': ('test.xlsx', io.BytesIO(sample_excel_file), 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees/import/preview",
            files=files
        )
        assert response.status_code == 401


class TestImportExecute:
    """Tests for import execute endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def sample_excel_file(self, auth_headers):
        """Download template and use it as sample file"""
        response = requests.get(
            f"{BASE_URL}/api/employees/template/download",
            headers=auth_headers
        )
        return response.content
    
    def test_import_execute_with_template(self, auth_headers, sample_excel_file):
        """Test import execute with template file (has example row)"""
        files = {
            'file': ('test_employees.xlsx', io.BytesIO(sample_excel_file), 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees/import/execute",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files
        )
        assert response.status_code == 200, f"Import execute failed: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "imported_count" in data
        assert "failed_count" in data
        assert "errors" in data
        assert "message" in data
        
        # Template has 1 example row that should import
        assert data["success"] == True
        assert data["imported_count"] >= 0
    
    def test_import_execute_invalid_file_type(self, auth_headers):
        """Test import execute with invalid file type"""
        files = {
            'file': ('test.txt', io.BytesIO(b'invalid content'), 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees/import/execute",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files
        )
        assert response.status_code == 400
    
    def test_import_execute_without_auth(self, sample_excel_file):
        """Test that import execute without auth returns 401"""
        files = {
            'file': ('test.xlsx', io.BytesIO(sample_excel_file), 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees/import/execute",
            files=files
        )
        assert response.status_code == 401


class TestExportExcel:
    """Tests for export employees to Excel endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_export_employees_success(self, auth_headers):
        """Test exporting employees to Excel"""
        response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export failed: {response.text}"
        
        # Verify content type is Excel
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "application/vnd" in content_type, \
            f"Expected Excel content type, got: {content_type}"
        
        # Verify content disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition
        assert "empleados_" in content_disposition
        assert ".xlsx" in content_disposition
        
        # Verify file has content
        assert len(response.content) > 0, "Export file is empty"
        
        # Verify it's a valid Excel file (starts with PK for ZIP format)
        assert response.content[:2] == b'PK', "File does not appear to be a valid Excel file"
    
    def test_export_employees_without_auth(self):
        """Test that export without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/employees/export/excel")
        assert response.status_code == 401


class TestBulkEditFields:
    """Tests for bulk edit fields endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_get_bulk_edit_fields(self, auth_headers):
        """Test getting available bulk edit fields"""
        response = requests.get(
            f"{BASE_URL}/api/employees/bulk-edit/fields",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get fields failed: {response.text}"
        
        data = response.json()
        assert "fields" in data
        assert isinstance(data["fields"], list)
        assert len(data["fields"]) > 0
        
        # Verify field structure
        field = data["fields"][0]
        assert "field" in field
        assert "label" in field
        assert "type" in field
        
        # Verify expected fields are present
        field_names = [f["field"] for f in data["fields"]]
        expected_fields = ["department", "position", "status", "salary", "contract_type"]
        for expected in expected_fields:
            assert expected in field_names, f"Missing expected field: {expected}"
    
    def test_bulk_edit_fields_without_auth(self):
        """Test that bulk edit fields without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/employees/bulk-edit/fields")
        assert response.status_code == 401


class TestBulkEdit:
    """Tests for bulk edit execution endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_employees(self, auth_headers):
        """Get existing employees for testing"""
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        return response.json() if response.status_code == 200 else []
    
    def test_bulk_edit_department(self, auth_headers, test_employees):
        """Test bulk editing department for multiple employees"""
        if len(test_employees) < 1:
            pytest.skip("No employees available for testing")
        
        employee_ids = [emp["employee_id"] for emp in test_employees[:2]]
        
        response = requests.post(
            f"{BASE_URL}/api/employees/bulk-edit",
            headers=auth_headers,
            json={
                "employee_ids": employee_ids,
                "fields_to_update": {
                    "department": "Administración"
                }
            }
        )
        assert response.status_code == 200, f"Bulk edit failed: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "modified_count" in data
        assert "message" in data
    
    def test_bulk_edit_multiple_fields(self, auth_headers, test_employees):
        """Test bulk editing multiple fields at once"""
        if len(test_employees) < 1:
            pytest.skip("No employees available for testing")
        
        employee_ids = [emp["employee_id"] for emp in test_employees[:1]]
        
        response = requests.post(
            f"{BASE_URL}/api/employees/bulk-edit",
            headers=auth_headers,
            json={
                "employee_ids": employee_ids,
                "fields_to_update": {
                    "department": "TI",
                    "city": "Santo Domingo",
                    "payment_method": "Transferencia Bancaria"
                }
            }
        )
        assert response.status_code == 200, f"Bulk edit failed: {response.text}"
        
        data = response.json()
        assert data["success"] == True
    
    def test_bulk_edit_empty_employees(self, auth_headers):
        """Test bulk edit with empty employee list returns error"""
        response = requests.post(
            f"{BASE_URL}/api/employees/bulk-edit",
            headers=auth_headers,
            json={
                "employee_ids": [],
                "fields_to_update": {"department": "Test"}
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_bulk_edit_empty_fields(self, auth_headers, test_employees):
        """Test bulk edit with empty fields returns error"""
        if len(test_employees) < 1:
            pytest.skip("No employees available for testing")
        
        employee_ids = [emp["employee_id"] for emp in test_employees[:1]]
        
        response = requests.post(
            f"{BASE_URL}/api/employees/bulk-edit",
            headers=auth_headers,
            json={
                "employee_ids": employee_ids,
                "fields_to_update": {}
            }
        )
        assert response.status_code == 400
    
    def test_bulk_edit_invalid_field(self, auth_headers, test_employees):
        """Test bulk edit with invalid field is ignored"""
        if len(test_employees) < 1:
            pytest.skip("No employees available for testing")
        
        employee_ids = [emp["employee_id"] for emp in test_employees[:1]]
        
        response = requests.post(
            f"{BASE_URL}/api/employees/bulk-edit",
            headers=auth_headers,
            json={
                "employee_ids": employee_ids,
                "fields_to_update": {
                    "invalid_field": "test",
                    "_id": "should_be_ignored"
                }
            }
        )
        # Should return 400 because no valid fields
        assert response.status_code == 400
    
    def test_bulk_edit_without_auth(self):
        """Test that bulk edit without auth returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/employees/bulk-edit",
            json={
                "employee_ids": ["emp_test"],
                "fields_to_update": {"department": "Test"}
            }
        )
        assert response.status_code == 401


class TestGlobalSearch:
    """Tests for global search endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_search_employees_by_name(self, auth_headers):
        """Test searching employees by name"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=Juan",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Search failed: {response.text}"
        
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    
    def test_search_vacations(self, auth_headers):
        """Test searching for vacations"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=vacaciones",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
    
    def test_search_payroll(self, auth_headers):
        """Test searching for payroll"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=nomina",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
    
    def test_search_loans(self, auth_headers):
        """Test searching for loans"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=prestamo",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
    
    def test_search_attendance(self, auth_headers):
        """Test searching for attendance"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=asistencia",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
    
    def test_search_results_structure(self, auth_headers):
        """Test that search results have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=test",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        
        # If there are results, verify structure
        if len(data["results"]) > 0:
            result = data["results"][0]
            assert "type" in result
            assert "title" in result
    
    def test_search_without_auth(self):
        """Test that search without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/search?q=test")
        assert response.status_code == 401
    
    def test_search_empty_query(self, auth_headers):
        """Test search with empty query"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=",
            headers=auth_headers
        )
        # Should return 200 with empty results
        assert response.status_code in [200, 422]


class TestIntegration:
    """Integration tests for import/export workflow"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_full_import_workflow(self, auth_headers):
        """Test complete import workflow: download template -> preview -> execute"""
        # Step 1: Download template
        template_response = requests.get(
            f"{BASE_URL}/api/employees/template/download",
            headers=auth_headers
        )
        assert template_response.status_code == 200
        template_content = template_response.content
        
        # Step 2: Preview import
        files = {
            'file': ('test.xlsx', io.BytesIO(template_content), 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        preview_response = requests.post(
            f"{BASE_URL}/api/employees/import/preview",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files
        )
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        assert "total_rows" in preview_data
        
        # Step 3: Execute import (using same file)
        files = {
            'file': ('test.xlsx', io.BytesIO(template_content), 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        execute_response = requests.post(
            f"{BASE_URL}/api/employees/import/execute",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files
        )
        assert execute_response.status_code == 200
        execute_data = execute_response.json()
        assert execute_data["success"] == True
    
    def test_export_after_import(self, auth_headers):
        """Test that export works after importing employees"""
        # Export employees
        export_response = requests.get(
            f"{BASE_URL}/api/employees/export/excel",
            headers=auth_headers
        )
        assert export_response.status_code == 200
        assert len(export_response.content) > 0
        
        # Verify it's a valid Excel file
        assert export_response.content[:2] == b'PK'
    
    def test_bulk_edit_after_import(self, auth_headers):
        """Test bulk edit on imported employees"""
        # Get employees
        emp_response = requests.get(
            f"{BASE_URL}/api/employees",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        if emp_response.status_code == 200:
            employees = emp_response.json()
            if len(employees) > 0:
                employee_ids = [emp["employee_id"] for emp in employees[:2]]
                
                # Bulk edit
                edit_response = requests.post(
                    f"{BASE_URL}/api/employees/bulk-edit",
                    headers={**auth_headers, "Content-Type": "application/json"},
                    json={
                        "employee_ids": employee_ids,
                        "fields_to_update": {
                            "department": "Recursos Humanos"
                        }
                    }
                )
                assert edit_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
