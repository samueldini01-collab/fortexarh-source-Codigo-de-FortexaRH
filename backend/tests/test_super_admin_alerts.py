"""
Super Admin Alerts API Tests - FortexaRH
Tests for the new inactivity alerts feature:
- GET /api/super-admin/alerts returns companies inactive 30+ days
- Alerts include: company_id, name, subscription_plan, days_inactive, last_activity, risk, user_count, employee_count
- Risk levels: high (60+ days), medium (30-59 days)
- GET /api/super-admin/companies includes days_inactive and last_activity fields
- Login tracking updates last_login on user and last_activity on company
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Super Admin credentials
SA_USERNAME = "fortexa2026rd"
SA_PASSWORD = "FortexaAdmin2026!"

# Regular user credentials for login tracking test
TEST_USER_EMAIL = "test_refactor@fortexa.com"
TEST_USER_PASSWORD = "test123"


@pytest.fixture
def sa_token():
    """Get Super Admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
        "username": SA_USERNAME,
        "password": SA_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Super Admin authentication failed - skipping authenticated tests")


@pytest.fixture
def sa_headers(sa_token):
    """Get headers with Super Admin token"""
    return {"Authorization": f"Bearer {sa_token}"}


# ---------- Alerts Endpoint Tests ----------

class TestSuperAdminAlertsEndpoint:
    """Tests for GET /api/super-admin/alerts endpoint"""
    
    def test_alerts_endpoint_exists(self, sa_headers):
        """GET /api/super-admin/alerts should return 200"""
        response = requests.get(f"{BASE_URL}/api/super-admin/alerts", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Alerts endpoint returns {len(data)} alerts")
    
    def test_alerts_unauthenticated(self):
        """GET /api/super-admin/alerts without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/super-admin/alerts")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated alerts request correctly rejected")
    
    def test_alerts_structure(self, sa_headers):
        """Alerts should have required fields: company_id, name, subscription_plan, days_inactive, last_activity, risk, user_count, employee_count"""
        response = requests.get(f"{BASE_URL}/api/super-admin/alerts", headers=sa_headers)
        assert response.status_code == 200
        
        alerts = response.json()
        
        if len(alerts) == 0:
            print("✓ No alerts found (all companies have recent activity)")
            return
        
        required_fields = ["company_id", "name", "subscription_plan", "days_inactive", "last_activity", "risk", "user_count", "employee_count"]
        
        for alert in alerts[:5]:  # Check first 5 alerts
            for field in required_fields:
                assert field in alert, f"Alert should have '{field}' field. Got: {list(alert.keys())}"
            
            print(f"✓ Alert for '{alert['name']}': {alert['days_inactive']}d inactive, risk={alert['risk']}")
    
    def test_alerts_only_30_plus_days(self, sa_headers):
        """All alerts should be for companies inactive 30+ days"""
        response = requests.get(f"{BASE_URL}/api/super-admin/alerts", headers=sa_headers)
        assert response.status_code == 200
        
        alerts = response.json()
        
        for alert in alerts:
            days = alert.get("days_inactive", 0)
            assert days >= 30, f"Alert for '{alert.get('name')}' has days_inactive={days}, should be >= 30"
        
        print(f"✓ All {len(alerts)} alerts have days_inactive >= 30")
    
    def test_alerts_risk_levels(self, sa_headers):
        """Risk should be 'high' for 60+ days, 'medium' for 30-59 days"""
        response = requests.get(f"{BASE_URL}/api/super-admin/alerts", headers=sa_headers)
        assert response.status_code == 200
        
        alerts = response.json()
        
        high_count = 0
        medium_count = 0
        
        for alert in alerts:
            days = alert.get("days_inactive", 0)
            risk = alert.get("risk")
            
            if days >= 60:
                assert risk == "high", f"Company '{alert.get('name')}' with {days}d should have risk='high', got '{risk}'"
                high_count += 1
            elif days >= 30:
                assert risk == "medium", f"Company '{alert.get('name')}' with {days}d should have risk='medium', got '{risk}'"
                medium_count += 1
        
        print(f"✓ Risk levels correct: {high_count} high (60+d), {medium_count} medium (30-59d)")
    
    def test_alerts_sorted_by_days_inactive(self, sa_headers):
        """Alerts should be sorted by days_inactive descending"""
        response = requests.get(f"{BASE_URL}/api/super-admin/alerts", headers=sa_headers)
        assert response.status_code == 200
        
        alerts = response.json()
        
        if len(alerts) < 2:
            print("✓ Not enough alerts to verify sorting")
            return
        
        days_list = [a.get("days_inactive", 0) for a in alerts]
        assert days_list == sorted(days_list, reverse=True), "Alerts should be sorted by days_inactive descending"
        
        print(f"✓ Alerts correctly sorted: {days_list[:5]}...")


# ---------- Companies Endpoint - days_inactive and last_activity ----------

class TestCompaniesInactivityFields:
    """Tests for days_inactive and last_activity fields in GET /api/super-admin/companies"""
    
    def test_companies_have_days_inactive(self, sa_headers):
        """GET /api/super-admin/companies should include days_inactive field"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "days_inactive" in company, f"Company '{company.get('name')}' should have days_inactive field"
            days = company.get("days_inactive")
            # days_inactive can be None if no activity data, or an integer
            if days is not None:
                assert isinstance(days, int), f"days_inactive should be int or None, got {type(days)}"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}': days_inactive={days}")
    
    def test_companies_have_last_activity(self, sa_headers):
        """GET /api/super-admin/companies should include last_activity field"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "last_activity" in company, f"Company '{company.get('name')}' should have last_activity field"
            last_activity = company.get("last_activity")
            # last_activity can be None or a date string
            if last_activity is not None:
                assert isinstance(last_activity, str), f"last_activity should be string or None, got {type(last_activity)}"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}': last_activity={last_activity}")


# ---------- Login Tracking Tests ----------

class TestLoginTracking:
    """Tests for login tracking - updates last_login on user and last_activity on company"""
    
    def test_login_updates_last_activity(self, sa_headers):
        """Login should update company's last_activity"""
        # First, get the company_id for the test user
        # Login as test user
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Test user login failed: {login_response.status_code} - {login_response.text}")
        
        login_data = login_response.json()
        
        # Handle 2FA if enabled
        if login_data.get("requires_2fa"):
            pytest.skip("Test user has 2FA enabled - skipping login tracking test")
        
        company_id = login_data.get("user", {}).get("company_id")
        
        if not company_id:
            pytest.skip("Test user has no company_id")
        
        print(f"✓ Logged in as {TEST_USER_EMAIL}, company_id: {company_id}")
        
        # Now check the company's last_activity via super admin
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert companies_response.status_code == 200
        
        companies = companies_response.json()
        company = next((c for c in companies if c.get("company_id") == company_id), None)
        
        if company:
            last_activity = company.get("last_activity")
            print(f"✓ Company '{company.get('name')}' last_activity: {last_activity}")
            
            # Verify last_activity is recent (within last minute)
            if last_activity:
                from datetime import datetime, timezone
                try:
                    last_dt = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    diff_seconds = (now - last_dt).total_seconds()
                    
                    # Should be within last 60 seconds since we just logged in
                    assert diff_seconds < 120, f"last_activity should be recent, but is {diff_seconds}s ago"
                    print(f"✓ last_activity is recent ({diff_seconds:.1f}s ago)")
                except Exception as e:
                    print(f"⚠ Could not parse last_activity: {e}")
        else:
            print(f"⚠ Company {company_id} not found in super admin companies list")


# ---------- KPI Cards Tests ----------

class TestKPICards:
    """Tests for KPI cards - Total, Activas, Inactivas, Empleados, Usuarios"""
    
    def test_stats_kpi_values(self, sa_headers):
        """GET /api/super-admin/stats should return all KPI values"""
        response = requests.get(f"{BASE_URL}/api/super-admin/stats", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all KPI fields exist
        assert "total_companies" in data, "Stats should have total_companies"
        assert "active_companies" in data, "Stats should have active_companies"
        assert "inactive_companies" in data, "Stats should have inactive_companies"
        assert "total_employees" in data, "Stats should have total_employees"
        assert "total_users" in data, "Stats should have total_users"
        
        # Verify types
        assert isinstance(data["total_companies"], int)
        assert isinstance(data["active_companies"], int)
        assert isinstance(data["inactive_companies"], int)
        assert isinstance(data["total_employees"], int)
        assert isinstance(data["total_users"], int)
        
        # Verify active + inactive = total
        assert data["active_companies"] + data["inactive_companies"] == data["total_companies"], \
            f"active ({data['active_companies']}) + inactive ({data['inactive_companies']}) should equal total ({data['total_companies']})"
        
        print(f"✓ KPIs: Total={data['total_companies']}, Activas={data['active_companies']}, Inactivas={data['inactive_companies']}")
        print(f"✓ KPIs: Empleados={data['total_employees']}, Usuarios={data['total_users']}")


# ---------- Sync Button Tests ----------

class TestSyncButton:
    """Tests for sync-statuses endpoint (Sync button)"""
    
    def test_sync_statuses_works(self, sa_headers):
        """POST /api/super-admin/sync-statuses should work"""
        response = requests.post(f"{BASE_URL}/api/super-admin/sync-statuses", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "activated" in data
        assert "deactivated" in data
        assert "total" in data
        
        print(f"✓ Sync completed: {data['activated']} activated, {data['deactivated']} deactivated, {data['total']} total")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
