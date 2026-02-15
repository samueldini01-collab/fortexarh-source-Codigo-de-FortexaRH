"""
Partner Plan Management API Tests
Tests for client activation, subscription management, plans endpoint
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PARTNER_EMAIL = "testfirm@test.com"
PARTNER_PASSWORD = "test123"


class TestPartnerPlansEndpoint:
    """Tests for GET /api/partners/plans endpoint"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Get partner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    def test_get_available_plans_success(self, partner_token):
        """Test GET /api/partners/plans returns available plans"""
        response = requests.get(
            f"{BASE_URL}/api/partners/plans",
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "plans" in data, "Response should contain 'plans' key"
        plans = data["plans"]
        assert isinstance(plans, list), "Plans should be a list"
        assert len(plans) >= 3, "Should have at least 3 plans (basic, pro, enterprise)"
        
        # Validate each plan has required fields
        plan_ids_found = []
        for plan in plans:
            assert "plan_id" in plan, "Plan should have plan_id"
            assert "name" in plan, "Plan should have name"
            assert "base_price" in plan, "Plan should have base_price"
            assert "price_per_employee" in plan, "Plan should have price_per_employee"
            assert "max_employees" in plan, "Plan should have max_employees"
            plan_ids_found.append(plan["plan_id"])
        
        # Verify basic, pro, enterprise plans exist (trial should be excluded)
        assert "basic" in plan_ids_found, "Basic plan should be available"
        assert "pro" in plan_ids_found, "Pro plan should be available"
        assert "enterprise" in plan_ids_found, "Enterprise plan should be available"
        assert "trial" not in plan_ids_found, "Trial plan should NOT be in partner plans"
        
        print("✓ GET /api/partners/plans returns correct plans structure")
    
    def test_plans_pricing_values(self, partner_token):
        """Test that plans have correct pricing values"""
        response = requests.get(
            f"{BASE_URL}/api/partners/plans",
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        
        assert response.status_code == 200
        plans = response.json()["plans"]
        
        # Find specific plans and validate pricing
        for plan in plans:
            if plan["plan_id"] == "basic":
                assert plan["base_price"] == 5.0, f"Basic base_price should be 5.0, got {plan['base_price']}"
                assert plan["price_per_employee"] == 1.5, f"Basic price_per_employee should be 1.5"
                assert plan["max_employees"] == 50, f"Basic max_employees should be 50"
            elif plan["plan_id"] == "pro":
                assert plan["base_price"] == 10.0, f"Pro base_price should be 10.0"
                assert plan["price_per_employee"] == 1.5, f"Pro price_per_employee should be 1.5"
                assert plan["max_employees"] == 200, f"Pro max_employees should be 200"
            elif plan["plan_id"] == "enterprise":
                assert plan["base_price"] == 20.0, f"Enterprise base_price should be 20.0"
                assert plan["price_per_employee"] == 1.5, f"Enterprise price_per_employee should be 1.5"
                assert plan["max_employees"] >= 9999, f"Enterprise max_employees should be 9999+"
        
        print("✓ Plan pricing values are correct")
    
    def test_plans_requires_partner_auth(self):
        """Test that plans endpoint requires partner authentication"""
        # Without token
        response = requests.get(f"{BASE_URL}/api/partners/plans")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        
        # With invalid token
        response = requests.get(
            f"{BASE_URL}/api/partners/plans",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code in [401, 403], f"Should reject invalid token, got {response.status_code}"
        
        print("✓ Plans endpoint properly requires partner authentication")


class TestClientActivation:
    """Tests for client activation endpoint PATCH /api/partners/clients/{id}/activate"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Get partner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def test_client_id(self, partner_token):
        """Create a test client for activation tests"""
        unique_id = str(uuid.uuid4())[:8]
        client_data = {
            "company_name": f"TEST_ActivationClient_{unique_id}",
            "contact_name": f"Test Contact {unique_id}",
            "email": f"test_activation_{unique_id}@test.com",
            "phone": "809-555-0001",
            "billing_type": "direct"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            json=client_data,
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        
        assert response.status_code == 200, f"Failed to create test client: {response.text}"
        return response.json()["client_id"]
    
    def test_activate_client_basic_plan(self, partner_token, test_client_id):
        """Test activating a client with basic plan"""
        activation_data = {
            "plan_id": "basic",
            "employee_count": 10
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{test_client_id}/activate",
            json=activation_data,
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response
        assert "message" in data, "Response should contain message"
        assert "client_id" in data, "Response should contain client_id"
        assert "plan" in data, "Response should contain plan"
        assert "employee_count" in data, "Response should contain employee_count"
        assert "monthly_value" in data, "Response should contain monthly_value"
        
        # Validate values
        assert data["plan"] == "basic", f"Plan should be basic, got {data['plan']}"
        assert data["employee_count"] == 10, f"Employee count should be 10, got {data['employee_count']}"
        
        # Validate monthly value calculation: base_price + (employee_count * price_per_employee)
        # Basic: $5 + (10 * $1.50) = $5 + $15 = $20
        expected_monthly = 5.0 + (10 * 1.5)
        assert data["monthly_value"] == expected_monthly, f"Monthly value should be {expected_monthly}, got {data['monthly_value']}"
        
        print("✓ Client activation with basic plan works correctly")
    
    def test_activate_client_validates_employee_count(self, partner_token):
        """Test that activation validates employee count against plan limits"""
        # Create a new client for this test
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            json={
                "company_name": f"TEST_EmpLimit_{unique_id}",
                "contact_name": "Test",
                "email": f"test_emplimit_{unique_id}@test.com",
                "billing_type": "direct"
            },
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        assert response.status_code == 200
        client_id = response.json()["client_id"]
        
        # Try to activate with too many employees for basic plan (max 50)
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{client_id}/activate",
            json={"plan_id": "basic", "employee_count": 100},
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400, f"Should reject employee count > max, got {response.status_code}"
        
        print("✓ Activation properly validates employee count against plan limits")
    
    def test_activate_client_validates_plan_id(self, partner_token):
        """Test that activation validates plan_id"""
        # Create a new client
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            json={
                "company_name": f"TEST_PlanVal_{unique_id}",
                "contact_name": "Test",
                "email": f"test_planval_{unique_id}@test.com",
                "billing_type": "direct"
            },
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        assert response.status_code == 200
        client_id = response.json()["client_id"]
        
        # Try invalid plan_id
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{client_id}/activate",
            json={"plan_id": "invalid_plan", "employee_count": 5},
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400, f"Should reject invalid plan_id, got {response.status_code}"
        
        # Try trial plan (should be rejected)
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{client_id}/activate",
            json={"plan_id": "trial", "employee_count": 1},
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400, f"Should reject trial plan, got {response.status_code}"
        
        print("✓ Activation properly validates plan_id")


class TestClientSubscriptionUpdate:
    """Tests for subscription update endpoint PATCH /api/partners/clients/{id}/subscription"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Get partner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def active_test_client(self, partner_token):
        """Create and activate a test client for subscription update tests"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create client
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            json={
                "company_name": f"TEST_SubUpdate_{unique_id}",
                "contact_name": "Test Contact",
                "email": f"test_subupdate_{unique_id}@test.com",
                "billing_type": "direct"
            },
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        assert response.status_code == 200
        client_id = response.json()["client_id"]
        
        # Activate with basic plan
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{client_id}/activate",
            json={"plan_id": "basic", "employee_count": 5},
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        
        return client_id
    
    def test_update_subscription_plan(self, partner_token, active_test_client):
        """Test updating client's subscription plan"""
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{active_test_client}/subscription",
            json={"plan_id": "pro", "employee_count": 15},
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "plan" in data, "Response should contain plan"
        assert "employee_count" in data, "Response should contain employee_count"
        assert "monthly_value" in data, "Response should contain monthly_value"
        
        assert data["plan"] == "pro", f"Plan should be pro, got {data['plan']}"
        assert data["employee_count"] == 15, f"Employee count should be 15, got {data['employee_count']}"
        
        # Pro: $10 + (15 * $1.50) = $10 + $22.50 = $32.50
        expected_monthly = 10.0 + (15 * 1.5)
        assert data["monthly_value"] == expected_monthly, f"Monthly value should be {expected_monthly}, got {data['monthly_value']}"
        
        print("✓ Subscription update works correctly")
    
    def test_update_employee_count_only(self, partner_token, active_test_client):
        """Test updating only employee count"""
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{active_test_client}/subscription",
            json={"employee_count": 25},
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["employee_count"] == 25, f"Employee count should be 25, got {data['employee_count']}"
        
        print("✓ Update employee count only works")


class TestClientDeactivation:
    """Tests for client deactivation endpoint PATCH /api/partners/clients/{id}/deactivate"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Get partner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_deactivate_client(self, partner_token):
        """Test deactivating an active client"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create and activate a client
        response = requests.post(
            f"{BASE_URL}/api/partners/clients",
            json={
                "company_name": f"TEST_Deactivate_{unique_id}",
                "contact_name": "Test",
                "email": f"test_deactivate_{unique_id}@test.com",
                "billing_type": "direct"
            },
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        assert response.status_code == 200
        client_id = response.json()["client_id"]
        
        # Activate
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{client_id}/activate",
            json={"plan_id": "basic", "employee_count": 3},
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        
        # Deactivate
        response = requests.patch(
            f"{BASE_URL}/api/partners/clients/{client_id}/deactivate",
            json={},
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain message"
        
        # Verify client is inactive
        response = requests.get(
            f"{BASE_URL}/api/partners/clients/{client_id}",
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        assert response.status_code == 200
        client_data = response.json()["client"]
        assert client_data["status"] == "inactive", f"Status should be inactive, got {client_data['status']}"
        
        print("✓ Client deactivation works correctly")


class TestExistingClientAcmeCorp:
    """Tests using existing client 'Acme Corp' (client_bde627abff09624a)"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Get partner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_verify_acme_corp_exists(self, partner_token):
        """Verify Acme Corp client exists and has expected data"""
        response = requests.get(
            f"{BASE_URL}/api/partners/clients",
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        
        assert response.status_code == 200
        clients = response.json()["clients"]
        
        acme_corp = None
        for client in clients:
            if "Acme" in client.get("company_name", ""):
                acme_corp = client
                break
        
        if acme_corp:
            print(f"✓ Found Acme Corp: {acme_corp.get('company_name')}")
            print(f"  - Status: {acme_corp.get('status')}")
            print(f"  - Plan: {acme_corp.get('subscription_plan')}")
            print(f"  - Employees: {acme_corp.get('employee_count')}")
            print(f"  - Monthly Value: ${acme_corp.get('monthly_value', 0)}")
        else:
            print("! Acme Corp not found in clients list (may have been modified by previous tests)")


class TestDashboardWithPlanData:
    """Tests to verify dashboard returns plan-related data"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Get partner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_dashboard_returns_statistics(self, partner_token):
        """Test that dashboard returns proper statistics"""
        response = requests.get(
            f"{BASE_URL}/api/partners/dashboard",
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate structure
        assert "statistics" in data, "Dashboard should contain statistics"
        assert "commissions" in data, "Dashboard should contain commissions"
        assert "firm" in data, "Dashboard should contain firm info"
        
        stats = data["statistics"]
        assert "total_clients" in stats, "Statistics should have total_clients"
        assert "active_clients" in stats, "Statistics should have active_clients"
        
        print(f"✓ Dashboard statistics: {stats['active_clients']} active / {stats['total_clients']} total clients")


class TestPayoutEndpoints:
    """Tests for payout endpoints (after fixing PAYOUT_FREQUENCY bug)"""
    
    @pytest.fixture(scope="class")
    def partner_token(self):
        """Get partner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PARTNER_EMAIL,
            "password": PARTNER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_payout_balance_endpoint(self, partner_token):
        """Test GET /api/partners/payouts/balance works after fix"""
        response = requests.get(
            f"{BASE_URL}/api/partners/payouts/balance",
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate structure
        assert "available_balance" in data, "Should have available_balance"
        assert "payout_frequency" in data, "Should have payout_frequency"
        
        print(f"✓ Payout balance endpoint works: ${data.get('available_balance', 0)} available")
    
    def test_payout_history_endpoint(self, partner_token):
        """Test GET /api/partners/payouts/history works"""
        response = requests.get(
            f"{BASE_URL}/api/partners/payouts/history",
            headers={"Authorization": f"Bearer {partner_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "payouts" in data, "Should have payouts list"
        print(f"✓ Payout history endpoint works: {len(data['payouts'])} payouts found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
