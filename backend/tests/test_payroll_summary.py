"""
Test Payroll Summary Feature - Executive payroll summary with charts and PDF export
Tests:
- POST /api/search/payroll-summary - returns summary with department breakdown, charts data
- POST /api/search/ai with 'resumen de nomina' - triggers quick pattern resumen_nomina
- POST /api/search/ai with 'gastos de nomina' - triggers quick pattern resumen_nomina
- POST /api/search/ai with 'comparar nomina' - triggers quick pattern resumen_nomina
- POST /api/search/execute-action with resumen_nomina - returns show_payroll_summary:true
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestPayrollSummaryBackend:
    """Tests for the payroll summary feature backend endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token") or data.get("access_token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    # ============ POST /api/search/payroll-summary Tests ============
    
    def test_payroll_summary_endpoint_exists(self):
        """Test that payroll-summary endpoint exists and returns 200"""
        response = self.session.post(
            f"{BASE_URL}/api/search/payroll-summary",
            json={"months": 3}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Payroll summary endpoint returns 200")
    
    def test_payroll_summary_returns_summary_object(self):
        """Test that payroll-summary returns summary with totals"""
        response = self.session.post(
            f"{BASE_URL}/api/search/payroll-summary",
            json={"months": 6}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for summary object or message about no data
        if data.get("summary"):
            summary = data["summary"]
            assert "total_gross" in summary, "Missing total_gross in summary"
            assert "total_deductions" in summary, "Missing total_deductions in summary"
            assert "total_net" in summary, "Missing total_net in summary"
            assert "total_periods" in summary, "Missing total_periods in summary"
            assert "avg_per_period" in summary, "Missing avg_per_period in summary"
            assert "avg_employees" in summary, "Missing avg_employees in summary"
            print(f"✓ Summary object contains all required fields: total_gross={summary['total_gross']}, total_net={summary['total_net']}")
        else:
            # No payroll data available - this is acceptable
            assert "message" in data, "Expected either summary or message"
            print(f"✓ No payroll data available: {data.get('message')}")
    
    def test_payroll_summary_returns_department_totals(self):
        """Test that payroll-summary returns department breakdown"""
        response = self.session.post(
            f"{BASE_URL}/api/search/payroll-summary",
            json={"months": 6}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("summary"):
            assert "department_totals" in data, "Missing department_totals"
            dept_totals = data["department_totals"]
            
            if dept_totals:
                # Check structure of department data
                for dept, vals in dept_totals.items():
                    assert "gross" in vals, f"Missing gross for department {dept}"
                    assert "net" in vals, f"Missing net for department {dept}"
                    assert "deductions" in vals, f"Missing deductions for department {dept}"
                    assert "employees" in vals, f"Missing employees for department {dept}"
                print(f"✓ Department totals structure is correct, {len(dept_totals)} departments found")
            else:
                print("✓ No department data (empty department_totals)")
        else:
            print("✓ No payroll data available")
    
    def test_payroll_summary_returns_charts_data(self):
        """Test that payroll-summary returns charts data for trend and departments"""
        response = self.session.post(
            f"{BASE_URL}/api/search/payroll-summary",
            json={"months": 6}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("summary"):
            assert "charts" in data, "Missing charts data"
            charts = data["charts"]
            
            assert "trend" in charts, "Missing trend chart data"
            assert "departments" in charts, "Missing departments chart data"
            
            # Check trend data structure
            if charts["trend"]:
                for item in charts["trend"]:
                    assert "period" in item, "Missing period in trend item"
                    assert "bruto" in item, "Missing bruto in trend item"
                    assert "neto" in item, "Missing neto in trend item"
                print(f"✓ Trend chart data has {len(charts['trend'])} periods")
            
            # Check departments pie chart data
            if charts["departments"]:
                for item in charts["departments"]:
                    assert "name" in item, "Missing name in department chart item"
                    assert "value" in item, "Missing value in department chart item"
                print(f"✓ Department pie chart has {len(charts['departments'])} departments")
        else:
            print("✓ No payroll data available")
    
    def test_payroll_summary_returns_comparison(self):
        """Test that payroll-summary returns period comparison when available"""
        response = self.session.post(
            f"{BASE_URL}/api/search/payroll-summary",
            json={"months": 6}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("summary") and data.get("comparison"):
            comparison = data["comparison"]
            assert "current_period" in comparison, "Missing current_period"
            assert "previous_period" in comparison, "Missing previous_period"
            assert "gross_change_pct" in comparison, "Missing gross_change_pct"
            assert "gross_diff" in comparison, "Missing gross_diff"
            print(f"✓ Comparison data: {comparison['current_period']} vs {comparison['previous_period']}, change: {comparison['gross_change_pct']}%")
        else:
            print("✓ No comparison data (less than 2 periods or no data)")
    
    def test_payroll_summary_returns_periods_list(self):
        """Test that payroll-summary returns list of periods"""
        response = self.session.post(
            f"{BASE_URL}/api/search/payroll-summary",
            json={"months": 6}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("summary"):
            assert "periods" in data, "Missing periods list"
            periods = data["periods"]
            
            if periods:
                for period in periods:
                    assert "period_id" in period, "Missing period_id"
                    assert "label" in period, "Missing label"
                    assert "total_gross" in period, "Missing total_gross"
                    assert "total_net" in period, "Missing total_net"
                    assert "departments" in period, "Missing departments breakdown"
                print(f"✓ Periods list has {len(periods)} periods")
            else:
                print("✓ Empty periods list")
        else:
            print("✓ No payroll data available")
    
    # ============ POST /api/search/ai Quick Pattern Tests ============
    
    def test_ai_search_resumen_de_nomina_triggers_quick_pattern(self):
        """Test that 'resumen de nomina' triggers quick pattern and returns resumen_nomina action"""
        response = self.session.post(
            f"{BASE_URL}/api/search/ai",
            json={"query": "resumen de nomina"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should trigger quick pattern and return show_payroll_summary flag
        assert data.get("show_payroll_summary") == True, f"Expected show_payroll_summary=True, got {data.get('show_payroll_summary')}"
        print(f"✓ 'resumen de nomina' triggers show_payroll_summary=True")
    
    def test_ai_search_gastos_de_nomina_triggers_quick_pattern(self):
        """Test that 'gastos de nomina' triggers quick pattern resumen_nomina"""
        response = self.session.post(
            f"{BASE_URL}/api/search/ai",
            json={"query": "gastos de nomina"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("show_payroll_summary") == True, f"Expected show_payroll_summary=True, got {data.get('show_payroll_summary')}"
        print(f"✓ 'gastos de nomina' triggers show_payroll_summary=True")
    
    def test_ai_search_reporte_de_nomina_triggers_quick_pattern(self):
        """Test that 'reporte de nomina' triggers quick pattern resumen_nomina"""
        response = self.session.post(
            f"{BASE_URL}/api/search/ai",
            json={"query": "reporte de nomina"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("show_payroll_summary") == True, f"Expected show_payroll_summary=True, got {data.get('show_payroll_summary')}"
        print(f"✓ 'reporte de nomina' triggers show_payroll_summary=True")
    
    def test_ai_search_comparar_nomina_triggers_quick_pattern(self):
        """Test that 'comparar nomina' triggers quick pattern resumen_nomina"""
        response = self.session.post(
            f"{BASE_URL}/api/search/ai",
            json={"query": "comparar nomina"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("show_payroll_summary") == True, f"Expected show_payroll_summary=True, got {data.get('show_payroll_summary')}"
        print(f"✓ 'comparar nomina' triggers show_payroll_summary=True")
    
    def test_ai_search_resumen_nomina_returns_action_type(self):
        """Test that resumen_nomina action type is returned in ai_interpretation"""
        response = self.session.post(
            f"{BASE_URL}/api/search/ai",
            json={"query": "resumen de nomina"}
        )
        assert response.status_code == 200
        data = response.json()
        
        ai_interp = data.get("ai_interpretation", {})
        assert ai_interp.get("action") == "resumen_nomina", f"Expected action=resumen_nomina, got {ai_interp.get('action')}"
        assert ai_interp.get("confidence", 0) >= 0.9, f"Expected confidence >= 0.9, got {ai_interp.get('confidence')}"
        print(f"✓ AI interpretation returns action=resumen_nomina with confidence={ai_interp.get('confidence')}")
    
    # ============ POST /api/search/execute-action Tests ============
    
    def test_execute_action_resumen_nomina_returns_show_payroll_summary(self):
        """Test that execute-action with resumen_nomina returns show_payroll_summary:true"""
        response = self.session.post(
            f"{BASE_URL}/api/search/execute-action",
            json={
                "action_type": "resumen_nomina",
                "parameters": {}
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got {data.get('success')}"
        assert data.get("show_payroll_summary") == True, f"Expected show_payroll_summary=True, got {data.get('show_payroll_summary')}"
        assert data.get("action") == "resumen_nomina", f"Expected action=resumen_nomina, got {data.get('action')}"
        print(f"✓ Execute action resumen_nomina returns show_payroll_summary=True")
    
    def test_execute_action_resumen_nomina_no_redirect(self):
        """Test that execute-action with resumen_nomina has redirect=None (stays in search)"""
        response = self.session.post(
            f"{BASE_URL}/api/search/execute-action",
            json={
                "action_type": "resumen_nomina",
                "parameters": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("redirect") is None, f"Expected redirect=None, got {data.get('redirect')}"
        print(f"✓ Execute action resumen_nomina has redirect=None (panel shows in search)")
    
    # ============ Regression Tests - Other AI Commands Still Work ============
    
    def test_ai_search_ir_a_nomina_still_works(self):
        """REGRESSION: Test that 'ir a nomina' still triggers navegar action"""
        response = self.session.post(
            f"{BASE_URL}/api/search/ai",
            json={"query": "ir a nomina"}
        )
        assert response.status_code == 200
        data = response.json()
        
        ai_interp = data.get("ai_interpretation", {})
        assert ai_interp.get("action") == "navegar", f"Expected action=navegar, got {ai_interp.get('action')}"
        assert ai_interp.get("parameters", {}).get("destination") == "nomina", f"Expected destination=nomina"
        print(f"✓ REGRESSION: 'ir a nomina' still triggers navegar action")
    
    def test_ai_search_informational_query_still_works(self):
        """REGRESSION: Test that informational queries still return ai_answer"""
        response = self.session.post(
            f"{BASE_URL}/api/search/ai",
            json={"query": "cuantos empleados activos hay"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return ai_answer for informational queries
        ai_interp = data.get("ai_interpretation", {})
        # Either returns consultar_info action or ai_answer
        has_answer = data.get("ai_answer") is not None or ai_interp.get("action") == "consultar_info"
        assert has_answer, "Expected ai_answer or consultar_info action for informational query"
        print(f"✓ REGRESSION: Informational query returns answer or consultar_info action")
    
    def test_ai_search_aprobar_vacaciones_still_works(self):
        """REGRESSION: Test that 'aprobar vacaciones pendientes' still works"""
        response = self.session.post(
            f"{BASE_URL}/api/search/ai",
            json={"query": "aprobar vacaciones pendientes"}
        )
        assert response.status_code == 200
        data = response.json()
        
        ai_interp = data.get("ai_interpretation", {})
        assert ai_interp.get("action") == "aprobar_vacaciones", f"Expected action=aprobar_vacaciones, got {ai_interp.get('action')}"
        print(f"✓ REGRESSION: 'aprobar vacaciones pendientes' still triggers aprobar_vacaciones action")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
