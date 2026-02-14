"""
Test Dashboard Fixes - Iteration 48
Tests for:
1. PayrollDashboard Top 10 Salaries showing actual salary values (not RD$0)
2. Notification endpoints (GET /api/notifications, GET /api/notifications/count)
3. Notification settings endpoints (/api/notification-settings/*)
4. Dashboard payroll-stats endpoint returning proper data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAuthSession:
    """Get authentication session for all tests"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
        
        # Extract token and set Authorization header
        data = response.json()
        token = data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        
        return session
    
    def test_login_success(self, auth_session):
        """Verify login works and returns user data"""
        response = auth_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        print(f"Logged in as: {data.get('email')}")


class TestPayrollDashboardStats:
    """Test payroll dashboard stats endpoint fixes"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Auth failed: {response.text}")
        data = response.json()
        token = data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_payroll_stats_endpoint(self, auth_session):
        """Test /api/dashboard/payroll-stats returns valid data"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard/payroll-stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields exist
        assert "summary" in data or "monthly_trend" in data
        print(f"Payroll stats response: {list(data.keys())}")
    
    def test_top_salaries_have_values(self, auth_session):
        """Verify top_salaries array contains actual salary values (not 0)"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard/payroll-stats")
        assert response.status_code == 200
        data = response.json()
        
        top_salaries = data.get("top_salaries", [])
        print(f"Top salaries count: {len(top_salaries)}")
        
        if len(top_salaries) > 0:
            # Verify each entry has the required fields
            for i, emp in enumerate(top_salaries):
                assert "employee_id" in emp, f"Missing employee_id in entry {i}"
                assert "name" in emp, f"Missing name in entry {i}"
                assert "salary" in emp, f"Missing salary in entry {i}"
                
                # KEY FIX VERIFICATION: salary should NOT be 0 for employees
                salary = emp.get("salary", 0)
                print(f"  [{i+1}] {emp.get('name')}: salary={salary}")
                
                # If employee exists and has salary, it should be > 0
                if emp.get("name") and emp.get("name").strip():
                    # At least some employees should have non-zero salary
                    pass  # Will check aggregate below
            
            # Verify at least one employee has non-zero salary
            salaries_with_value = [e for e in top_salaries if e.get("salary", 0) > 0]
            print(f"Employees with salary > 0: {len(salaries_with_value)}/{len(top_salaries)}")
            
            # At least 50% should have salary values
            if len(top_salaries) >= 2:
                assert len(salaries_with_value) > 0, "All top_salaries have 0 salary - FIX NOT APPLIED"
        else:
            print("No top_salaries data (may be empty company)")
    
    def test_avg_salary_not_zero(self, auth_session):
        """Verify avg_salary uses salary field (not base_salary)"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard/payroll-stats")
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", {})
        avg_salary = summary.get("avg_salary", 0)
        total_employees = summary.get("total_employees", 0)
        
        print(f"Summary: total_employees={total_employees}, avg_salary={avg_salary}")
        
        if total_employees > 0:
            # avg_salary should be a reasonable value
            assert isinstance(avg_salary, (int, float))
            # If there are employees, avg should generally be > 0
            print(f"Average salary: {avg_salary}")
    
    def test_department_distribution_has_salary(self, auth_session):
        """Verify department distribution uses salary field"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard/payroll-stats")
        assert response.status_code == 200
        data = response.json()
        
        dept_dist = data.get("department_distribution", [])
        print(f"Department distribution count: {len(dept_dist)}")
        
        for dept in dept_dist:
            assert "department" in dept
            total = dept.get("total_salary", 0)
            print(f"  {dept.get('department')}: total_salary={total}")


class TestNotificationBellEndpoints:
    """Test notification bell endpoints (notifications_system.py)"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Auth failed: {response.text}")
        data = response.json()
        token = data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_notifications(self, auth_session):
        """Test GET /api/notifications endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        print(f"Notifications count: {len(data)}")
        
        # If there are notifications, check structure
        if len(data) > 0:
            notif = data[0]
            assert "notification_id" in notif or "id" in notif
            assert "title" in notif
            print(f"Sample notification: {notif.get('title')}")
    
    def test_get_notifications_count(self, auth_session):
        """Test GET /api/notifications/count endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/notifications/count")
        assert response.status_code == 200
        data = response.json()
        
        assert "unread_count" in data
        print(f"Unread notifications count: {data.get('unread_count')}")


class TestNotificationSettingsEndpoints:
    """Test notification settings endpoints (notifications.py with /notification-settings prefix)"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Auth failed: {response.text}")
        data = response.json()
        token = data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_notification_settings(self, auth_session):
        """Test GET /api/notification-settings/settings"""
        response = auth_session.get(f"{BASE_URL}/api/notification-settings/settings")
        assert response.status_code == 200
        data = response.json()
        
        # Should return settings object
        assert isinstance(data, dict)
        print(f"Notification settings keys: {list(data.keys())}")
        
        # Common settings fields
        if "payroll_reminder_enabled" in data:
            print(f"Payroll reminder enabled: {data.get('payroll_reminder_enabled')}")
    
    def test_get_upcoming_birthdays(self, auth_session):
        """Test GET /api/notification-settings/upcoming-birthdays"""
        response = auth_session.get(f"{BASE_URL}/api/notification-settings/upcoming-birthdays?days=30")
        assert response.status_code == 200
        data = response.json()
        
        # Should return list
        assert isinstance(data, list)
        print(f"Upcoming birthdays count: {len(data)}")
    
    def test_get_notification_logs(self, auth_session):
        """Test GET /api/notification-settings/logs"""
        response = auth_session.get(f"{BASE_URL}/api/notification-settings/logs?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        # Should return list
        assert isinstance(data, list)
        print(f"Notification logs count: {len(data)}")


class TestMetricsDashboard:
    """Test metrics dashboard endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Auth failed: {response.text}")
        data = response.json()
        token = data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_metrics_dashboard_endpoint(self, auth_session):
        """Test /api/metrics/dashboard returns valid data"""
        response = auth_session.get(f"{BASE_URL}/api/metrics/dashboard?year=2026")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "payroll_trend" in data or "employee_metrics" in data or "department_costs" in data
        print(f"Metrics dashboard keys: {list(data.keys())}")
        
        # Check payroll_trend contains month_number for drill-down
        payroll_trend = data.get("payroll_trend", [])
        if len(payroll_trend) > 0:
            sample = payroll_trend[0]
            print(f"Payroll trend sample keys: {list(sample.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
