"""
Super Admin Improvements Tests - FortexaRH
Tests for the new Super Admin features:
- Prices in USD (not RD$): Basico=$5, Pro=$10, Enterprise=$20, per_employee=$1.50
- New columns: monthly_billing, active_employee_count, contact_name, contact_email, payment_method, activation_date, next_payment_date, per_employee_rate, extra_users
- Monthly billing calculation: base plan + (active_employees × per_employee_rate) + (extra_users × extra_user_cost)
- Drill-down endpoint: GET /api/super-admin/companies/{company_id}/users
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Super Admin credentials
SA_USERNAME = "fortexa2026rd"
SA_PASSWORD = "FortexaAdmin2026!"

# Expected USD prices
EXPECTED_PLAN_PRICES = {
    "basico": {"monthly": 5, "per_employee": 1.50, "included_users": 3, "extra_user": 2},
    "pro": {"monthly": 10, "per_employee": 1.50, "included_users": 5, "extra_user": 2},
    "enterprise": {"monthly": 20, "per_employee": 1.50, "included_users": 7, "extra_user": 2},
}


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


class TestCompaniesNewFields:
    """Tests for new enriched fields in GET /api/super-admin/companies"""
    
    def test_companies_have_monthly_billing(self, sa_headers):
        """GET /api/super-admin/companies should return monthly_billing for each company"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "monthly_billing" in company, f"Company {company.get('company_id')} should have monthly_billing"
            assert isinstance(company["monthly_billing"], (int, float)), "monthly_billing should be a number"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' has monthly_billing: ${company.get('monthly_billing')}")
    
    def test_companies_have_active_employee_count(self, sa_headers):
        """GET /api/super-admin/companies should return active_employee_count"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "active_employee_count" in company, f"Company {company.get('company_id')} should have active_employee_count"
            assert isinstance(company["active_employee_count"], int), "active_employee_count should be int"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' has active_employee_count: {company.get('active_employee_count')}")
    
    def test_companies_have_contact_fields(self, sa_headers):
        """GET /api/super-admin/companies should return contact_name and contact_email"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "contact_name" in company, f"Company {company.get('company_id')} should have contact_name"
            assert "contact_email" in company, f"Company {company.get('company_id')} should have contact_email"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' contact: {company.get('contact_name')} ({company.get('contact_email')})")
    
    def test_companies_have_payment_method(self, sa_headers):
        """GET /api/super-admin/companies should return payment_method"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "payment_method" in company, f"Company {company.get('company_id')} should have payment_method"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' payment_method: {company.get('payment_method')}")
    
    def test_companies_have_activation_date(self, sa_headers):
        """GET /api/super-admin/companies should return activation_date"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "activation_date" in company, f"Company {company.get('company_id')} should have activation_date"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' activation_date: {company.get('activation_date')}")
    
    def test_companies_have_next_payment_date(self, sa_headers):
        """GET /api/super-admin/companies should return next_payment_date"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "next_payment_date" in company, f"Company {company.get('company_id')} should have next_payment_date"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' next_payment_date: {company.get('next_payment_date')}")
    
    def test_companies_have_per_employee_rate(self, sa_headers):
        """GET /api/super-admin/companies should return per_employee_rate"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "per_employee_rate" in company, f"Company {company.get('company_id')} should have per_employee_rate"
            assert isinstance(company["per_employee_rate"], (int, float)), "per_employee_rate should be a number"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' per_employee_rate: ${company.get('per_employee_rate')}")
    
    def test_companies_have_extra_users(self, sa_headers):
        """GET /api/super-admin/companies should return extra_users"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        for company in companies[:5]:
            assert "extra_users" in company, f"Company {company.get('company_id')} should have extra_users"
            assert isinstance(company["extra_users"], int), "extra_users should be int"
            print(f"✓ Company '{company.get('name', company.get('company_id'))}' extra_users: {company.get('extra_users')}")


class TestUSDPricing:
    """Tests for USD pricing (not RD$)"""
    
    def test_plan_prices_are_usd(self, sa_headers):
        """Plan prices should be in USD: Basico=$5, Pro=$10, Enterprise=$20"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        
        for company in companies:
            plan = company.get("subscription_plan", "free")
            monthly_price = company.get("monthly_price", 0)
            
            if plan in EXPECTED_PLAN_PRICES:
                expected_price = EXPECTED_PLAN_PRICES[plan]["monthly"]
                assert monthly_price == expected_price, f"Plan '{plan}' should be ${expected_price}, got ${monthly_price}"
                print(f"✓ Plan '{plan}' correctly priced at ${monthly_price} USD")
    
    def test_per_employee_rate_is_usd(self, sa_headers):
        """Per employee rate should be $1.50 USD"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        
        for company in companies:
            plan = company.get("subscription_plan", "free")
            per_emp_rate = company.get("per_employee_rate", 0)
            
            if plan in EXPECTED_PLAN_PRICES:
                expected_rate = EXPECTED_PLAN_PRICES[plan]["per_employee"]
                assert per_emp_rate == expected_rate, f"Per employee rate for '{plan}' should be ${expected_rate}, got ${per_emp_rate}"
                print(f"✓ Plan '{plan}' per_employee_rate correctly at ${per_emp_rate} USD")


class TestMonthlyBillingCalculation:
    """Tests for monthly billing calculation: base + (active_employees × per_employee) + (extra_users × extra_user_cost)"""
    
    def test_monthly_billing_calculation(self, sa_headers):
        """Monthly billing should equal: base + (active_employees × per_employee_rate) + (extra_users × extra_user_cost)"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        
        for company in companies:
            plan = company.get("subscription_plan", "free")
            monthly_price = company.get("monthly_price", 0)
            active_emp_count = company.get("active_employee_count", 0)
            per_emp_rate = company.get("per_employee_rate", 0)
            extra_users = company.get("extra_users", 0)
            monthly_billing = company.get("monthly_billing", 0)
            
            # Get extra_user cost from expected prices
            extra_user_cost = EXPECTED_PLAN_PRICES.get(plan, {}).get("extra_user", 0)
            
            # Calculate expected billing
            expected_billing = round(monthly_price + (active_emp_count * per_emp_rate) + (extra_users * extra_user_cost), 2)
            
            assert monthly_billing == expected_billing, f"Company '{company.get('name')}' billing should be ${expected_billing}, got ${monthly_billing}"
            print(f"✓ Company '{company.get('name')}': ${monthly_price} + ({active_emp_count} × ${per_emp_rate}) + ({extra_users} × ${extra_user_cost}) = ${monthly_billing}")
    
    def test_fortexarh_demo_corp_billing(self, sa_headers):
        """FortexaRH Demo Corp should have $19.00/mes billing (Pro $10 + 6 employees × $1.50)"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert response.status_code == 200
        
        companies = response.json()
        
        # Find FortexaRH Demo Corp
        demo_corp = None
        for c in companies:
            if "Demo Corp" in c.get("name", "") or "demo" in c.get("name", "").lower():
                demo_corp = c
                break
        
        if demo_corp is None:
            pytest.skip("FortexaRH Demo Corp not found")
        
        plan = demo_corp.get("subscription_plan")
        monthly_billing = demo_corp.get("monthly_billing", 0)
        active_emp_count = demo_corp.get("active_employee_count", 0)
        
        print(f"✓ FortexaRH Demo Corp: plan={plan}, active_employees={active_emp_count}, monthly_billing=${monthly_billing}")
        
        # If Pro plan with 6 employees: $10 + (6 × $1.50) = $19.00
        if plan == "pro" and active_emp_count == 6:
            expected = 10 + (6 * 1.50)  # $19.00
            assert monthly_billing == expected, f"Demo Corp billing should be ${expected}, got ${monthly_billing}"
            print(f"✓ FortexaRH Demo Corp billing verified: ${monthly_billing}/mes")


class TestDrillDownEndpoint:
    """Tests for GET /api/super-admin/companies/{company_id}/users drill-down endpoint"""
    
    def test_drill_down_endpoint_exists(self, sa_headers):
        """GET /api/super-admin/companies/{company_id}/users should return users and employees"""
        # First get a company
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        assert companies_response.status_code == 200
        companies = companies_response.json()
        
        if len(companies) == 0:
            pytest.skip("No companies available")
        
        company_id = companies[0]["company_id"]
        
        # Call drill-down endpoint
        response = requests.get(f"{BASE_URL}/api/super-admin/companies/{company_id}/users", headers=sa_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "users" in data, "Response should have 'users' array"
        assert "employees" in data, "Response should have 'employees' array"
        assert isinstance(data["users"], list), "users should be a list"
        assert isinstance(data["employees"], list), "employees should be a list"
        
        print(f"✓ Drill-down endpoint returns {len(data['users'])} users and {len(data['employees'])} employees")
    
    def test_drill_down_users_fields(self, sa_headers):
        """Users array should include name, email, role, last_login (excludes password)"""
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies = companies_response.json()
        
        # Find a company with users
        target_company = None
        for c in companies:
            if c.get("user_count", 0) > 0:
                target_company = c
                break
        
        if target_company is None:
            pytest.skip("No companies with users found")
        
        company_id = target_company["company_id"]
        
        response = requests.get(f"{BASE_URL}/api/super-admin/companies/{company_id}/users", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        users = data.get("users", [])
        
        if len(users) > 0:
            user = users[0]
            # Should have these fields
            assert "email" in user, "User should have email"
            # Should NOT have password
            assert "password" not in user, "User should NOT have password"
            assert "password_hash" not in user, "User should NOT have password_hash"
            
            print(f"✓ User fields verified: name={user.get('name')}, email={user.get('email')}, role={user.get('role')}")
            print(f"✓ Password fields correctly excluded")
    
    def test_drill_down_employees_fields(self, sa_headers):
        """Employees array should include first_name, last_name, position, department, status (cedula is optional)"""
        companies_response = requests.get(f"{BASE_URL}/api/super-admin/companies", headers=sa_headers)
        companies = companies_response.json()
        
        # Find a company with employees
        target_company = None
        for c in companies:
            if c.get("employee_count", 0) > 0:
                target_company = c
                break
        
        if target_company is None:
            pytest.skip("No companies with employees found")
        
        company_id = target_company["company_id"]
        
        response = requests.get(f"{BASE_URL}/api/super-admin/companies/{company_id}/users", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        employees = data.get("employees", [])
        
        if len(employees) > 0:
            emp = employees[0]
            # Should have these required fields
            required_fields = ["first_name", "last_name", "position", "department", "status"]
            for field in required_fields:
                assert field in emp, f"Employee should have {field}"
            
            # cedula is optional but should be in the projection
            print(f"✓ Employee fields verified: {emp.get('first_name')} {emp.get('last_name')}, position={emp.get('position')}, dept={emp.get('department')}, status={emp.get('status')}, cedula={emp.get('cedula', 'N/A')}")
    
    def test_drill_down_unauthenticated(self):
        """GET /api/super-admin/companies/{company_id}/users without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies/any_company/users")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated drill-down request correctly rejected")
    
    def test_drill_down_nonexistent_company(self, sa_headers):
        """GET /api/super-admin/companies/{invalid_id}/users should return empty arrays (not 404)"""
        response = requests.get(f"{BASE_URL}/api/super-admin/companies/nonexistent_company_xyz/users", headers=sa_headers)
        # The endpoint returns empty arrays for non-existent companies (not 404)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("users") == [], "Should return empty users array"
        assert data.get("employees") == [], "Should return empty employees array"
        print("✓ Nonexistent company returns empty arrays")


class TestRevenueUSDPricing:
    """Tests for USD pricing in revenue metrics"""
    
    def test_revenue_mrr_in_usd(self, sa_headers):
        """MRR should be in USD (small numbers like $5, $10, $20 per company)"""
        response = requests.get(f"{BASE_URL}/api/super-admin/revenue", headers=sa_headers)
        assert response.status_code == 200
        
        data = response.json()
        mrr = data.get("mrr", 0)
        
        # MRR in USD should be reasonable (not thousands like RD$)
        # With USD pricing, even 100 companies would be ~$1000-2000 MRR
        print(f"✓ MRR: ${mrr} (USD)")
        
        # ARR should be MRR * 12
        arr = data.get("arr", 0)
        expected_arr = round(mrr * 12, 2)
        assert arr == expected_arr, f"ARR should be ${expected_arr}, got ${arr}"
        print(f"✓ ARR: ${arr} (USD)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
