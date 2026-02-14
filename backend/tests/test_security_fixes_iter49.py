"""
Test Suite for FortexaRH P0+P1 Security Fixes (Iteration 49)
Tests:
1. Login endpoint with rate limiting
2. Payroll Dashboard stats with top_salaries
3. Accounting routes (modular)
4. System Users management (modular)
5. Reports System page (double /api fix)
6. Notifications endpoints
7. Dashboard and Metrics
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAuthAndLogin:
    """Test authentication with rate limiting"""
    token = None
    
    def test_login_success(self):
        """Test login endpoint works correctly (POST /api/auth/login)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token missing from login response"
        assert "user" in data, "User data missing from login response"
        TestAuthAndLogin.token = data["token"]
        print(f"PASSED: Login successful, token received")
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"PASSED: Invalid login returns 401")


class TestPayrollDashboard:
    """Test Payroll Dashboard stats - top_salaries fix"""
    
    @pytest.fixture(autouse=True)
    def get_token(self):
        """Get auth token"""
        if not TestAuthAndLogin.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            TestAuthAndLogin.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndLogin.token}"}
    
    def test_dashboard_stats(self):
        """Test GET /api/dashboard/stats returns valid data"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        assert "total_employees" in data, "total_employees missing"
        print(f"PASSED: Dashboard stats - {data.get('total_employees')} employees")
    
    def test_payroll_stats_endpoint(self):
        """Test GET /api/dashboard/payroll-stats returns top_salaries"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/payroll-stats",
            headers=self.headers
        )
        assert response.status_code == 200, f"Payroll stats failed: {response.text}"
        data = response.json()
        assert "top_salaries" in data, "top_salaries missing from payroll-stats"
        assert "summary" in data, "summary missing from payroll-stats"
        print(f"PASSED: Payroll stats returns top_salaries ({len(data.get('top_salaries', []))} entries)")
        
    def test_top_salaries_have_values(self):
        """Test top_salaries contains actual salary values, not zeros"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/payroll-stats",
            headers=self.headers
        )
        data = response.json()
        top_salaries = data.get("top_salaries", [])
        if top_salaries:
            # Check that at least some salaries are > 0
            non_zero_salaries = [s for s in top_salaries if s.get("salary", 0) > 0]
            assert len(non_zero_salaries) > 0, "All top salaries are zero - fix may have regressed"
            print(f"PASSED: Top salaries have values ({len(non_zero_salaries)} non-zero)")
        else:
            print("SKIPPED: No employees to verify top_salaries")


class TestAccountingModule:
    """Test Accounting routes (via modular router)"""
    
    @pytest.fixture(autouse=True)
    def get_token(self):
        if not TestAuthAndLogin.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            TestAuthAndLogin.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndLogin.token}"}
    
    def test_get_accounts(self):
        """Test GET /api/accounting/accounts"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/accounts",
            headers=self.headers
        )
        assert response.status_code == 200, f"Accounting accounts failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of accounts"
        print(f"PASSED: Accounting accounts returns {len(data)} accounts")
    
    def test_get_journal_entries(self):
        """Test GET /api/accounting/journal-entries"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries",
            headers=self.headers
        )
        assert response.status_code == 200, f"Journal entries failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of journal entries"
        print(f"PASSED: Journal entries returns {len(data)} entries")
    
    def test_get_catalog_templates(self):
        """Test GET /api/accounting/catalog-templates"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/catalog-templates",
            headers=self.headers
        )
        assert response.status_code == 200, f"Catalog templates failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of templates"
        print(f"PASSED: Catalog templates returns {len(data)} templates")


class TestSystemUsersModule:
    """Test System Users routes (via modular router)"""
    
    @pytest.fixture(autouse=True)
    def get_token(self):
        if not TestAuthAndLogin.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            TestAuthAndLogin.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndLogin.token}"}
    
    def test_get_system_users(self):
        """Test GET /api/system-users"""
        response = requests.get(
            f"{BASE_URL}/api/system-users",
            headers=self.headers
        )
        assert response.status_code == 200, f"System users failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of users"
        print(f"PASSED: System users returns {len(data)} users")
    
    def test_get_all_activities(self):
        """Test GET /api/system-users/activities/all (fixed endpoint)"""
        response = requests.get(
            f"{BASE_URL}/api/system-users/activities/all",
            headers=self.headers
        )
        assert response.status_code == 200, f"User activities failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of activities"
        print(f"PASSED: User activities returns {len(data)} activities")


class TestReportsSystemModule:
    """Test Reports System routes (double /api prefix fix)"""
    
    @pytest.fixture(autouse=True)
    def get_token(self):
        if not TestAuthAndLogin.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            TestAuthAndLogin.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndLogin.token}"}
    
    def test_get_reports_catalog(self):
        """Test GET /api/reports-system/catalog (previously was /api/api/...)"""
        response = requests.get(
            f"{BASE_URL}/api/reports-system/catalog",
            headers=self.headers
        )
        assert response.status_code == 200, f"Reports catalog failed: {response.text}"
        data = response.json()
        assert "categories" in data or "total_reports" in data, "Expected catalog structure"
        print(f"PASSED: Reports catalog loads ({data.get('total_reports', 'N/A')} reports)")
    
    def test_get_saved_reports(self):
        """Test GET /api/reports-system/saved"""
        response = requests.get(
            f"{BASE_URL}/api/reports-system/saved",
            headers=self.headers
        )
        assert response.status_code == 200, f"Saved reports failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of saved reports"
        print(f"PASSED: Saved reports returns {len(data)} items")
    
    def test_get_report_history(self):
        """Test GET /api/reports-system/history"""
        response = requests.get(
            f"{BASE_URL}/api/reports-system/history",
            headers=self.headers
        )
        assert response.status_code == 200, f"Report history failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of history items"
        print(f"PASSED: Report history returns {len(data)} items")


class TestNotificationsModule:
    """Test Notifications endpoints (both notification-settings and notifications)"""
    
    @pytest.fixture(autouse=True)
    def get_token(self):
        if not TestAuthAndLogin.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            TestAuthAndLogin.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndLogin.token}"}
    
    def test_get_notification_settings(self):
        """Test GET /api/notification-settings/settings"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/settings",
            headers=self.headers
        )
        assert response.status_code == 200, f"Notification settings failed: {response.text}"
        print(f"PASSED: Notification settings loads")
    
    def test_get_upcoming_birthdays(self):
        """Test GET /api/notification-settings/upcoming-birthdays"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/upcoming-birthdays",
            headers=self.headers
        )
        assert response.status_code == 200, f"Upcoming birthdays failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of birthdays"
        print(f"PASSED: Upcoming birthdays returns {len(data)} items")
    
    def test_get_notification_logs(self):
        """Test GET /api/notification-settings/logs"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/logs",
            headers=self.headers
        )
        assert response.status_code == 200, f"Notification logs failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of logs"
        print(f"PASSED: Notification logs returns {len(data)} items")
    
    def test_get_notifications_bell(self):
        """Test GET /api/notifications (bell icon)"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200, f"Notifications bell failed: {response.text}"
        print(f"PASSED: Notifications bell endpoint works")
    
    def test_get_notifications_count(self):
        """Test GET /api/notifications/count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/count",
            headers=self.headers
        )
        assert response.status_code == 200, f"Notifications count failed: {response.text}"
        data = response.json()
        assert "unread_count" in data, "Expected unread_count in response"
        print(f"PASSED: Notifications count - {data.get('unread_count')} unread")


class TestMetricsDashboard:
    """Test Metrics Dashboard endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_token(self):
        if not TestAuthAndLogin.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            TestAuthAndLogin.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndLogin.token}"}
    
    def test_metrics_dashboard(self):
        """Test GET /api/metrics/dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/metrics/dashboard",
            headers=self.headers
        )
        assert response.status_code == 200, f"Metrics dashboard failed: {response.text}"
        print(f"PASSED: Metrics dashboard loads")


class TestSubscription:
    """Test Subscription endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_token(self):
        if not TestAuthAndLogin.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            TestAuthAndLogin.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndLogin.token}"}
    
    def test_get_subscription(self):
        """Test GET /api/subscription"""
        response = requests.get(
            f"{BASE_URL}/api/subscription",
            headers=self.headers
        )
        assert response.status_code == 200, f"Subscription failed: {response.text}"
        print(f"PASSED: Subscription endpoint works")


class TestRolesEndpoint:
    """Test Roles endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_token(self):
        if not TestAuthAndLogin.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            TestAuthAndLogin.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndLogin.token}"}
    
    def test_get_roles(self):
        """Test GET /api/roles"""
        response = requests.get(
            f"{BASE_URL}/api/roles",
            headers=self.headers
        )
        assert response.status_code == 200, f"Roles failed: {response.text}"
        print(f"PASSED: Roles endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
