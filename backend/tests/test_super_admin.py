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


# ---------- Sync Statuses Tests (New in iteration 220) ----------

class TestSuperAdminSyncStatuses:
    """Super Admin sync-statuses endpoint tests - smart status detection"""
    
    def test_sync_statuses_endpoint_exists(self, sa_headers):
        """POST /api/super-admin/sync-statuses should be accessible"""
        response = requests.post(f"{BASE_URL}/api/super-admin/sync-statuses", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "activated" in data, "Response should have 'activated' count"
        assert "deactivated" in data, "Response should have 'deactivated' count"
        assert "total" in data, "Response should have 'total' count"
        
        print(f"✓ Sync statuses: {data['activated']} activated, {data['deactivated']} deactivated, {data['total']} total")
    
    def test_sync_statuses_unauthenticated(self):
        """POST /api/super-admin/sync-statuses without token should return 401"""
        response = requests.post(f"{BASE_URL}/api/super-admin/sync-statuses")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated sync-statuses request correctly rejected")


class TestSuperAdminCompaniesEnrichedFields:
    """Tests for enriched company fields: subscription_plan, plan_name, monthly_price"""
    
    def test_companies_have_subscription_plan(self, sa_headers):
        """GET /api/super-admin/companies should return subscription_plan for each company"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:  # Check first 5
            assert "subscription_plan" in company, f"Company {company.get('company_id')} should have subscription_plan"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' has subscription_plan: {company.get('subscription_plan')}")
    
    def test_companies_have_plan_name(self, sa_headers):
        """GET /api/super-admin/companies should return plan_name for each company"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:  # Check first 5
            assert "plan_name" in company, f"Company {company.get('company_id')} should have plan_name"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' has plan_name: {company.get('plan_name')}")
    
    def test_companies_have_monthly_price(self, sa_headers):
        """GET /api/super-admin/companies should return monthly_price for each company"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:  # Check first 5
            assert "monthly_price" in company, f"Company {company.get('company_id')} should have monthly_price"
            assert isinstance(company["monthly_price"], (int, float)), "monthly_price should be a number"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' has monthly_price: RD${company.get('monthly_price')}")


class TestSuperAdminSmartStatusDetection:
    """Tests for smart status detection - companies with data should be active"""
    
    def test_stats_has_active_companies(self, sa_headers):
        """GET /api/super-admin/stats should return active_companies > 0 if companies have data"""
        response = requests.get(f"{BASE_URL}/api/super-admin/stats", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        active = data.get("active_companies", 0)
        inactive = data.get("inactive_companies", 0)
        total = data.get("total_companies", 0)
        
        print(f"✓ Stats: {active} active, {inactive} inactive, {total} total")
        
        # If there are companies with employees/users, at least some should be active
        if data.get("total_employees", 0) > 0 or data.get("total_users", 0) > 0:
            assert active > 0, f"Expected active_companies > 0 when there are employees/users, got {active}"
            print(f"✓ Active companies count is > 0 as expected (smart status detection working)")
    
    def test_companies_with_users_are_active(self, sa_headers):
        """Companies with users and employees should show as active"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        
        # Find companies with users and employees
        companies_with_data = [c for c in companies if c.get("user_count", 0) > 0 and c.get("employee_count", 0) > 0]
        
        if len(companies_with_data) == 0:
            pytest.skip("No companies with both users and employees")
        
        for company in companies_with_data[:3]:  # Check first 3
            status = company.get("status")
            plan = company.get("subscription_plan", "free")
            
            # Companies with users AND employees should be active (unless plan is free/trial with no explicit status)
            if plan not in ("free", "trial"):
                assert status == "active", f"Company '{company.get('name')}' with {company.get('user_count')} users and {company.get('employee_count')} employees should be active, got {status}"
                print(f"✓ Company '{company.get('name')}' with users+employees is correctly marked as 'active'")
            else:
                print(f"✓ Company '{company.get('name')}' has plan '{plan}', status: {status}")


# ---------- Revenue Metrics Tests (New in iteration 214) ----------

class TestSuperAdminRevenue:
    """Super Admin revenue endpoint tests - MRR, ARR, plan distribution, overdue alerts"""
    
    def test_get_revenue_metrics(self, sa_headers):
        """GET /api/super-admin/revenue should return all revenue metrics"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify all required fields exist
        required_fields = ["mrr", "arr", "active_paying", "plan_distribution", 
                          "overdue_alerts", "overdue_count", "partner_companies", 
                          "partner_mrr", "payment_history"]
        for field in required_fields:
            assert field in data, f"Revenue response should have '{field}'"
        
        print(f"✓ Revenue endpoint returns all required fields: {required_fields}")
    
    def test_revenue_mrr_is_number(self, sa_headers):
        """Revenue MRR should be a number >= 0"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        mrr = data.get("mrr")
        
        assert isinstance(mrr, (int, float)), f"MRR should be a number, got {type(mrr)}"
        assert mrr >= 0, f"MRR should be >= 0, got {mrr}"
        print(f"✓ MRR is valid number: RD${mrr:,.2f}")
    
    def test_revenue_arr_is_mrr_times_12(self, sa_headers):
        """Revenue ARR should be MRR * 12"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        mrr = data.get("mrr", 0)
        arr = data.get("arr", 0)
        
        expected_arr = round(mrr * 12, 2)
        assert arr == expected_arr, f"ARR should be MRR*12 ({expected_arr}), got {arr}"
        print(f"✓ ARR correctly calculated: RD${arr:,.2f} (MRR: RD${mrr:,.2f})")
    
    def test_plan_distribution_structure(self, sa_headers):
        """plan_distribution should contain entries with plan_name, count, mrr, and type"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        plan_dist = data.get("plan_distribution", {})
        
        assert isinstance(plan_dist, dict), "plan_distribution should be a dict"
        
        if len(plan_dist) > 0:
            for plan_id, plan_data in plan_dist.items():
                assert "plan_name" in plan_data, f"Plan '{plan_id}' should have plan_name"
                assert "count" in plan_data, f"Plan '{plan_id}' should have count"
                assert "mrr" in plan_data, f"Plan '{plan_id}' should have mrr"
                assert "type" in plan_data, f"Plan '{plan_id}' should have type"
                
                # Verify type is one of expected values
                valid_types = ["direct", "partner", "trial", "free"]
                assert plan_data["type"] in valid_types, f"Plan type should be one of {valid_types}, got {plan_data['type']}"
                
                print(f"✓ Plan '{plan_data['plan_name']}': {plan_data['count']} companies, RD${plan_data['mrr']:,.2f}/mes, type: {plan_data['type']}")
        else:
            print("✓ plan_distribution is empty (no subscriptions)")
    
    def test_overdue_alerts_structure(self, sa_headers):
        """overdue_alerts should be a list with proper structure"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        overdue = data.get("overdue_alerts", [])
        overdue_count = data.get("overdue_count", 0)
        
        assert isinstance(overdue, list), "overdue_alerts should be a list"
        assert overdue_count == len(overdue), f"overdue_count ({overdue_count}) should match len(overdue_alerts) ({len(overdue)})"
        
        if len(overdue) > 0:
            alert = overdue[0]
            assert "company_id" in alert, "Alert should have company_id"
            assert "company_name" in alert, "Alert should have company_name"
            assert "days_overdue" in alert, "Alert should have days_overdue"
            print(f"✓ Found {len(overdue)} overdue alerts")
            print(f"✓ First alert: {alert.get('company_name')} - {alert.get('days_overdue')} days overdue")
        else:
            print("✓ No overdue alerts (all payments current)")
    
    def test_partner_metrics(self, sa_headers):
        """Partner companies and partner_mrr should be valid numbers"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        partner_companies = data.get("partner_companies", 0)
        partner_mrr = data.get("partner_mrr", 0)
        
        assert isinstance(partner_companies, int), f"partner_companies should be int, got {type(partner_companies)}"
        assert isinstance(partner_mrr, (int, float)), f"partner_mrr should be number, got {type(partner_mrr)}"
        assert partner_companies >= 0, "partner_companies should be >= 0"
        assert partner_mrr >= 0, "partner_mrr should be >= 0"
        
        print(f"✓ Partner metrics: {partner_companies} companies, RD${partner_mrr:,.2f} MRR")
    
    def test_payment_history_structure(self, sa_headers):
        """payment_history should be a list of activation records"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        history = data.get("payment_history", [])
        
        assert isinstance(history, list), "payment_history should be a list"
        print(f"✓ Payment history has {len(history)} records")
    
    def test_revenue_unauthenticated(self):
        """GET /api/super-admin/revenue without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated revenue request correctly rejected")


class TestSuperAdminPlanChange:
    """Super Admin plan change endpoint tests"""
    
    def test_change_plan_success(self, sa_headers):
        """POST /api/super-admin/companies/{id}/plan should update company plan"""
        # Get a company to test with
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert companies_response.status_code == 200
        companies = companies_response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available to test plan change")
        
        company = companies[0]
        company_id = company["company_id"]
        company_name = company.get("name", company_id)
        
        # Change to pro plan
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/{company_id}/plan",
            headers=sa_headers,
            json={"plan_id": "pro"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have message"
        assert "monthly" in data, "Response should have monthly price"
        assert data["monthly"] == 5000, f"Pro plan should be RD$5000, got {data['monthly']}"
        print(f"✓ Changed '{company_name}' to Pro plan (RD$5,000/mes)")
        
        # Verify the change persisted
        verify_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies_after = verify_response.json()
        updated_company = next((c for c in companies_after if c["company_id"] == company_id), None)
        assert updated_company is not None
        assert updated_company.get("subscription_plan") == "pro", f"Company plan should be 'pro', got {updated_company.get('subscription_plan')}"
        print(f"✓ Verified company subscription_plan is now 'pro'")
    
    def test_change_plan_invalid_plan_id(self, sa_headers):
        """POST /api/super-admin/companies/{id}/plan with invalid plan_id should return 400"""
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies = companies_response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        company_id = companies[0]["company_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/{company_id}/plan",
            headers=sa_headers,
            json={"plan_id": "invalid_plan_xyz"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid plan, got {response.status_code}"
        print("✓ Invalid plan_id correctly rejected with 400")
    
    def test_change_plan_nonexistent_company(self, sa_headers):
        """POST /api/super-admin/companies/{id}/plan with invalid company should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/nonexistent_company_xyz/plan",
            headers=sa_headers,
            json={"plan_id": "basico"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Nonexistent company correctly returns 404")
    
    def test_change_plan_with_custom_price(self, sa_headers):
        """POST /api/super-admin/companies/{id}/plan with custom_price should use custom price"""
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies = companies_response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        company_id = companies[0]["company_id"]
        custom_price = 3000
        
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/{company_id}/plan",
            headers=sa_headers,
            json={"plan_id": "basico", "custom_price": custom_price}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["monthly"] == custom_price, f"Monthly should be custom price {custom_price}, got {data['monthly']}"
        print(f"✓ Plan changed with custom price RD${custom_price}")
    
    def test_change_plan_all_valid_plans(self, sa_headers):
        """Test changing to all valid plan types"""
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies = companies_response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        company_id = companies[0]["company_id"]
        
        valid_plans = ["basico", "pro", "enterprise", "partner_basico", "partner_pro", "partner_enterprise", "trial", "free"]
        
        for plan_id in valid_plans:
            response = requests.post(
                f"{BASE_URL}/api/super-admin/companies/{company_id}/plan",
                headers=sa_headers,
                json={"plan_id": plan_id}
            )
            assert response.status_code == 200, f"Plan change to '{plan_id}' failed: {response.text}"
            print(f"✓ Successfully changed to plan '{plan_id}'")
    
    def test_change_plan_unauthenticated(self):
        """POST /api/super-admin/companies/{id}/plan without token should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/any_company/plan",
            json={"plan_id": "pro"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated plan change correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
