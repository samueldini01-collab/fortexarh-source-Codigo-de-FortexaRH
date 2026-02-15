"""
Test Suite for FortexaRH Modular Routers
Tests all refactored endpoints: auth, employees, payroll, attendance, vacations,
evaluations, recruitment, organigrama, accounting, system-users, dgii-reports, dashboard
"""
import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fortexa-preview.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAuthRouter:
    """Authentication endpoint tests - routes/auth.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_login_success(self):
        """Test successful login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == TEST_EMAIL
        assert "user_id" in data["user"]
        assert "company_id" in data["user"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint"""
        # First login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_resp.json()["token"]
        
        # Test /auth/me
        response = self.session.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        data = response.json()
        assert data["email"] == TEST_EMAIL
    
    def test_auth_me_unauthorized(self):
        """Test /auth/me without token"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
    
    def test_change_password_wrong_current(self):
        """Test change password with wrong current password"""
        # First login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_resp.json()["token"]
        
        # Try to change password with wrong current
        response = self.session.post(
            f"{BASE_URL}/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400


class TestCompanyRouter:
    """Company endpoint tests - routes/company.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login and get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_company(self):
        """Test GET /company"""
        response = self.session.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200, f"Get company failed: {response.text}"
        data = response.json()
        assert "company_id" in data
        assert "name" in data
    
    def test_get_company_settings(self):
        """Test GET /company/settings"""
        response = self.session.get(f"{BASE_URL}/api/company/settings")
        assert response.status_code == 200, f"Get company settings failed: {response.text}"
        data = response.json()
        # Should have default settings
        assert "payment_frequency" in data or "company_id" in data


class TestEmployeesRouter:
    """Employees endpoint tests - routes/employees.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_employees(self):
        """Test GET /employees"""
        response = self.session.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200, f"Get employees failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_and_get_employee(self):
        """Test POST /employees and GET /employees/{id}"""
        # Create employee
        employee_data = {
            "first_name": "TEST_Router",
            "last_name": "Employee",
            "email": f"test_router_{uuid.uuid4().hex[:6]}@test.com",
            "position": "Developer",
            "department": "IT",
            "hire_date": "2024-01-15",
            "salary": 50000.00
        }
        
        create_resp = self.session.post(f"{BASE_URL}/api/employees", json=employee_data)
        assert create_resp.status_code == 200, f"Create employee failed: {create_resp.text}"
        create_data = create_resp.json()
        assert "employee_id" in create_data
        
        employee_id = create_data["employee_id"]
        
        # Get employee
        get_resp = self.session.get(f"{BASE_URL}/api/employees/{employee_id}")
        assert get_resp.status_code == 200, f"Get employee failed: {get_resp.text}"
        emp_data = get_resp.json()
        assert emp_data["first_name"] == "TEST_Router"
        assert emp_data["email"] == employee_data["email"]
        
        # Cleanup - delete employee
        delete_resp = self.session.delete(f"{BASE_URL}/api/employees/{employee_id}")
        assert delete_resp.status_code == 200


class TestPayrollRouter:
    """Payroll endpoint tests - routes/payroll.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_payrolls(self):
        """Test GET /payroll"""
        response = self.session.get(f"{BASE_URL}/api/payroll")
        assert response.status_code == 200, f"Get payrolls failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestAttendanceRouter:
    """Attendance endpoint tests - routes/attendance.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_attendances(self):
        """Test GET /attendance"""
        response = self.session.get(f"{BASE_URL}/api/attendance")
        assert response.status_code == 200, f"Get attendances failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_attendances_by_date(self):
        """Test GET /attendance with date filter"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = self.session.get(f"{BASE_URL}/api/attendance?date={today}")
        assert response.status_code == 200, f"Get attendances by date failed: {response.text}"


class TestVacationsRouter:
    """Vacations endpoint tests - routes/vacations.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_vacations(self):
        """Test GET /vacations"""
        response = self.session.get(f"{BASE_URL}/api/vacations")
        assert response.status_code == 200, f"Get vacations failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestEvaluationsRouter:
    """Evaluations endpoint tests - routes/evaluations.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_evaluations(self):
        """Test GET /evaluations"""
        response = self.session.get(f"{BASE_URL}/api/evaluations")
        assert response.status_code == 200, f"Get evaluations failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestRecruitmentRouter:
    """Recruitment endpoint tests - routes/recruitment.py (jobs and candidates)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_jobs(self):
        """Test GET /jobs"""
        response = self.session.get(f"{BASE_URL}/api/jobs")
        assert response.status_code == 200, f"Get jobs failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_candidates(self):
        """Test GET /candidates"""
        response = self.session.get(f"{BASE_URL}/api/candidates")
        assert response.status_code == 200, f"Get candidates failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestOrganigramaRouter:
    """Organigrama endpoint tests - routes/organigrama.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_organigrama(self):
        """Test GET /organigrama"""
        response = self.session.get(f"{BASE_URL}/api/organigrama")
        assert response.status_code == 200, f"Get organigrama failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestAccountingRouter:
    """Accounting endpoint tests - routes/accounting.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_accounts(self):
        """Test GET /accounting/accounts"""
        response = self.session.get(f"{BASE_URL}/api/accounting/accounts")
        assert response.status_code == 200, f"Get accounts failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_catalog_templates(self):
        """Test GET /accounting/catalog-templates"""
        response = self.session.get(f"{BASE_URL}/api/accounting/catalog-templates")
        assert response.status_code == 200, f"Get catalog templates failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the default templates
        assert len(data) >= 1
    
    def test_get_journal_entries(self):
        """Test GET /accounting/journal-entries"""
        response = self.session.get(f"{BASE_URL}/api/accounting/journal-entries")
        assert response.status_code == 200, f"Get journal entries failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestSystemUsersRouter:
    """System Users endpoint tests - routes/system_users.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_system_users(self):
        """Test GET /system-users"""
        response = self.session.get(f"{BASE_URL}/api/system-users")
        assert response.status_code == 200, f"Get system users failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the test user
        assert len(data) >= 1
    
    def test_get_all_activities(self):
        """Test GET /system-users/activities/all"""
        response = self.session.get(f"{BASE_URL}/api/system-users/activities/all")
        assert response.status_code == 200, f"Get activities failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestDGIIReportsRouter:
    """DGII Reports endpoint tests - routes/dgii_reports.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_dgii_summary(self):
        """Test GET /dgii-reports/summary"""
        current_period = datetime.now().strftime("%Y-%m")
        response = self.session.get(f"{BASE_URL}/api/dgii-reports/summary?period={current_period}")
        assert response.status_code == 200, f"Get DGII summary failed: {response.text}"
        data = response.json()
        assert "period" in data
        assert "tss" in data
        assert "isr" in data
    
    def test_get_dgii_deadlines(self):
        """Test GET /dgii-reports/deadlines"""
        response = self.session.get(f"{BASE_URL}/api/dgii-reports/deadlines")
        assert response.status_code == 200, f"Get DGII deadlines failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestDashboardRouter:
    """Dashboard endpoint tests - routes/dashboard.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_dashboard_stats(self):
        """Test GET /dashboard/stats"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200, f"Get dashboard stats failed: {response.text}"
        data = response.json()
        assert "total_employees" in data or "employee_count" in data
    
    def test_get_payroll_stats(self):
        """Test GET /dashboard/payroll-stats"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/payroll-stats")
        assert response.status_code == 200, f"Get payroll stats failed: {response.text}"
        data = response.json()
        assert "monthly_trend" in data or "by_department" in data


class TestUnauthorizedAccess:
    """Test that all endpoints require authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_employees_unauthorized(self):
        """Test /employees without auth"""
        response = self.session.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 401
    
    def test_company_unauthorized(self):
        """Test /company without auth"""
        response = self.session.get(f"{BASE_URL}/api/company")
        assert response.status_code == 401
    
    def test_payroll_unauthorized(self):
        """Test /payroll without auth"""
        response = self.session.get(f"{BASE_URL}/api/payroll")
        assert response.status_code == 401
    
    def test_dashboard_unauthorized(self):
        """Test /dashboard/stats without auth"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
