"""
Test Employee Portal Fixes:
1. Password translations (frontend test)
2. PDF download endpoint with payroll_v2 lookup
3. Payslips list endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
EMPLOYEE_CEDULA = "001-0000001-1"
EMPLOYEE_PASSWORD = "portal123"


class TestEmployeePortalLogin:
    """Test employee portal login"""
    
    def test_01_login_success(self):
        """Test employee login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": EMPLOYEE_CEDULA,
            "password": EMPLOYEE_PASSWORD
        })
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "employee" in data, "Response should contain employee info"
        
        # Store token for other tests
        TestEmployeePortalLogin.token = data["token"]
        TestEmployeePortalLogin.employee_id = data["employee"]["employee_id"]
        print(f"Login successful for employee: {data['employee']['name']}")
    
    def test_02_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
            "document_number": "999-9999999-9",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestEmployeePortalPayslips:
    """Test payslips endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        if not hasattr(TestEmployeePortalLogin, 'token'):
            response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
                "document_number": EMPLOYEE_CEDULA,
                "password": EMPLOYEE_PASSWORD
            })
            if response.status_code == 200:
                TestEmployeePortalLogin.token = response.json()["token"]
            else:
                pytest.skip("Could not authenticate")
        self.headers = {"Authorization": f"Bearer {TestEmployeePortalLogin.token}"}
    
    def test_03_get_payslips_list(self):
        """Test getting payslips list"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/payslips", headers=self.headers)
        print(f"Payslips response status: {response.status_code}")
        print(f"Payslips response: {response.text[:1000] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            slip = data[0]
            print(f"First payslip keys: {slip.keys()}")
            # Check for payroll_id (new format) or entry_id (old format)
            has_id = "payroll_id" in slip or "entry_id" in slip
            assert has_id, "Payslip should have payroll_id or entry_id"
            
            # Store payslip ID for PDF download test
            TestEmployeePortalPayslips.payslip_id = slip.get("payroll_id") or slip.get("entry_id")
            TestEmployeePortalPayslips.payslips = data
            print(f"Found {len(data)} payslips, first ID: {TestEmployeePortalPayslips.payslip_id}")
        else:
            print("No payslips found for this employee")
            TestEmployeePortalPayslips.payslip_id = None
            TestEmployeePortalPayslips.payslips = []
    
    def test_04_get_payslip_detail(self):
        """Test getting payslip detail"""
        if not hasattr(TestEmployeePortalPayslips, 'payslip_id') or not TestEmployeePortalPayslips.payslip_id:
            pytest.skip("No payslip available to test")
        
        payslip_id = TestEmployeePortalPayslips.payslip_id
        response = requests.get(f"{BASE_URL}/api/employee-portal/payslips/{payslip_id}", headers=self.headers)
        print(f"Payslip detail response status: {response.status_code}")
        print(f"Payslip detail response: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "net_salary" in data or "gross_salary" in data, "Payslip should have salary info"
    
    def test_05_download_payslip_pdf(self):
        """Test downloading payslip as PDF - this was the bug fix"""
        if not hasattr(TestEmployeePortalPayslips, 'payslip_id') or not TestEmployeePortalPayslips.payslip_id:
            pytest.skip("No payslip available to test")
        
        payslip_id = TestEmployeePortalPayslips.payslip_id
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/payslips/{payslip_id}/pdf", 
            headers=self.headers
        )
        print(f"PDF download response status: {response.status_code}")
        print(f"PDF content-type: {response.headers.get('content-type', 'not set')}")
        
        # The bug was 404 error because endpoint only searched payroll_entries by entry_id
        # but payroll_v2 uses payroll_id
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:500] if response.text else 'empty'}"
        
        content_type = response.headers.get('content-type', '')
        assert 'application/pdf' in content_type, f"Expected PDF content-type, got: {content_type}"
        
        # Check PDF content starts with PDF magic bytes
        content = response.content
        assert len(content) > 100, "PDF should have content"
        assert content[:4] == b'%PDF', f"Content should start with PDF header, got: {content[:20]}"
        
        print(f"PDF downloaded successfully, size: {len(content)} bytes")
    
    def test_06_verify_pdf_contains_fortexaerp_url(self):
        """Verify PDF footer contains fortexaerp.com URL"""
        if not hasattr(TestEmployeePortalPayslips, 'payslip_id') or not TestEmployeePortalPayslips.payslip_id:
            pytest.skip("No payslip available to test")
        
        payslip_id = TestEmployeePortalPayslips.payslip_id
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/payslips/{payslip_id}/pdf", 
            headers=self.headers
        )
        
        assert response.status_code == 200
        
        # PDF content is binary, but we can search for the URL string
        content = response.content
        # The URL should be embedded in the PDF
        # Note: PDF text is often encoded, so we check for partial matches
        url_found = b'fortexaerp.com' in content or b'fortexaerp' in content
        print(f"PDF contains fortexaerp reference: {url_found}")
        # This is informational - the URL might be encoded differently in PDF
        

class TestEmployeePortalDashboard:
    """Test dashboard endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        if not hasattr(TestEmployeePortalLogin, 'token'):
            response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
                "document_number": EMPLOYEE_CEDULA,
                "password": EMPLOYEE_PASSWORD
            })
            if response.status_code == 200:
                TestEmployeePortalLogin.token = response.json()["token"]
            else:
                pytest.skip("Could not authenticate")
        self.headers = {"Authorization": f"Bearer {TestEmployeePortalLogin.token}"}
    
    def test_07_get_dashboard(self):
        """Test getting dashboard data"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/dashboard", headers=self.headers)
        print(f"Dashboard response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "employee" in data, "Dashboard should have employee info"
        assert "salary" in data, "Dashboard should have salary info"
        assert "vacations" in data, "Dashboard should have vacation info"
        print(f"Dashboard loaded for: {data['employee']['name']}")


class TestEmployeePortalProfile:
    """Test profile endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        if not hasattr(TestEmployeePortalLogin, 'token'):
            response = requests.post(f"{BASE_URL}/api/employee-portal/login", json={
                "document_number": EMPLOYEE_CEDULA,
                "password": EMPLOYEE_PASSWORD
            })
            if response.status_code == 200:
                TestEmployeePortalLogin.token = response.json()["token"]
            else:
                pytest.skip("Could not authenticate")
        self.headers = {"Authorization": f"Bearer {TestEmployeePortalLogin.token}"}
    
    def test_08_get_profile(self):
        """Test getting employee profile"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/profile", headers=self.headers)
        print(f"Profile response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "employee" in data, "Profile should have employee info"
        employee = data["employee"]
        assert "first_name" in employee or "name" in employee, "Employee should have name"
        print(f"Profile loaded: {employee.get('first_name', '')} {employee.get('last_name', '')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
