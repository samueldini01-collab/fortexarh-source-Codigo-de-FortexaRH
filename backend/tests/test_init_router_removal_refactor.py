"""
FortexaRH - init_router Pattern Removal Validation Tests (Iteration 189)
=========================================================================
This tests the massive refactor where init_router was removed from 42 route files.
Routes now import db from config.py directly and use get_current_user/get_user_from_request 
from utils/auth.py.

Test Categories:
1. Auth endpoints (login, check-partner, me)
2. Subscription endpoints
3. Dashboard endpoints
4. Core CRUD endpoints (employees, loans, roles, documents)
5. Partner endpoints
6. Geolocation attendance
7. Bank files
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://mi-perfil-repair.preview.emergentagent.com"

# Test credentials from review request
REGULAR_USER_EMAIL = "test_refactor@fortexa.com"
REGULAR_USER_PASSWORD = "test123"
PARTNER_USER_EMAIL = "testpartner@test.com"
PARTNER_USER_PASSWORD = "test123"


class TestHealthEndpoints:
    """Test health check endpoints - no auth required"""
    
    def test_health_check(self):
        """Test /health endpoint works"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ /health returns healthy status")
    
    def test_health_db(self):
        """Test /health/db endpoint for database connection"""
        response = requests.get(f"{BASE_URL}/health/db")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✓ /health/db returns status: {data.get('status')}")
    
    def test_config_status(self):
        """Test /api/config/status endpoint"""
        response = requests.get(f"{BASE_URL}/api/config/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ /api/config/status returns ok")


class TestAuthEndpointsRegularUser:
    """Test auth endpoints with regular user (test_refactor@fortexa.com)"""
    
    def test_login_regular_user(self):
        """POST /api/auth/login - regular user should return token and is_partner=false"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "token" in data, "Token missing from response"
        assert "user" in data, "User missing from response"
        assert len(data["token"]) > 0, "Token should not be empty"
        
        # Validate user data
        user = data["user"]
        assert user["email"] == REGULAR_USER_EMAIL
        assert user.get("is_partner", False) == False, "Regular user should have is_partner=false"
        assert user.get("role") == "admin", f"Expected role=admin, got {user.get('role')}"
        
        print(f"✓ Regular user login successful - is_partner={user.get('is_partner')}, role={user.get('role')}")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly returns 401")


class TestAuthEndpointsPartnerUser:
    """Test auth endpoints with partner user (testpartner@test.com)"""
    
    def test_login_partner_user(self):
        """POST /api/auth/login - partner should return is_partner=true"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_USER_EMAIL,
            "password": PARTNER_USER_PASSWORD
        })
        assert response.status_code == 200, f"Partner login failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "token" in data, "Token missing"
        assert "user" in data, "User missing"
        
        # Validate partner-specific fields
        user = data["user"]
        assert user["email"] == PARTNER_USER_EMAIL
        assert user.get("is_partner") == True, f"Partner should have is_partner=true, got {user.get('is_partner')}"
        assert user.get("partner_id") is not None, "Partner should have partner_id"
        
        print(f"✓ Partner login successful - is_partner={user.get('is_partner')}, partner_id={user.get('partner_id')}")
    
    def test_check_partner_with_partner_email(self):
        """POST /api/auth/check-partner - partner email should return is_partner=true"""
        response = requests.post(f"{BASE_URL}/api/auth/check-partner", json={
            "email": PARTNER_USER_EMAIL
        })
        assert response.status_code == 200, f"Check partner failed: {response.text}"
        data = response.json()
        assert data.get("is_partner") == True, f"Expected is_partner=true for partner email"
        print(f"✓ check-partner for partner email returns is_partner=true")
    
    def test_check_partner_with_regular_email(self):
        """POST /api/auth/check-partner - regular email should return is_partner=false"""
        response = requests.post(f"{BASE_URL}/api/auth/check-partner", json={
            "email": REGULAR_USER_EMAIL
        })
        assert response.status_code == 200, f"Check partner failed: {response.text}"
        data = response.json()
        assert data.get("is_partner") == False, f"Expected is_partner=false for regular email"
        print(f"✓ check-partner for regular email returns is_partner=false")


class TestAuthMeEndpoint:
    """Test /api/auth/me endpoint"""
    
    @pytest.fixture
    def regular_token(self):
        """Get token for regular user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not get regular user token")
    
    @pytest.fixture
    def partner_token(self):
        """Get token for partner user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_USER_EMAIL,
            "password": PARTNER_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not get partner token")
    
    def test_auth_me_regular_user(self, regular_token):
        """GET /api/auth/me with regular user token should return user data"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert data["email"] == REGULAR_USER_EMAIL
        assert data.get("is_partner") == False
        print(f"✓ /api/auth/me for regular user returns correct data")
    
    def test_auth_me_partner_user(self, partner_token):
        """GET /api/auth/me with partner token should return partner data"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert data["email"] == PARTNER_USER_EMAIL
        assert data.get("is_partner") == True
        assert data.get("partner_id") is not None
        print(f"✓ /api/auth/me for partner returns is_partner=true, partner_id={data.get('partner_id')}")
    
    def test_auth_me_no_token(self):
        """GET /api/auth/me without token should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ /api/auth/me without token returns {response.status_code}")


class TestSubscriptionEndpoint:
    """Test subscription endpoint (uses get_user_from_request helper)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_subscription(self):
        """GET /api/subscription - should return plan info"""
        response = requests.get(f"{BASE_URL}/api/subscription", headers=self.headers)
        assert response.status_code == 200, f"Subscription failed: {response.text}"
        data = response.json()
        
        # Validate response has expected fields
        assert "plan_id" in data or "subscription_id" in data, "Missing plan_id or subscription_id"
        assert "status" in data, "Missing status field"
        
        print(f"✓ GET /api/subscription returns plan_id={data.get('plan_id')}, status={data.get('status')}")


class TestDashboardEndpoint:
    """Test dashboard stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_dashboard_stats(self):
        """GET /api/dashboard/stats - should return statistics"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        # Validate expected fields
        assert "total_employees" in data, "Missing total_employees"
        
        print(f"✓ GET /api/dashboard/stats returns total_employees={data.get('total_employees')}")


class TestEmployeesEndpoint:
    """Test employees endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_employees(self):
        """GET /api/employees - should return list of employees"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=self.headers)
        assert response.status_code == 200, f"Employees failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list"
        print(f"✓ GET /api/employees returns {len(data)} employees")


class TestLoansEndpoint:
    """Test loans endpoint (uses get_user_from_request helper)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_loans(self):
        """GET /api/loans - should return loans"""
        response = requests.get(f"{BASE_URL}/api/loans", headers=self.headers)
        assert response.status_code == 200, f"Loans failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list"
        print(f"✓ GET /api/loans returns {len(data)} loans")


class TestRolesEndpoint:
    """Test roles endpoint (uses get_user_from_request helper)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_roles(self):
        """GET /api/roles - should return roles"""
        response = requests.get(f"{BASE_URL}/api/roles", headers=self.headers)
        assert response.status_code == 200, f"Roles failed: {response.text}"
        data = response.json()
        
        # Roles endpoint returns dict with roles array
        assert isinstance(data, dict), "Should return a dict"
        print(f"✓ GET /api/roles returns response with is_enterprise={data.get('is_enterprise')}")


class TestDocumentsEndpoint:
    """Test documents endpoint (uses get_user_from_request helper)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_document_templates(self):
        """GET /api/doc-generator/templates - should return templates"""
        response = requests.get(f"{BASE_URL}/api/doc-generator/templates", headers=self.headers)
        assert response.status_code == 200, f"Documents failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list"
        print(f"✓ GET /api/doc-generator/templates returns {len(data)} templates")


class TestPartnerEndpoints:
    """Test partner endpoints with partner token"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get partner auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_USER_EMAIL,
            "password": PARTNER_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Partner authentication failed")
    
    def test_partner_dashboard(self):
        """GET /api/partners/dashboard - should return partner dashboard data"""
        response = requests.get(f"{BASE_URL}/api/partners/dashboard", headers=self.headers)
        assert response.status_code == 200, f"Partner dashboard failed: {response.text}"
        data = response.json()
        
        assert "firm" in data, "Should have firm info"
        assert "statistics" in data, "Should have statistics"
        print(f"✓ GET /api/partners/dashboard returns firm={data['firm'].get('name')}")
    
    def test_partner_clients(self):
        """GET /api/partners/clients - should return partner's clients"""
        response = requests.get(f"{BASE_URL}/api/partners/clients", headers=self.headers)
        assert response.status_code == 200, f"Partner clients failed: {response.text}"
        data = response.json()
        
        assert "clients" in data, "Should have clients array"
        assert "total" in data, "Should have total count"
        print(f"✓ GET /api/partners/clients returns {data.get('total')} clients")
    
    def test_partner_plans(self):
        """GET /api/partners/plans - should return available plans"""
        response = requests.get(f"{BASE_URL}/api/partners/plans", headers=self.headers)
        assert response.status_code == 200, f"Partner plans failed: {response.text}"
        data = response.json()
        
        assert "plans" in data, "Should have plans array"
        print(f"✓ GET /api/partners/plans returns {len(data.get('plans', []))} plans")


class TestPlansEndpoint:
    """Test public plans endpoint - no auth required"""
    
    def test_get_plans(self):
        """GET /api/plans - should return subscription plans"""
        response = requests.get(f"{BASE_URL}/api/plans")
        assert response.status_code == 200, f"Plans failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list"
        assert len(data) > 0, "Should have plans"
        
        # Validate first plan structure
        plan = data[0]
        assert "plan_id" in plan, "Plan should have plan_id"
        assert "name" in plan, "Plan should have name"
        
        print(f"✓ GET /api/plans returns {len(data)} plans")


class TestGeolocationAttendanceEndpoint:
    """Test geolocation attendance endpoints (uses get_user_from_request helper)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_geo_locations(self):
        """GET /api/geo-attendance/locations - should return locations"""
        response = requests.get(f"{BASE_URL}/api/geolocation-attendance/locations", headers=self.headers)
        assert response.status_code == 200, f"Geo locations failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list"
        print(f"✓ GET /api/geolocation-attendance/locations returns {len(data)} locations")


class TestBankFilesEndpoint:
    """Test bank files endpoints (uses get_user_from_request helper)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_bank_list(self):
        """GET /api/bank-files/banks - should return available banks"""
        response = requests.get(f"{BASE_URL}/api/bank-files/banks", headers=self.headers)
        assert response.status_code == 200, f"Bank list failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list"
        assert len(data) > 0, "Should have banks"
        print(f"✓ GET /api/bank-files/banks returns {len(data)} banks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
