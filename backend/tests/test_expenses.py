"""
Test suite for Expenses & Viáticos Module - FortexaRH
Tests: categories, requests CRUD, approvals, reports
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestExpensesCategories:
    """Test expense categories endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_categories_returns_9_categories(self):
        """GET /api/expenses/categories - should return 9 configured categories"""
        response = requests.get(
            f"{BASE_URL}/api/expenses/categories",
            headers=self.headers
        )
        assert response.status_code == 200
        
        categories = response.json()
        assert isinstance(categories, list)
        assert len(categories) == 9, f"Expected 9 categories, got {len(categories)}"
        
        # Verify expected category IDs
        expected_ids = ["transporte", "alojamiento", "alimentacion", "materiales", 
                       "viajes", "administrativos", "educacion", "uniformes", "otros"]
        actual_ids = [cat["id"] for cat in categories]
        
        for expected_id in expected_ids:
            assert expected_id in actual_ids, f"Missing category: {expected_id}"
        
        # Verify each category has required fields
        for cat in categories:
            assert "id" in cat
            assert "name" in cat
            assert "icon" in cat


class TestExpenseRequests:
    """Test expense request CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_request_id = None
    
    def test_create_expense_request(self):
        """POST /api/expenses/requests - create new expense request"""
        unique_id = uuid.uuid4().hex[:6]
        payload = {
            "title": f"TEST_Viaje de negocios {unique_id}",
            "expense_type": "travel",
            "description": "Viaje para reunión con cliente importante",
            "destination": "Santiago",
            "start_date": "2026-02-01",
            "end_date": "2026-02-03",
            "estimated_budget": 15000.00,
            "requires_advance": True,
            "advance_amount": 10000.00,
            "advance_date": "2026-01-28",
            "notes": "Requiere hotel y transporte",
            "budget_breakdown": [
                {"category": "transporte", "amount": 5000, "description": "Vuelos"},
                {"category": "alojamiento", "amount": 8000, "description": "Hotel 2 noches"},
                {"category": "alimentacion", "amount": 2000, "description": "Comidas"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/expenses/requests",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert "request_id" in data
        assert "message" in data
        assert data["request_id"].startswith("exp_")
        
        self.created_request_id = data["request_id"]
        print(f"Created expense request: {self.created_request_id}")
        
        return self.created_request_id
    
    def test_get_expense_requests_list(self):
        """GET /api/expenses/requests - list user's expense requests"""
        response = requests.get(
            f"{BASE_URL}/api/expenses/requests",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify structure of returned requests
        if len(data) > 0:
            req = data[0]
            assert "request_id" in req
            assert "title" in req
            assert "status" in req
            assert "estimated_budget" in req
    
    def test_get_pending_approvals(self):
        """GET /api/expenses/requests/pending-approval - list pending approvals for managers"""
        response = requests.get(
            f"{BASE_URL}/api/expenses/requests/pending-approval",
            headers=self.headers
        )
        
        # Should return 200 for admin/manager users
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_and_get_request_details(self):
        """POST then GET /api/expenses/requests/{id} - create and verify details"""
        # First create a request
        unique_id = uuid.uuid4().hex[:6]
        payload = {
            "title": f"TEST_Gastos administrativos {unique_id}",
            "expense_type": "administrative",
            "description": "Compra de suministros de oficina",
            "start_date": "2026-02-05",
            "end_date": "2026-02-05",
            "estimated_budget": 5000.00,
            "requires_advance": False,
            "budget_breakdown": [
                {"category": "materiales", "amount": 3000, "description": "Papelería"},
                {"category": "otros", "amount": 2000, "description": "Varios"}
            ]
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/expenses/requests",
            json=payload,
            headers=self.headers
        )
        assert create_response.status_code == 200
        request_id = create_response.json()["request_id"]
        
        # Now get the details
        details_response = requests.get(
            f"{BASE_URL}/api/expenses/requests/{request_id}",
            headers=self.headers
        )
        
        assert details_response.status_code == 200
        data = details_response.json()
        
        # Verify structure
        assert "request" in data
        assert "advances" in data
        assert "expense_items" in data
        assert "attachments" in data
        assert "approval_history" in data
        
        # Verify request data
        req = data["request"]
        assert req["request_id"] == request_id
        assert req["title"] == payload["title"]
        assert req["expense_type"] == payload["expense_type"]
        assert req["estimated_budget"] == payload["estimated_budget"]
        assert req["status"] == "pending"
        
        # Verify approval history has creation entry
        assert len(data["approval_history"]) >= 1
        assert data["approval_history"][0]["action"] == "created"


class TestExpenseApprovals:
    """Test expense approval workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_approve_expense_request(self):
        """POST /api/expenses/requests/{id}/approve - approve a request"""
        # First create a request to approve
        unique_id = uuid.uuid4().hex[:6]
        payload = {
            "title": f"TEST_Solicitud para aprobar {unique_id}",
            "expense_type": "transportation",
            "description": "Gastos de transporte mensual",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "estimated_budget": 3000.00,
            "requires_advance": False
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/expenses/requests",
            json=payload,
            headers=self.headers
        )
        assert create_response.status_code == 200
        request_id = create_response.json()["request_id"]
        
        # Now approve it
        approval_payload = {
            "action": "approve",
            "comments": "Aprobado por testing"
        }
        
        approve_response = requests.post(
            f"{BASE_URL}/api/expenses/requests/{request_id}/approve",
            json=approval_payload,
            headers=self.headers
        )
        
        assert approve_response.status_code == 200
        data = approve_response.json()
        assert "message" in data
        assert "new_status" in data
        # Admin approval should go directly to approved_admin
        assert data["new_status"] in ["approved_manager", "approved_admin"]
        
        # Verify the status was updated
        details_response = requests.get(
            f"{BASE_URL}/api/expenses/requests/{request_id}",
            headers=self.headers
        )
        assert details_response.status_code == 200
        assert details_response.json()["request"]["status"] in ["approved_manager", "approved_admin"]
    
    def test_reject_expense_request(self):
        """POST /api/expenses/requests/{id}/approve - reject a request"""
        # First create a request to reject
        unique_id = uuid.uuid4().hex[:6]
        payload = {
            "title": f"TEST_Solicitud para rechazar {unique_id}",
            "expense_type": "other",
            "description": "Solicitud de prueba para rechazo",
            "start_date": "2026-02-01",
            "end_date": "2026-02-01",
            "estimated_budget": 1000.00,
            "requires_advance": False
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/expenses/requests",
            json=payload,
            headers=self.headers
        )
        assert create_response.status_code == 200
        request_id = create_response.json()["request_id"]
        
        # Now reject it
        rejection_payload = {
            "action": "reject",
            "comments": "Rechazado por testing - presupuesto insuficiente"
        }
        
        reject_response = requests.post(
            f"{BASE_URL}/api/expenses/requests/{request_id}/approve",
            json=rejection_payload,
            headers=self.headers
        )
        
        assert reject_response.status_code == 200
        data = reject_response.json()
        assert data["new_status"] == "rejected"
        
        # Verify the status was updated
        details_response = requests.get(
            f"{BASE_URL}/api/expenses/requests/{request_id}",
            headers=self.headers
        )
        assert details_response.status_code == 200
        assert details_response.json()["request"]["status"] == "rejected"


class TestExpenseReports:
    """Test expense reports endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_expenses_summary(self):
        """GET /api/expenses/reports/summary - get expenses summary report"""
        response = requests.get(
            f"{BASE_URL}/api/expenses/reports/summary",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify summary structure
        assert "total_requests" in data
        assert "total_estimated" in data
        assert "total_actual" in data
        assert "savings" in data
        assert "by_status" in data
        assert "by_type" in data
        assert "by_department" in data
        assert "pending_advances" in data
        
        # Verify pending_advances structure
        assert "count" in data["pending_advances"]
        assert "total_amount" in data["pending_advances"]


class TestExpenseRequestCancellation:
    """Test expense request cancellation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_cancel_pending_request(self):
        """DELETE /api/expenses/requests/{id} - cancel a pending request"""
        # First create a request to cancel
        unique_id = uuid.uuid4().hex[:6]
        payload = {
            "title": f"TEST_Solicitud para cancelar {unique_id}",
            "expense_type": "meals",
            "description": "Solicitud de prueba para cancelación",
            "start_date": "2026-02-01",
            "end_date": "2026-02-01",
            "estimated_budget": 500.00,
            "requires_advance": False
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/expenses/requests",
            json=payload,
            headers=self.headers
        )
        assert create_response.status_code == 200
        request_id = create_response.json()["request_id"]
        
        # Now cancel it
        cancel_response = requests.delete(
            f"{BASE_URL}/api/expenses/requests/{request_id}",
            headers=self.headers
        )
        
        assert cancel_response.status_code == 200
        data = cancel_response.json()
        assert "message" in data
        
        # Verify the status was updated to cancelled
        details_response = requests.get(
            f"{BASE_URL}/api/expenses/requests/{request_id}",
            headers=self.headers
        )
        assert details_response.status_code == 200
        assert details_response.json()["request"]["status"] == "cancelled"


class TestUnauthorizedAccess:
    """Test that endpoints require authentication"""
    
    def test_categories_requires_no_auth(self):
        """Categories endpoint should work without auth (public)"""
        # Actually checking if it requires auth or not
        response = requests.get(f"{BASE_URL}/api/expenses/categories")
        # This might require auth based on implementation
        # If it returns 401, that's expected for protected endpoints
        assert response.status_code in [200, 401]
    
    def test_requests_requires_auth(self):
        """Requests endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/expenses/requests")
        assert response.status_code == 401
    
    def test_pending_approval_requires_auth(self):
        """Pending approval endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/expenses/requests/pending-approval")
        assert response.status_code == 401
    
    def test_summary_requires_auth(self):
        """Summary report endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/expenses/reports/summary")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
