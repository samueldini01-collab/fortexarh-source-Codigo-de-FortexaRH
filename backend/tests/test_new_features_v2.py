"""
Test Suite for 4 New Features - FortexaRH
1. Payroll Approval Workflow (submit-for-approval, approve, reject)
2. Metrics Dashboard with real data
3. Costs by Department Preview
4. AI Search Learning (log-query, suggestions)
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
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
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL


class TestPayrollApprovalWorkflow:
    """Test payroll approval workflow: Draft -> Pending Approval -> Approved -> Paid"""
    
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
    
    @pytest.fixture(scope="class")
    def test_period_id(self, auth_headers):
        """Create a test payroll period for workflow testing"""
        # Create a new period
        period_data = {
            "period_type": "quincenal_1",
            "year": 2026,
            "month": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-15",
            "description": "TEST_Workflow Period"
        }
        response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods",
            headers=auth_headers,
            json=period_data
        )
        assert response.status_code == 200, f"Failed to create period: {response.text}"
        data = response.json()
        period_id = data.get("period_id")
        assert period_id is not None
        
        # Add employees to the period
        add_response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees",
            headers=auth_headers
        )
        # May return 200 even if no employees added
        
        yield period_id
        
        # Cleanup: Delete the test period
        requests.delete(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}",
            headers=auth_headers
        )
    
    def test_get_payroll_periods(self, auth_headers):
        """Test getting payroll periods"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_period_with_draft_status(self, auth_headers):
        """Test that new periods are created with 'draft' status"""
        period_data = {
            "period_type": "quincenal_1",
            "year": 2026,
            "month": 2,
            "start_date": "2026-02-01",
            "end_date": "2026-02-15",
            "description": "TEST_Draft Status Check"
        }
        response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods",
            headers=auth_headers,
            json=period_data
        )
        assert response.status_code == 200
        data = response.json()
        period_id = data.get("period_id")
        
        # Get the period and verify status is 'draft'
        get_response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        period = get_response.json()
        assert period.get("status") == "draft", f"Expected 'draft' status, got '{period.get('status')}'"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}",
            headers=auth_headers
        )
    
    def test_submit_for_approval_endpoint(self, auth_headers, test_period_id):
        """Test POST /api/payroll-v2/periods/{id}/submit-for-approval"""
        response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods/{test_period_id}/submit-for-approval",
            headers=auth_headers,
            json={"comments": "Ready for review"}
        )
        # May fail if no employees, but endpoint should exist
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}, {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "pending_approval"
    
    def test_approve_endpoint(self, auth_headers, test_period_id):
        """Test POST /api/payroll-v2/periods/{id}/approve"""
        response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods/{test_period_id}/approve",
            headers=auth_headers,
            json={"comments": "Approved by admin"}
        )
        # May fail depending on current status, but endpoint should exist
        assert response.status_code in [200, 400, 403], f"Unexpected status: {response.status_code}, {response.text}"
    
    def test_reject_endpoint(self, auth_headers):
        """Test POST /api/payroll-v2/periods/{id}/reject"""
        # Create a new period for rejection test
        period_data = {
            "period_type": "quincenal_1",
            "year": 2026,
            "month": 3,
            "start_date": "2026-03-01",
            "end_date": "2026-03-15",
            "description": "TEST_Reject Test"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods",
            headers=auth_headers,
            json=period_data
        )
        assert create_response.status_code == 200
        period_id = create_response.json().get("period_id")
        
        # Try to reject (should fail if not in pending_approval status)
        response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}/reject",
            headers=auth_headers,
            json={"comments": "Needs corrections"}
        )
        # Endpoint should exist
        assert response.status_code in [200, 400, 403], f"Unexpected status: {response.status_code}, {response.text}"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}",
            headers=auth_headers
        )
    
    def test_workflow_history_tracking(self, auth_headers):
        """Test that workflow history is tracked"""
        # Create period
        period_data = {
            "period_type": "quincenal_1",
            "year": 2026,
            "month": 4,
            "start_date": "2026-04-01",
            "end_date": "2026-04-15",
            "description": "TEST_Workflow History"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods",
            headers=auth_headers,
            json=period_data
        )
        period_id = create_response.json().get("period_id")
        
        # Add employees first
        requests.post(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}/add-employees",
            headers=auth_headers
        )
        
        # Submit for approval
        submit_response = requests.post(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}/submit-for-approval",
            headers=auth_headers,
            json={"comments": "Test workflow"}
        )
        
        # Get period and check workflow_history
        get_response = requests.get(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}",
            headers=auth_headers
        )
        if get_response.status_code == 200:
            period = get_response.json()
            # workflow_history should exist if submit was successful
            if submit_response.status_code == 200:
                assert "workflow_history" in period or period.get("status") == "pending_approval"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/payroll-v2/periods/{period_id}",
            headers=auth_headers
        )


class TestMetricsDashboard:
    """Test metrics dashboard with real data"""
    
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
    
    def test_metrics_dashboard_endpoint(self, auth_headers):
        """Test GET /api/metrics/dashboard?year=2026"""
        response = requests.get(
            f"{BASE_URL}/api/metrics/dashboard?year=2026",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "payroll_trend" in data, "Missing payroll_trend"
        assert "department_costs" in data, "Missing department_costs"
        assert "employee_metrics" in data, "Missing employee_metrics"
        assert "loan_metrics" in data, "Missing loan_metrics"
        assert "quick_stats" in data, "Missing quick_stats"
    
    def test_metrics_payroll_trend_structure(self, auth_headers):
        """Test payroll trend data structure"""
        response = requests.get(
            f"{BASE_URL}/api/metrics/dashboard?year=2026",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        payroll_trend = data.get("payroll_trend", [])
        assert isinstance(payroll_trend, list)
        
        # Should have 12 months
        assert len(payroll_trend) == 12, f"Expected 12 months, got {len(payroll_trend)}"
        
        # Each month should have required fields
        for month_data in payroll_trend:
            assert "month" in month_data
            assert "gross" in month_data
            assert "net" in month_data
            assert "deductions" in month_data
    
    def test_metrics_employee_metrics_structure(self, auth_headers):
        """Test employee metrics structure"""
        response = requests.get(
            f"{BASE_URL}/api/metrics/dashboard?year=2026",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee_metrics = data.get("employee_metrics", {})
        assert "total_employees" in employee_metrics
        assert "new_this_month" in employee_metrics
        assert "turnover_rate" in employee_metrics
    
    def test_metrics_loan_metrics_structure(self, auth_headers):
        """Test loan metrics structure"""
        response = requests.get(
            f"{BASE_URL}/api/metrics/dashboard?year=2026",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        loan_metrics = data.get("loan_metrics", {})
        assert "total_active_loans" in loan_metrics
        assert "total_loaned" in loan_metrics
        assert "total_pending" in loan_metrics
    
    def test_metrics_different_year(self, auth_headers):
        """Test metrics for different year"""
        response = requests.get(
            f"{BASE_URL}/api/metrics/dashboard?year=2025",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "payroll_trend" in data


class TestCostsByDepartment:
    """Test costs by department report with preview"""
    
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
    
    def test_costs_by_department_endpoint(self, auth_headers):
        """Test GET /api/reports/costs-by-department"""
        response = requests.get(
            f"{BASE_URL}/api/reports/costs-by-department?period=2026-01",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "period" in data
        assert "departments" in data
        assert "summary" in data
        assert "generated_at" in data
    
    def test_costs_department_structure(self, auth_headers):
        """Test department data structure"""
        response = requests.get(
            f"{BASE_URL}/api/reports/costs-by-department?period=2026-01",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        departments = data.get("departments", [])
        assert isinstance(departments, list)
        
        # Each department should have required fields
        for dept in departments:
            assert "department" in dept
            assert "employee_count" in dept
            assert "gross_salary" in dept
            assert "sfs_deduction" in dept
            assert "afp_deduction" in dept
            assert "isr_deduction" in dept
            assert "total_employer_cost" in dept
            assert "percentage_of_total" in dept
    
    def test_costs_summary_structure(self, auth_headers):
        """Test summary data structure"""
        response = requests.get(
            f"{BASE_URL}/api/reports/costs-by-department?period=2026-01",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", {})
        assert "total_gross" in summary
        assert "total_sfs" in summary
        assert "total_afp" in summary
        assert "total_isr" in summary
        assert "employee_count" in summary
        assert "grand_total_cost" in summary
    
    def test_costs_export_csv(self, auth_headers):
        """Test CSV export endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/reports/costs-by-department/export?period=2026-01&format=csv",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
    
    def test_department_comparison_endpoint(self, auth_headers):
        """Test GET /api/reports/department-comparison"""
        response = requests.get(
            f"{BASE_URL}/api/reports/department-comparison",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Each item should have comparison metrics
        for dept in data:
            assert "department" in dept
            assert "employee_count" in dept
            assert "total_salary" in dept
            assert "average_salary" in dept


class TestAISearchLearning:
    """Test AI search learning functionality"""
    
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
    
    def test_log_query_endpoint(self, auth_headers):
        """Test POST /api/search/log-query"""
        log_data = {
            "query": "TEST_empleados activos",
            "action_taken": "navigate",
            "action_target": "/employees",
            "result_count": 5
        }
        response = requests.post(
            f"{BASE_URL}/api/search/log-query",
            headers=auth_headers,
            json=log_data
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data or "log_id" in data
    
    def test_log_query_with_results(self, auth_headers):
        """Test logging query with results selected"""
        log_data = {
            "query": "TEST_nómina enero",
            "action_taken": "select_result",
            "action_target": "/payroll/period_123",
            "result_count": 3,
            "selected_result_index": 0
        }
        response = requests.post(
            f"{BASE_URL}/api/search/log-query",
            headers=auth_headers,
            json=log_data
        )
        assert response.status_code == 200
    
    def test_suggestions_endpoint(self, auth_headers):
        """Test GET /api/search/suggestions"""
        response = requests.get(
            f"{BASE_URL}/api/search/suggestions",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should return suggestions structure
        assert isinstance(data, (list, dict))
    
    def test_suggestions_with_query(self, auth_headers):
        """Test suggestions with partial query"""
        response = requests.get(
            f"{BASE_URL}/api/search/suggestions?q=emp",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_search_endpoint_exists(self, auth_headers):
        """Test main search endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=empleados",
            headers=auth_headers
        )
        # Should return 200 or valid response
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"


class TestIntegration:
    """Integration tests for all features working together"""
    
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
    
    def test_dashboard_stats_endpoint(self, auth_headers):
        """Test dashboard stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_subscription_endpoint(self, auth_headers):
        """Test subscription endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/subscription",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_employees_endpoint(self, auth_headers):
        """Test employees endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
