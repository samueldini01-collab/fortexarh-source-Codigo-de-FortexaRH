"""
Test Partner Portal for Accounting Firms - FortexaRH
Tests partner registration, dashboard, client management, and commissions APIs
"""
import pytest
import requests
import os
import secrets

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_PARTNER_EMAIL = "testpartner@test.com"
TEST_PARTNER_PASSWORD = "test123"
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"


class TestPartnerRegistration:
    """Test partner registration endpoint"""
    
    def test_register_new_partner_success(self):
        """Test successful registration of a new accounting firm"""
        unique_id = secrets.token_hex(4)
        response = requests.post(
            f"{BASE_URL}/api/partners/register",
            json={
                "firm_name": f"Test Firm {unique_id}",
                "contact_name": "Test Contact",
                "email": f"testfirm{unique_id}@test.com",
                "phone": "809-555-1234",
                "password": "test123"
            }
        )
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "partner_id" in data
        assert "company_id" in data
        assert "referral_code" in data
        assert "referral_link" in data
        assert "trial_days" in data
        assert data["trial_days"] == 14
        assert data["partner_id"].startswith("partner_")
        assert data["company_id"].startswith("company_")
    
    def test_register_duplicate_email_fails(self):
        """Test that registering with existing email fails"""
        response = requests.post(
            f"{BASE_URL}/api/partners/register",
            json={
                "firm_name": "Duplicate Test Firm",
                "contact_name": "Test Contact",
                "email": TEST_PARTNER_EMAIL,  # Already exists
                "phone": "809-555-1234",
                "password": "test123"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "correo" in data["detail"].lower() or "registrado" in data["detail"].lower()
    
    def test_register_missing_required_fields(self):
        """Test that registration fails with missing required fields"""
        response = requests.post(
            f"{BASE_URL}/api/partners/register",
            json={
                "firm_name": "Test Firm",
                # Missing contact_name, email, phone, password
            }
        )
        assert response.status_code == 422  # Validation error


class TestPartnerLogin:
    """Test partner login functionality"""
    
    def test_partner_login_success(self):
        """Test successful login with partner credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_PARTNER_EMAIL, "password": TEST_PARTNER_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_PARTNER_EMAIL
        assert data["user"]["role"] == "partner_admin"
    
    def test_partner_login_invalid_password(self):
        """Test login with invalid password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_PARTNER_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code in [401, 400]


@pytest.fixture(scope="module")
def partner_token():
    """Get authentication token for partner tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_PARTNER_EMAIL, "password": TEST_PARTNER_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Partner authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def partner_headers(partner_token):
    """Get headers with partner authentication token"""
    return {
        "Authorization": f"Bearer {partner_token}",
        "Content-Type": "application/json"
    }


class TestPartnerDashboard:
    """Test partner dashboard endpoint"""
    
    def test_get_dashboard_authenticated(self, partner_headers):
        """Test getting dashboard data with authentication"""
        response = requests.get(
            f"{BASE_URL}/api/partners/dashboard",
            headers=partner_headers
        )
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        
        # Verify firm info
        assert "firm" in data
        assert "name" in data["firm"]
        assert "referral_code" in data["firm"]
        assert "referral_link" in data["firm"]
        assert "status" in data["firm"]
        assert "subscription_status" in data["firm"]
        
        # Verify statistics
        assert "statistics" in data
        assert "total_clients" in data["statistics"]
        assert "active_clients" in data["statistics"]
        assert "trial_clients" in data["statistics"]
        
        # Verify commissions
        assert "commissions" in data
        assert "total_earned" in data["commissions"]
        assert "total_paid" in data["commissions"]
        assert "pending" in data["commissions"]
        assert "commission_rate" in data["commissions"]
        assert data["commissions"]["commission_rate"] == "30.0%"
        
        # Verify benefits
        assert "benefits" in data
        assert "has_benefits" in data["benefits"]
        
        # Verify pricing
        assert "pricing" in data
        
        # Verify recent clients
        assert "recent_clients" in data
        assert isinstance(data["recent_clients"], list)
    
    def test_get_dashboard_unauthenticated(self):
        """Test that dashboard without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/partners/dashboard")
        assert response.status_code == 401


class TestPartnerClients:
    """Test partner client management endpoints"""
    
    def test_get_clients_list(self, partner_headers):
        """Test getting list of partner clients"""
        response = requests.get(
            f"{BASE_URL}/api/partners/clients",
            headers=partner_headers
        )
        assert response.status_code == 200, f"Get clients failed: {response.text}"
        
        data = response.json()
        assert "clients" in data
        assert "total" in data
        assert "limit" in data
        assert "skip" in data
        assert isinstance(data["clients"], list)
    
    def test_add_client_success(self, partner_headers):
        """Test adding a new client"""
        unique_id = secrets.token_hex(4)
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            headers=partner_headers,
            json={
                "company_name": f"Test Client {unique_id}",
                "contact_name": "Test Contact",
                "email": f"client{unique_id}@test.com",
                "phone": "809-111-2222",
                "billing_type": "direct"
            }
        )
        assert response.status_code == 200, f"Add client failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "client_id" in data
        assert "invitation_link" in data
        assert "invitation_code" in data
        assert data["client_id"].startswith("client_")
    
    def test_add_client_duplicate_email_fails(self, partner_headers):
        """Test that adding client with existing email fails"""
        # First add a client
        unique_id = secrets.token_hex(4)
        email = f"duplicate{unique_id}@test.com"
        
        requests.post(
            f"{BASE_URL}/api/partners/clients",
            headers=partner_headers,
            json={
                "company_name": "First Client",
                "contact_name": "Test",
                "email": email,
                "billing_type": "direct"
            }
        )
        
        # Try to add again with same email
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            headers=partner_headers,
            json={
                "company_name": "Second Client",
                "contact_name": "Test",
                "email": email,
                "billing_type": "direct"
            }
        )
        assert response.status_code == 400
    
    def test_add_client_with_firm_billing(self, partner_headers):
        """Test adding client with firm billing type"""
        unique_id = secrets.token_hex(4)
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            headers=partner_headers,
            json={
                "company_name": f"Firm Billing Client {unique_id}",
                "contact_name": "Test Contact",
                "email": f"firmbilling{unique_id}@test.com",
                "billing_type": "firm"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "client_id" in data
    
    def test_get_clients_unauthenticated(self):
        """Test that getting clients without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/partners/clients")
        assert response.status_code == 401
    
    def test_add_client_unauthenticated(self):
        """Test that adding client without auth returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            json={
                "company_name": "Test",
                "contact_name": "Test",
                "email": "test@test.com",
                "billing_type": "direct"
            }
        )
        assert response.status_code == 401


class TestPartnerCommissions:
    """Test partner commissions endpoints"""
    
    def test_get_commissions_list(self, partner_headers):
        """Test getting list of commissions"""
        response = requests.get(
            f"{BASE_URL}/api/partners/commissions",
            headers=partner_headers
        )
        assert response.status_code == 200, f"Get commissions failed: {response.text}"
        
        data = response.json()
        assert "commissions" in data
        assert "totals" in data
        assert "commission_rate" in data
        assert data["commission_rate"] == "30.0%"
        assert isinstance(data["commissions"], list)
    
    def test_get_commissions_with_status_filter(self, partner_headers):
        """Test getting commissions with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/partners/commissions",
            params={"status": "pending"},
            headers=partner_headers
        )
        assert response.status_code == 200
    
    def test_get_commissions_with_month_filter(self, partner_headers):
        """Test getting commissions with month filter"""
        response = requests.get(
            f"{BASE_URL}/api/partners/commissions",
            params={"month": "2026-01"},
            headers=partner_headers
        )
        assert response.status_code == 200
    
    def test_get_commissions_summary(self, partner_headers):
        """Test getting commissions summary"""
        response = requests.get(
            f"{BASE_URL}/api/partners/commissions/summary",
            headers=partner_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "monthly_breakdown" in data
        assert "commission_rate" in data
        assert data["commission_rate"] == 0.30
    
    def test_get_commissions_unauthenticated(self):
        """Test that getting commissions without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/partners/commissions")
        assert response.status_code == 401


class TestPartnerSubscription:
    """Test partner subscription endpoint"""
    
    def test_get_subscription_status(self, partner_headers):
        """Test getting subscription status"""
        response = requests.get(
            f"{BASE_URL}/api/partners/subscription",
            headers=partner_headers
        )
        assert response.status_code == 200, f"Get subscription failed: {response.text}"
        
        data = response.json()
        assert "subscription_status" in data
        assert "subscription_plan" in data
        assert "benefits" in data
        assert "pricing" in data
        assert "requirements" in data
        
        # Verify requirements structure
        assert "minimum_active_clients" in data["requirements"]
        assert data["requirements"]["minimum_active_clients"] == 1
        assert "grace_period_days" in data["requirements"]


class TestPartnerReferral:
    """Test partner referral endpoint"""
    
    def test_get_referral_info(self, partner_headers):
        """Test getting referral information"""
        response = requests.get(
            f"{BASE_URL}/api/partners/referral",
            headers=partner_headers
        )
        assert response.status_code == 200, f"Get referral failed: {response.text}"
        
        data = response.json()
        assert "referral_code" in data
        assert "referral_link" in data
        assert "statistics" in data
        assert "commission_info" in data
        
        # Verify statistics structure
        assert "total_referrals" in data["statistics"]
        assert "converted" in data["statistics"]
        assert "conversion_rate" in data["statistics"]
        
        # Verify commission info
        assert data["commission_info"]["rate"] == "30.0%"


class TestNonPartnerAccess:
    """Test that non-partner users cannot access partner endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin user headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Admin authentication failed")
    
    def test_non_partner_cannot_access_dashboard(self, admin_headers):
        """Test that non-partner user cannot access partner dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/partners/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
    
    def test_non_partner_cannot_access_clients(self, admin_headers):
        """Test that non-partner user cannot access partner clients"""
        response = requests.get(
            f"{BASE_URL}/api/partners/clients",
            headers=admin_headers
        )
        assert response.status_code == 403
    
    def test_non_partner_cannot_add_client(self, admin_headers):
        """Test that non-partner user cannot add partner client"""
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            headers=admin_headers,
            json={
                "company_name": "Test",
                "contact_name": "Test",
                "email": "test@test.com",
                "billing_type": "direct"
            }
        )
        assert response.status_code == 403
