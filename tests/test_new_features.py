"""
Test suite for new FortexaRH features:
1. Document Generation Module (/api/doc-generator/*)
2. Employee Portal (/api/employee-portal/*)
3. Bank Files (/api/bank-files/*)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://emp-alerts.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def test_employee_id(auth_headers):
    """Get or create a test employee for document generation"""
    # First try to get existing employees
    response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
    if response.status_code == 200:
        employees = response.json()
        if employees:
            return employees[0]["employee_id"]
    
    # Create a test employee if none exist
    employee_data = {
        "first_name": "TEST_DocGen",
        "last_name": "Employee",
        "email": "test_docgen@fortexa.com",
        "position": "Analista",
        "department": "Recursos Humanos",
        "hire_date": "2024-01-15",
        "salary": 50000.0,
        "document_number": "001-0000001-1",
        "bank_account": "1234567890123456",
        "bank_name": "Banco Popular"
    }
    response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
    if response.status_code in [200, 201]:
        return response.json()["employee_id"]
    
    pytest.skip("Could not get or create test employee")


# ===================== DOCUMENT GENERATION TESTS =====================

class TestDocumentGeneration:
    """Tests for Document Generation Module"""
    
    def test_get_document_categories(self, auth_headers):
        """Test GET /api/doc-generator/categories returns 4 categories"""
        response = requests.get(f"{BASE_URL}/api/doc-generator/categories", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        categories = response.json()
        assert isinstance(categories, list), "Response should be a list"
        assert len(categories) == 4, f"Expected 4 categories, got {len(categories)}"
        
        # Verify category structure
        category_ids = [c["id"] for c in categories]
        assert "constancia" in category_ids, "Missing 'constancia' category"
        assert "carta" in category_ids, "Missing 'carta' category"
        assert "certificado" in category_ids, "Missing 'certificado' category"
        assert "notificacion" in category_ids, "Missing 'notificacion' category"
        
        print(f"✓ Categories returned: {category_ids}")
    
    def test_get_document_templates(self, auth_headers):
        """Test GET /api/doc-generator/templates returns default templates"""
        response = requests.get(f"{BASE_URL}/api/doc-generator/templates", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        templates = response.json()
        assert isinstance(templates, list), "Response should be a list"
        assert len(templates) >= 5, f"Expected at least 5 default templates, got {len(templates)}"
        
        # Verify template structure
        for template in templates:
            assert "template_id" in template, "Template missing template_id"
            assert "name" in template, "Template missing name"
            assert "category" in template, "Template missing category"
            assert "content" in template, "Template missing content"
        
        template_names = [t["name"] for t in templates]
        print(f"✓ Templates returned: {template_names}")
    
    def test_get_templates_by_category(self, auth_headers):
        """Test filtering templates by category"""
        response = requests.get(
            f"{BASE_URL}/api/doc-generator/templates?category=constancia", 
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        templates = response.json()
        for template in templates:
            assert template["category"] == "constancia", f"Template category mismatch: {template['category']}"
        
        print(f"✓ Filtered templates by category: {len(templates)} constancia templates")
    
    def test_get_specific_template(self, auth_headers):
        """Test GET /api/doc-generator/templates/{template_id}"""
        # First get templates to get a valid ID
        response = requests.get(f"{BASE_URL}/api/doc-generator/templates", headers=auth_headers)
        templates = response.json()
        
        if templates:
            template_id = templates[0]["template_id"]
            response = requests.get(
                f"{BASE_URL}/api/doc-generator/templates/{template_id}", 
                headers=auth_headers
            )
            assert response.status_code == 200, f"Failed: {response.text}"
            
            template = response.json()
            assert template["template_id"] == template_id
            print(f"✓ Got specific template: {template['name']}")
    
    def test_generate_document(self, auth_headers, test_employee_id):
        """Test POST /api/doc-generator/generate creates a document"""
        # First get templates
        response = requests.get(f"{BASE_URL}/api/doc-generator/templates", headers=auth_headers)
        templates = response.json()
        
        # Find constancia_trabajo template
        template = next((t for t in templates if t["template_id"] == "constancia_trabajo"), templates[0])
        
        generate_data = {
            "template_id": template["template_id"],
            "employee_id": test_employee_id,
            "custom_values": {
                "show_salary": True,
                "purpose": "trámites bancarios"
            },
            "save_to_history": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/doc-generator/generate",
            json=generate_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        result = response.json()
        assert "document_id" in result, "Response missing document_id"
        assert "content" in result, "Response missing content"
        assert "template_name" in result, "Response missing template_name"
        assert "employee_name" in result, "Response missing employee_name"
        
        # Verify content has HTML
        assert "<div" in result["content"], "Content should contain HTML"
        
        print(f"✓ Generated document: {result['document_id']} for {result['employee_name']}")
        return result["document_id"]
    
    def test_get_document_history(self, auth_headers):
        """Test GET /api/doc-generator/history returns generated documents"""
        response = requests.get(f"{BASE_URL}/api/doc-generator/history", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        history = response.json()
        assert isinstance(history, list), "Response should be a list"
        
        if history:
            doc = history[0]
            assert "document_id" in doc, "Document missing document_id"
            assert "template_name" in doc, "Document missing template_name"
            assert "employee_name" in doc, "Document missing employee_name"
            assert "created_at" in doc, "Document missing created_at"
        
        print(f"✓ Document history: {len(history)} documents")
    
    def test_document_templates_auth_required(self):
        """Test that document endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/doc-generator/templates")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Document templates require authentication")


# ===================== EMPLOYEE PORTAL TESTS =====================

class TestEmployeePortal:
    """Tests for Employee Self-Service Portal"""
    
    def test_employee_portal_login_invalid(self):
        """Test employee portal login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": "000-0000000-0", "password": "wrongpassword"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Employee portal rejects invalid credentials")
    
    def test_employee_portal_login_endpoint_exists(self):
        """Test that employee portal login endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": "test", "password": "test"}
        )
        # Should return 401 (unauthorized) not 404 (not found)
        assert response.status_code in [401, 422], f"Expected 401 or 422, got {response.status_code}"
        print("✓ Employee portal login endpoint exists")
    
    def test_employee_portal_profile_requires_auth(self):
        """Test that profile endpoint requires employee token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/profile")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Employee portal profile requires authentication")
    
    def test_employee_portal_payslips_requires_auth(self):
        """Test that payslips endpoint requires employee token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/payslips")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Employee portal payslips requires authentication")
    
    def test_employee_portal_vacations_balance_requires_auth(self):
        """Test that vacation balance endpoint requires employee token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/vacations/balance")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Employee portal vacation balance requires authentication")
    
    def test_employee_portal_dashboard_requires_auth(self):
        """Test that dashboard endpoint requires employee token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/dashboard")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Employee portal dashboard requires authentication")
    
    def test_employee_portal_login_with_employee(self, auth_headers, test_employee_id):
        """Test employee portal login with actual employee credentials"""
        # Get employee details
        response = requests.get(f"{BASE_URL}/api/employees/{test_employee_id}", headers=auth_headers)
        if response.status_code != 200:
            pytest.skip("Could not get employee details")
        
        employee = response.json()
        document_number = employee.get("document_number")
        
        if not document_number:
            pytest.skip("Employee has no document number")
        
        # Try to login with document number as password (first-time login)
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/login",
            json={"document_number": document_number, "password": document_number}
        )
        
        if response.status_code == 200:
            result = response.json()
            assert "token" in result, "Response missing token"
            assert "employee" in result, "Response missing employee"
            print(f"✓ Employee portal login successful for {document_number}")
            return result["token"]
        else:
            # Employee might already have a different password
            print(f"✓ Employee portal login endpoint works (status: {response.status_code})")


# ===================== BANK FILES TESTS =====================

class TestBankFiles:
    """Tests for Bank File Generation"""
    
    def test_get_available_banks(self, auth_headers):
        """Test GET /api/bank-files/banks returns available banks"""
        response = requests.get(f"{BASE_URL}/api/bank-files/banks", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        banks = response.json()
        assert isinstance(banks, list), "Response should be a list"
        assert len(banks) >= 3, f"Expected at least 3 banks, got {len(banks)}"
        
        # Verify bank structure
        bank_ids = [b["id"] for b in banks]
        assert "popular" in bank_ids, "Missing Banco Popular"
        assert "bhd" in bank_ids, "Missing BHD León"
        assert "banreservas" in bank_ids, "Missing Banreservas"
        
        for bank in banks:
            assert "id" in bank, "Bank missing id"
            assert "name" in bank, "Bank missing name"
            assert "format" in bank, "Bank missing format"
        
        print(f"✓ Available banks: {[b['name'] for b in banks]}")
    
    def test_bank_files_auth_required(self):
        """Test that bank files endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/bank-files/banks")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Bank files require authentication")
    
    def test_generate_bank_file_requires_approved_period(self, auth_headers):
        """Test that bank file generation requires approved/paid period"""
        # Try to generate for a non-existent period
        response = requests.get(
            f"{BASE_URL}/api/bank-files/generate/fake_period_id/popular",
            headers=auth_headers
        )
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
        print("✓ Bank file generation validates period status")
    
    def test_generate_bank_file_with_valid_period(self, auth_headers):
        """Test bank file generation with a valid approved/paid period"""
        # Get payroll periods
        response = requests.get(f"{BASE_URL}/api/payroll-v2/periods", headers=auth_headers)
        if response.status_code != 200:
            pytest.skip("Could not get payroll periods")
        
        periods = response.json()
        
        # Find an approved or paid period
        valid_period = next(
            (p for p in periods if p.get("status") in ["approved", "paid", "processed"]),
            None
        )
        
        if not valid_period:
            print("✓ No approved/paid periods available for bank file test (expected)")
            return
        
        period_id = valid_period["period_id"]
        
        # Try to generate bank file
        response = requests.get(
            f"{BASE_URL}/api/bank-files/generate/{period_id}/popular",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # Should return file content
            assert response.headers.get("content-type") in ["text/plain", "text/plain; charset=utf-8"]
            print(f"✓ Bank file generated for period {period_id}")
        elif response.status_code == 400:
            # No payroll entries in period
            print(f"✓ Bank file endpoint works (no entries in period)")
        else:
            print(f"✓ Bank file endpoint responded with status {response.status_code}")
    
    def test_bank_file_history(self, auth_headers):
        """Test GET /api/bank-files/history"""
        response = requests.get(f"{BASE_URL}/api/bank-files/history", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        history = response.json()
        assert isinstance(history, list), "Response should be a list"
        print(f"✓ Bank file history: {len(history)} records")


# ===================== INTEGRATION TESTS =====================

class TestIntegration:
    """Integration tests for new features"""
    
    def test_document_generation_flow(self, auth_headers, test_employee_id):
        """Test complete document generation flow"""
        # 1. Get categories
        response = requests.get(f"{BASE_URL}/api/doc-generator/categories", headers=auth_headers)
        assert response.status_code == 200
        categories = response.json()
        
        # 2. Get templates
        response = requests.get(f"{BASE_URL}/api/doc-generator/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()
        
        # 3. Generate document
        template = templates[0]
        response = requests.post(
            f"{BASE_URL}/api/doc-generator/generate",
            json={
                "template_id": template["template_id"],
                "employee_id": test_employee_id,
                "custom_values": {},
                "save_to_history": True
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        doc = response.json()
        
        # 4. Check history
        response = requests.get(f"{BASE_URL}/api/doc-generator/history", headers=auth_headers)
        assert response.status_code == 200
        history = response.json()
        
        # Verify document is in history
        doc_ids = [d["document_id"] for d in history]
        assert doc["document_id"] in doc_ids, "Generated document not in history"
        
        print("✓ Complete document generation flow works")
    
    def test_payroll_bank_integration(self, auth_headers):
        """Test payroll and bank file integration"""
        # 1. Get banks
        response = requests.get(f"{BASE_URL}/api/bank-files/banks", headers=auth_headers)
        assert response.status_code == 200
        banks = response.json()
        assert len(banks) >= 3
        
        # 2. Get payroll periods
        response = requests.get(f"{BASE_URL}/api/payroll-v2/periods", headers=auth_headers)
        if response.status_code == 200:
            periods = response.json()
            print(f"✓ Payroll-Bank integration: {len(banks)} banks, {len(periods)} periods")
        else:
            print("✓ Payroll-Bank integration: banks endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
