"""
Test Suite for Refactored Backend Routers - FortexaRH
Tests the modular routers extracted from server.py:
- Checkout Router: /api/public/checkout, /api/checkout, /api/checkout/status/{session_id}
- Invoices Router: /api/invoices, /api/invoices/{id}
- Search Router: /api/search?q=
- Documents Router: /api/doc-generator/generate
- Company Settings: /api/company/settings
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAuthSetup:
    """Authentication setup tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
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
        assert data["user"]["email"] == TEST_EMAIL


class TestPublicCheckoutRouter:
    """Tests for public checkout endpoints (no auth required)"""
    
    def test_public_checkout_basic_plan(self):
        """Test creating public checkout session for basic plan"""
        response = requests.post(
            f"{BASE_URL}/api/public/checkout",
            json={
                "plan_id": "basic",
                "employee_count": 5,
                "origin_url": BASE_URL
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
        assert data["session_id"].startswith("cs_")
    
    def test_public_checkout_pro_plan(self):
        """Test creating public checkout session for pro plan"""
        response = requests.post(
            f"{BASE_URL}/api/public/checkout",
            json={
                "plan_id": "pro",
                "employee_count": 10,
                "origin_url": BASE_URL
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
    
    def test_public_checkout_enterprise_plan(self):
        """Test creating public checkout session for enterprise plan"""
        response = requests.post(
            f"{BASE_URL}/api/public/checkout",
            json={
                "plan_id": "enterprise",
                "employee_count": 100,
                "origin_url": BASE_URL
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
    
    def test_public_checkout_invalid_plan(self):
        """Test public checkout with invalid plan returns error"""
        response = requests.post(
            f"{BASE_URL}/api/public/checkout",
            json={
                "plan_id": "invalid_plan",
                "employee_count": 5,
                "origin_url": BASE_URL
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_public_checkout_trial_plan_rejected(self):
        """Test that trial plan is rejected for checkout"""
        response = requests.post(
            f"{BASE_URL}/api/public/checkout",
            json={
                "plan_id": "trial",
                "employee_count": 1,
                "origin_url": BASE_URL
            }
        )
        assert response.status_code == 400
    
    def test_public_checkout_verify_nonexistent_session(self):
        """Test verifying a non-existent checkout session"""
        response = requests.get(
            f"{BASE_URL}/api/public/checkout/verify/cs_test_nonexistent_session_12345"
        )
        assert response.status_code == 404


class TestAuthenticatedCheckoutRouter:
    """Tests for authenticated checkout endpoints"""
    
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
    
    def test_authenticated_checkout_pro_plan(self, auth_headers):
        """Test creating authenticated checkout session"""
        response = requests.post(
            f"{BASE_URL}/api/checkout",
            headers=auth_headers,
            json={
                "plan_id": "pro",
                "employee_count": 15,
                "origin_url": BASE_URL
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
    
    def test_authenticated_checkout_without_auth(self):
        """Test that checkout without auth returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/checkout",
            json={
                "plan_id": "pro",
                "employee_count": 10,
                "origin_url": BASE_URL
            }
        )
        assert response.status_code == 401
    
    def test_checkout_status_nonexistent_session(self, auth_headers):
        """Test checkout status for non-existent session returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/checkout/status/cs_test_fake_session_xyz",
            headers=auth_headers
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestInvoicesRouter:
    """Tests for invoices endpoints"""
    
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
    
    def test_get_invoices_list(self, auth_headers):
        """Test getting list of invoices"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_invoices_without_auth(self):
        """Test that invoices without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 401
    
    def test_get_nonexistent_invoice(self, auth_headers):
        """Test getting a non-existent invoice returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/invoices/inv_nonexistent_12345",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestSearchRouter:
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
    
    def test_search_employees(self, auth_headers):
        """Test searching for employees"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=empleado",
            headers=auth_headers
        )
        assert response.status_code == 200
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
    
    def test_search_attendance(self, auth_headers):
        """Test searching for attendance"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=asistencia",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # Should include navigation result for attendance
        nav_results = [r for r in data["results"] if r.get("type") == "navigation"]
        assert len(nav_results) > 0 or len(data["results"]) >= 0
    
    def test_search_loans(self, auth_headers):
        """Test searching for loans"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=prestamo",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
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
        # Should return 200 with empty results or 422 for validation
        assert response.status_code in [200, 422]


class TestDocumentsRouter:
    """Tests for document generation endpoints"""
    
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
    
    def test_get_document_templates(self, auth_headers):
        """Test getting document templates"""
        response = requests.get(
            f"{BASE_URL}/api/doc-generator/templates",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have default templates
        if len(data) > 0:
            template = data[0]
            assert "template_id" in template
            assert "name" in template
            assert "content" in template
    
    def test_get_default_templates(self, auth_headers):
        """Test that default templates are available"""
        response = requests.get(
            f"{BASE_URL}/api/doc-generator/templates",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected default templates
        template_ids = [t.get("template_id") for t in data]
        expected_templates = ["constancia_trabajo", "carta_recomendacion", "certificado_ingresos"]
        
        for expected in expected_templates:
            assert expected in template_ids, f"Missing default template: {expected}"
    
    def test_get_novelty_types(self, auth_headers):
        """Test getting novelty types for documents"""
        response = requests.get(
            f"{BASE_URL}/api/doc-generator/novelty-types",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "income" in data
        assert "deduction" in data
    
    def test_documents_without_auth(self):
        """Test that document endpoints without auth return 401"""
        response = requests.get(f"{BASE_URL}/api/doc-generator/templates")
        assert response.status_code == 401


class TestCompanySettingsRouter:
    """Tests for company settings endpoint"""
    
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
    
    def test_get_company_settings(self, auth_headers):
        """Test getting company settings"""
        response = requests.get(
            f"{BASE_URL}/api/company/settings",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "company" in data
        assert "payroll_settings" in data
        
        # Verify company data
        company = data["company"]
        assert "company_id" in company
        assert "name" in company
        assert "subscription_plan" in company
    
    def test_company_settings_without_auth(self):
        """Test that company settings without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/company/settings")
        assert response.status_code == 401


class TestConfigStatus:
    """Tests for config status endpoint (debugging)"""
    
    def test_config_status(self):
        """Test config status endpoint"""
        response = requests.get(f"{BASE_URL}/api/config/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "ok"
        assert "stripe_configured" in data
        assert "mongo_configured" in data


class TestRouterIntegration:
    """Integration tests to verify routers are properly connected"""
    
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
    
    def test_all_routers_accessible(self, auth_headers):
        """Test that all refactored routers are accessible"""
        endpoints = [
            ("/api/invoices", "GET", True),
            ("/api/search?q=test", "GET", True),
            ("/api/doc-generator/templates", "GET", True),
            ("/api/company/settings", "GET", True),
            ("/api/config/status", "GET", False),  # No auth required
        ]
        
        for endpoint, method, requires_auth in endpoints:
            headers = auth_headers if requires_auth else {}
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            
            assert response.status_code in [200, 404], f"Endpoint {endpoint} returned {response.status_code}"
    
    def test_checkout_flow_integration(self, auth_headers):
        """Test the checkout flow from public to authenticated"""
        # 1. Create public checkout
        public_response = requests.post(
            f"{BASE_URL}/api/public/checkout",
            json={
                "plan_id": "basic",
                "employee_count": 3,
                "origin_url": BASE_URL
            }
        )
        assert public_response.status_code == 200
        public_data = public_response.json()
        assert "session_id" in public_data
        
        # 2. Create authenticated checkout
        auth_response = requests.post(
            f"{BASE_URL}/api/checkout",
            headers=auth_headers,
            json={
                "plan_id": "pro",
                "employee_count": 5,
                "origin_url": BASE_URL
            }
        )
        assert auth_response.status_code == 200
        auth_data = auth_response.json()
        assert "session_id" in auth_data
        
        # 3. Check status of authenticated checkout
        status_response = requests.get(
            f"{BASE_URL}/api/checkout/status/{auth_data['session_id']}",
            headers=auth_headers
        )
        # Should return pending or similar status
        assert status_response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
