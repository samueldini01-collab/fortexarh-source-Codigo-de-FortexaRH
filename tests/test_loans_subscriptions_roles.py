"""
Test suite for FortexaRH Loans, Subscriptions, and Roles APIs
Tests the modular routers extracted from server.py
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://emp-alerts.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == TEST_EMAIL
        print(f"✓ Login successful for {TEST_EMAIL}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    return response.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestLoansAPI:
    """Tests for Employee Loans API - /api/loans endpoints"""
    
    def test_get_loans_summary(self, auth_headers):
        """Test GET /api/loans/summary - should return loan summary"""
        response = requests.get(f"{BASE_URL}/api/loans/summary", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_active_loans" in data, "Missing total_active_loans"
        assert "total_loaned" in data, "Missing total_loaned"
        assert "total_paid" in data, "Missing total_paid"
        assert "total_pending" in data, "Missing total_pending"
        assert "employees_with_loans" in data, "Missing employees_with_loans"
        
        print(f"✓ Loans summary: {data['total_active_loans']} active loans, ${data['total_loaned']} total")
    
    def test_get_loans_list(self, auth_headers):
        """Test GET /api/loans - should return list of loans"""
        response = requests.get(f"{BASE_URL}/api/loans", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Loans list returned {len(data)} loans")
    
    def test_get_loans_filtered_by_status(self, auth_headers):
        """Test GET /api/loans?status=active - filter by status"""
        response = requests.get(f"{BASE_URL}/api/loans?status=active", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned loans should be active
        for loan in data:
            assert loan.get("status") == "active", f"Loan {loan.get('loan_id')} is not active"
        print(f"✓ Filtered loans by status=active: {len(data)} loans")
    
    def test_loans_requires_auth(self):
        """Test that loans endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/loans")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Loans endpoint correctly requires authentication")
    
    def test_loans_summary_requires_auth(self):
        """Test that loans summary requires authentication"""
        response = requests.get(f"{BASE_URL}/api/loans/summary")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Loans summary endpoint correctly requires authentication")


class TestSubscriptionAPI:
    """Tests for Subscription API - /api/subscription endpoints"""
    
    def test_get_subscription(self, auth_headers):
        """Test GET /api/subscription - should return current subscription"""
        response = requests.get(f"{BASE_URL}/api/subscription", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "subscription_id" in data or "plan_id" in data, "Missing subscription identifier"
        assert "status" in data, "Missing status"
        assert "plan_details" in data or "plan_name" in data, "Missing plan info"
        
        print(f"✓ Subscription: plan={data.get('plan_id', data.get('plan_name'))}, status={data.get('status')}")
    
    def test_subscription_requires_auth(self):
        """Test that subscription endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscription")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Subscription endpoint correctly requires authentication")
    
    def test_check_subscription_access(self, auth_headers):
        """Test GET /api/subscription/check-access - check feature access"""
        response = requests.get(f"{BASE_URL}/api/subscription/check-access", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "has_access" in data, "Missing has_access"
        assert "status" in data, "Missing status"
        
        print(f"✓ Subscription access check: has_access={data.get('has_access')}, status={data.get('status')}")
    
    def test_get_cancellation_info(self, auth_headers):
        """Test GET /api/subscription/cancellation-info - get cancellation flow info"""
        response = requests.get(f"{BASE_URL}/api/subscription/cancellation-info", headers=auth_headers)
        # May return 404 if no active subscription
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "current_plan" in data, "Missing current_plan"
            assert "retention_offer" in data, "Missing retention_offer"
            assert "cancellation_reasons" in data, "Missing cancellation_reasons"
            print(f"✓ Cancellation info retrieved: plan={data['current_plan'].get('name')}")
        else:
            print("✓ Cancellation info: No active subscription (404 expected)")


class TestRolesAPI:
    """Tests for Custom Roles API - /api/roles endpoints (Enterprise only)"""
    
    def test_get_roles(self, auth_headers):
        """Test GET /api/roles - should return roles list"""
        response = requests.get(f"{BASE_URL}/api/roles", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "roles" in data or "is_enterprise" in data, "Missing expected fields"
        
        if data.get("is_enterprise") == False:
            print(f"✓ Roles: Not Enterprise plan - custom roles not available")
        else:
            print(f"✓ Roles: {len(data.get('roles', []))} custom roles, is_enterprise={data.get('is_enterprise')}")
    
    def test_get_available_modules(self, auth_headers):
        """Test GET /api/roles/modules - get available modules for role config"""
        response = requests.get(f"{BASE_URL}/api/roles/modules", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "modules" in data, "Missing modules"
        assert "permission_types" in data, "Missing permission_types"
        assert len(data["modules"]) > 0, "No modules returned"
        
        print(f"✓ Available modules: {len(data['modules'])} modules, permissions: {data['permission_types']}")
    
    def test_roles_requires_auth(self):
        """Test that roles endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/roles")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Roles endpoint correctly requires authentication")


class TestLoansCreateAndPayment:
    """Tests for creating loans and registering payments"""
    
    @pytest.fixture(scope="class")
    def test_employee(self, auth_headers):
        """Get or create a test employee for loan tests"""
        # First try to get existing employees
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        if response.status_code == 200:
            employees = response.json()
            if employees:
                return employees[0]
        
        # Create a test employee if none exist
        employee_data = {
            "first_name": "TEST_Loan",
            "last_name": "Employee",
            "email": f"test_loan_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
            "position": "Test Position",
            "department": "Test Department",
            "hire_date": "2024-01-01",
            "salary": 50000.0
        }
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        if response.status_code in [200, 201]:
            emp_id = response.json().get("employee_id")
            # Fetch the full employee
            response = requests.get(f"{BASE_URL}/api/employees/{emp_id}", headers=auth_headers)
            if response.status_code == 200:
                return response.json()
        
        pytest.skip("Could not get or create test employee")
    
    def test_create_loan(self, auth_headers, test_employee):
        """Test POST /api/loans - create a new loan"""
        # Check if employee already has active loan
        response = requests.get(f"{BASE_URL}/api/loans?employee_id={test_employee['employee_id']}&status=active", headers=auth_headers)
        if response.status_code == 200:
            existing_loans = response.json()
            if existing_loans:
                print(f"✓ Employee already has active loan, skipping creation")
                return existing_loans[0]
        
        loan_data = {
            "employee_id": test_employee["employee_id"],
            "amount": 5000.0,
            "interest_rate": 0,  # No interest
            "term_months": 6,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "TEST_Loan for testing",
            "deduct_from_payroll": True
        }
        
        response = requests.post(f"{BASE_URL}/api/loans", json=loan_data, headers=auth_headers)
        
        # May fail if employee already has active loan
        if response.status_code == 400 and "ya tiene un préstamo activo" in response.text:
            print("✓ Loan creation correctly rejected - employee already has active loan")
            return None
        
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        
        assert "loan_id" in data, "Missing loan_id"
        assert "monthly_payment" in data, "Missing monthly_payment"
        
        # Verify monthly payment calculation (5000 / 6 months = 833.33)
        expected_payment = round(5000.0 / 6, 2)
        assert abs(data["monthly_payment"] - expected_payment) < 1, f"Monthly payment mismatch: {data['monthly_payment']} vs {expected_payment}"
        
        print(f"✓ Loan created: {data['loan_id']}, monthly_payment=${data['monthly_payment']}")
        return data
    
    def test_get_loan_detail(self, auth_headers):
        """Test GET /api/loans/{loan_id} - get loan details"""
        # First get a loan
        response = requests.get(f"{BASE_URL}/api/loans", headers=auth_headers)
        if response.status_code != 200 or not response.json():
            pytest.skip("No loans available for detail test")
        
        loan = response.json()[0]
        loan_id = loan["loan_id"]
        
        response = requests.get(f"{BASE_URL}/api/loans/{loan_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify loan detail structure
        assert data["loan_id"] == loan_id
        assert "payment_schedule" in data, "Missing payment_schedule"
        assert "employee" in data or "employee_id" in data, "Missing employee info"
        
        print(f"✓ Loan detail retrieved: {loan_id}, schedule has {len(data.get('payment_schedule', []))} installments")
    
    def test_loan_not_found(self, auth_headers):
        """Test GET /api/loans/{loan_id} with invalid ID"""
        response = requests.get(f"{BASE_URL}/api/loans/invalid_loan_id", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid loan ID correctly returns 404")


class TestEmployeeLoans:
    """Tests for employee-specific loan endpoints"""
    
    def test_get_employee_loans(self, auth_headers):
        """Test GET /api/employees/{employee_id}/loans - get loans for specific employee"""
        # First get an employee
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        if response.status_code != 200 or not response.json():
            pytest.skip("No employees available")
        
        employee = response.json()[0]
        employee_id = employee["employee_id"]
        
        response = requests.get(f"{BASE_URL}/api/employees/{employee_id}/loans", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "loans" in data, "Missing loans"
        assert "pending_deduction" in data, "Missing pending_deduction"
        assert "total_balance" in data, "Missing total_balance"
        
        print(f"✓ Employee loans: {len(data['loans'])} loans, pending_deduction=${data['pending_deduction']}")


class TestPlansEndpoint:
    """Tests for subscription plans endpoint"""
    
    def test_get_plans(self, auth_headers):
        """Test GET /api/plans - get available subscription plans"""
        response = requests.get(f"{BASE_URL}/api/plans", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should be a list or dict of plans
        assert data, "No plans returned"
        print(f"✓ Plans endpoint returned data")


class TestDashboardStats:
    """Tests for dashboard statistics"""
    
    def test_get_dashboard_stats(self, auth_headers):
        """Test GET /api/dashboard/stats - get dashboard statistics"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify some expected fields
        assert data, "No stats returned"
        print(f"✓ Dashboard stats retrieved")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
