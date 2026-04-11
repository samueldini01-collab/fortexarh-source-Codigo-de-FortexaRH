"""
Super Admin API Tests - FortexaRH
Tests for the Super Admin panel endpoints:
- Login with correct/wrong credentials
- Companies list with employee_count and user_count
- Stats endpoint with KPIs
- Activate/Deactivate company flows
- Events endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Super Admin credentials
SA_USERNAME = "fortexa2026rd"
SA_PASSWORD = "FortexaAdmin2026!"


class TestSuperAdminLogin:
    """Super Admin login endpoint tests"""
    
    def test_login_success(self):
        """POST /api/super-admin/login with correct credentials should return token"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "username": SA_USERNAME,
            "password": SA_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert "role" in data, "Response should contain role"
        assert data["role"] == "super_admin", f"Role should be super_admin, got {data['role']}"
        assert data["user"] == SA_USERNAME, f"User should be {SA_USERNAME}, got {data['user']}"
        assert len(data["token"]) > 0, "Token should not be empty"
        print(f"✓ Login successful, token length: {len(data['token'])}")
    
    def test_login_wrong_username(self):
        """POST /api/super-admin/login with wrong username should return 401"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "username": "wronguser",
            "password": SA_PASSWORD
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Wrong username correctly rejected with 401")
    
    def test_login_wrong_password(self):
        """POST /api/super-admin/login with wrong password should return 401"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "username": SA_USERNAME,
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Wrong password correctly rejected with 401")
    
    def test_login_empty_credentials(self):
        """POST /api/super-admin/login with empty credentials should fail"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "username": "",
            "password": ""
        })
        assert response.status_code in [401, 422], f"Expected 401 or 422, got {response.status_code}"
        print("✓ Empty credentials correctly rejected")


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


class TestSuperAdminCompanies:
    """Super Admin companies endpoint tests"""
    
    def test_get_companies_authenticated(self, sa_headers):
        """GET /api/super-admin/companies should return list of companies"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Got {len(data)} companies")
        
        if len(data) > 0:
            company = data[0]
            # Verify enriched fields
            assert "employee_count" in company, "Company should have employee_count"
            assert "user_count" in company, "Company should have user_count"
            assert "company_id" in company, "Company should have company_id"
            assert isinstance(company["employee_count"], int), "employee_count should be int"
            assert isinstance(company["user_count"], int), "user_count should be int"
            print(f"✓ First company: {company.get('name', company.get('company_id'))}, employees: {company['employee_count']}, users: {company['user_count']}")
    
    def test_get_companies_unauthenticated(self):
        """GET /api/super-admin/companies without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated request correctly rejected")
    
    def test_get_companies_invalid_token(self):
        """GET /api/super-admin/companies with invalid token should return 401"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid token correctly rejected")


class TestSuperAdminStats:
    """Super Admin stats endpoint tests"""
    
    def test_get_stats(self, sa_headers):
        """GET /api/super-admin/stats should return platform statistics"""
        response = requests.get(f"{BASE_URL}/api/super-admin/stats", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert "total_companies" in data, "Stats should have total_companies"
        assert "active_companies" in data, "Stats should have active_companies"
        assert "inactive_companies" in data, "Stats should have inactive_companies"
        assert "total_employees" in data, "Stats should have total_employees"
        assert "total_users" in data, "Stats should have total_users"
        assert "by_payment_method" in data, "Stats should have by_payment_method"
        
        # Verify types
        assert isinstance(data["total_companies"], int), "total_companies should be int"
        assert isinstance(data["active_companies"], int), "active_companies should be int"
        assert isinstance(data["inactive_companies"], int), "inactive_companies should be int"
        assert isinstance(data["total_employees"], int), "total_employees should be int"
        assert isinstance(data["total_users"], int), "total_users should be int"
        assert isinstance(data["by_payment_method"], dict), "by_payment_method should be dict"
        
        print(f"✓ Stats: {data['total_companies']} companies ({data['active_companies']} active, {data['inactive_companies']} inactive)")
        print(f"✓ Stats: {data['total_employees']} employees, {data['total_users']} users")
        print(f"✓ Payment methods: {data['by_payment_method']}")


class TestSuperAdminActivation:
    """Super Admin company activation/deactivation tests"""
    
    def test_activate_company(self, sa_headers):
        """POST /api/super-admin/companies/{id}/activate should activate company"""
        # First get a company to activate
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert companies_response.status_code == 200
        companies = companies_response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available to test activation")
        
        # Find an inactive company or use the first one
        target_company = None
        for c in companies:
            if c.get("status") != "active":
                target_company = c
                break
        
        if not target_company:
            target_company = companies[0]  # Use first company if all are active
        
        company_id = target_company["company_id"]
        company_name = target_company.get("name", company_id)
        
        # Activate with payment method
        activate_response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/{company_id}/activate",
            headers=sa_headers,
            json={
                "payment_method": "transferencia",
                "notes": "Test activation",
                "amount": 1000
            }
        )
        assert activate_response.status_code == 200, f"Expected 200, got {activate_response.status_code}: {activate_response.text}"
        
        data = activate_response.json()
        assert "message" in data, "Response should have message"
        assert data["company_id"] == company_id, "Response should have correct company_id"
        assert data["payment_method"] == "transferencia", "Response should have correct payment_method"
        print(f"✓ Company '{company_name}' activated with transferencia")
        
        # Verify company is now active
        verify_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies_after = verify_response.json()
        activated_company = next((c for c in companies_after if c["company_id"] == company_id), None)
        assert activated_company is not None, "Company should still exist"
        assert activated_company.get("status") == "active", f"Company status should be active, got {activated_company.get('status')}"
        assert activated_company.get("payment_method") == "transferencia", f"Payment method should be transferencia"
        print(f"✓ Verified company status is now 'active' with payment_method 'transferencia'")
    
    def test_deactivate_company(self, sa_headers):
        """POST /api/super-admin/companies/{id}/deactivate should deactivate company"""
        # First get companies
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert companies_response.status_code == 200
        companies = companies_response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available to test deactivation")
        
        # Find an active company
        target_company = None
        for c in companies:
            if c.get("status") == "active":
                target_company = c
                break
        
        if not target_company:
            pytest.skip("No active companies to deactivate")
        
        company_id = target_company["company_id"]
        company_name = target_company.get("name", company_id)
        
        # Deactivate
        deactivate_response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/{company_id}/deactivate",
            headers=sa_headers
        )
        assert deactivate_response.status_code == 200, f"Expected 200, got {deactivate_response.status_code}: {deactivate_response.text}"
        
        data = deactivate_response.json()
        assert "message" in data, "Response should have message"
        assert data["company_id"] == company_id, "Response should have correct company_id"
        print(f"✓ Company '{company_name}' deactivated")
        
        # Verify company is now inactive
        verify_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies_after = verify_response.json()
        deactivated_company = next((c for c in companies_after if c["company_id"] == company_id), None)
        assert deactivated_company is not None, "Company should still exist"
        assert deactivated_company.get("status") == "inactive", f"Company status should be inactive, got {deactivated_company.get('status')}"
        print(f"✓ Verified company status is now 'inactive'")
    
    def test_activate_nonexistent_company(self, sa_headers):
        """POST /api/super-admin/companies/{id}/activate with invalid ID should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/nonexistent_company_id/activate",
            headers=sa_headers,
            json={"payment_method": "tarjeta"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Nonexistent company correctly returns 404")
    
    def test_activate_with_different_payment_methods(self, sa_headers):
        """Test activation with all payment methods"""
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies = companies_response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        company_id = companies[0]["company_id"]
        payment_methods = ["tarjeta", "transferencia", "efectivo", "regalia"]
        
        for method in payment_methods:
            response = requests.post(
                f"{BASE_URL}/api/super-admin/companies/{company_id}/activate",
                headers=sa_headers,
                json={"payment_method": method}
            )
            assert response.status_code == 200, f"Activation with {method} failed: {response.text}"
            data = response.json()
            assert data["payment_method"] == method
            print(f"✓ Activation with payment method '{method}' successful")


class TestSuperAdminEvents:
    """Super Admin events endpoint tests"""
    
    def test_get_events(self, sa_headers):
        """GET /api/super-admin/events should return list of events"""
        response = requests.get(f"{BASE_URL}/api/super-admin/events?limit=50", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Got {len(data)} events")
        
        if len(data) > 0:
            event = data[0]
            # Events should have basic structure
            assert "event_type" in event or "action" in event, "Event should have event_type or action"
            print(f"✓ First event type: {event.get('event_type', event.get('action', 'unknown'))}")
    
    def test_get_events_unauthenticated(self):
        """GET /api/super-admin/events without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/super-admin/events")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated events request correctly rejected")


class TestSuperAdminActivations:
    """Super Admin activations history endpoint tests"""
    
    def test_get_activations(self, sa_headers):
        """GET /api/super-admin/activations should return activation history"""
        response = requests.get(f"{BASE_URL}/api/super-admin/activations", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Got {len(data)} activation records")
        
        if len(data) > 0:
            activation = data[0]
            assert "activation_id" in activation, "Activation should have activation_id"
            assert "company_id" in activation, "Activation should have company_id"
            assert "action" in activation, "Activation should have action"
            print(f"✓ First activation: {activation.get('action')} for {activation.get('company_name', activation.get('company_id'))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
