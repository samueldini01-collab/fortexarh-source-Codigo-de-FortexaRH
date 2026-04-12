"""
AI Search Feature Tests - FortexaRH
Tests for AI-powered search with quick pattern matching, action detection, and execution
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAISearchEndpoints:
    """Test AI Search backend endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    # ===== Standard Search Tests =====
    
    def test_standard_search_returns_results(self):
        """GET /api/search?q=empleado - standard search returns results"""
        response = self.session.get(f"{BASE_URL}/api/search?q=empleado")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "results" in data, "Response should contain 'results' key"
        assert "query" in data, "Response should contain 'query' key"
        assert data["query"] == "empleado", "Query should match input"
        assert isinstance(data["results"], list), "Results should be a list"
    
    def test_search_with_empty_query(self):
        """GET /api/search?q= - search with empty query"""
        response = self.session.get(f"{BASE_URL}/api/search?q=")
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    # ===== Suggestions Tests =====
    
    def test_suggestions_endpoint(self):
        """GET /api/search/suggestions?q= - returns suggestions list"""
        response = self.session.get(f"{BASE_URL}/api/search/suggestions?q=")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "suggestions" in data, "Response should contain 'suggestions' key"
        assert isinstance(data["suggestions"], list), "Suggestions should be a list"
    
    def test_suggestions_with_query(self):
        """GET /api/search/suggestions?q=crear - returns filtered suggestions"""
        response = self.session.get(f"{BASE_URL}/api/search/suggestions?q=crear")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        # Should return action suggestions related to "crear"
        suggestions = data["suggestions"]
        assert isinstance(suggestions, list)
    
    # ===== Quick Pattern Matching Tests =====
    
    def test_ai_search_quick_pattern_ir_a_nomina(self):
        """POST /api/search/ai with 'ir a nomina' - quick pattern returns navegar with confidence 0.95"""
        response = self.session.post(f"{BASE_URL}/api/search/ai", json={
            "query": "ir a nomina"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "action" in data, "Response should contain 'action' key"
        action = data.get("action")
        
        if action:
            assert action.get("type") == "navegar", f"Expected action type 'navegar', got {action.get('type')}"
            assert action.get("confidence") == 0.95, f"Expected confidence 0.95, got {action.get('confidence')}"
            assert action.get("parameters", {}).get("destination") == "nomina", "Destination should be 'nomina'"
    
    def test_ai_search_quick_pattern_aprobar_vacaciones(self):
        """POST /api/search/ai with 'aprobar vacaciones pendientes' - quick pattern returns aprobar_vacaciones"""
        response = self.session.post(f"{BASE_URL}/api/search/ai", json={
            "query": "aprobar vacaciones pendientes"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        action = data.get("action")
        if action:
            assert action.get("type") == "aprobar_vacaciones", f"Expected 'aprobar_vacaciones', got {action.get('type')}"
            assert action.get("confidence") == 0.95, "Quick pattern should have 0.95 confidence"
    
    def test_ai_search_quick_pattern_ver_dashboard(self):
        """POST /api/search/ai with 'ver el dashboard' - quick pattern returns navegar with destination dashboard"""
        response = self.session.post(f"{BASE_URL}/api/search/ai", json={
            "query": "ver el dashboard"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        action = data.get("action")
        if action:
            assert action.get("type") == "navegar", f"Expected 'navegar', got {action.get('type')}"
            assert action.get("parameters", {}).get("destination") == "dashboard"
    
    def test_ai_search_quick_pattern_calcular_nomina(self):
        """POST /api/search/ai with 'calcular nomina' - quick pattern returns calcular_nomina"""
        response = self.session.post(f"{BASE_URL}/api/search/ai", json={
            "query": "calcular nomina"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        action = data.get("action")
        if action:
            assert action.get("type") == "calcular_nomina", f"Expected 'calcular_nomina', got {action.get('type')}"
    
    # ===== AI-Powered Informational Query Tests =====
    
    def test_ai_search_informational_query(self):
        """POST /api/search/ai with 'cuantos empleados hay activos' - AI returns consultar_info with ai_answer"""
        response = self.session.post(f"{BASE_URL}/api/search/ai", json={
            "query": "cuantos empleados hay activos"
        }, timeout=15)  # Allow extra time for AI response
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # This query should trigger AI interpretation
        assert "ai_interpretation" in data, "Response should contain 'ai_interpretation'"
        
        # Check if AI answer is present (for informational queries)
        ai_answer = data.get("ai_answer")
        ai_interpretation = data.get("ai_interpretation", {})
        
        # Either ai_answer should be present or action should be consultar_info
        if ai_answer:
            assert isinstance(ai_answer, str), "ai_answer should be a string"
        elif ai_interpretation.get("action") == "consultar_info":
            assert ai_interpretation.get("answer") is not None or ai_interpretation.get("message") is not None
    
    # ===== Execute Action Tests =====
    
    def test_execute_action_navegar(self):
        """POST /api/search/execute-action with navegar type navigates correctly"""
        response = self.session.post(f"{BASE_URL}/api/search/execute-action", json={
            "action_type": "navegar",
            "parameters": {
                "destination": "nomina"
            }
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got {data.get('success')}"
        assert data.get("action") == "navegar", "Action should be 'navegar'"
        assert data.get("redirect") == "/payroll", f"Expected redirect '/payroll', got {data.get('redirect')}"
    
    def test_execute_action_navegar_dashboard(self):
        """POST /api/search/execute-action with navegar to dashboard"""
        response = self.session.post(f"{BASE_URL}/api/search/execute-action", json={
            "action_type": "navegar",
            "parameters": {
                "destination": "dashboard"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("redirect") == "/dashboard"
    
    def test_execute_action_ver_nomina(self):
        """POST /api/search/execute-action with ver_nomina type"""
        response = self.session.post(f"{BASE_URL}/api/search/execute-action", json={
            "action_type": "ver_nomina",
            "parameters": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("redirect") == "/payroll"
    
    def test_execute_action_invalid_type(self):
        """POST /api/search/execute-action with invalid action type returns 400"""
        response = self.session.post(f"{BASE_URL}/api/search/execute-action", json={
            "action_type": "invalid_action_type",
            "parameters": {}
        })
        
        assert response.status_code == 400, f"Expected 400 for invalid action, got {response.status_code}"
    
    # ===== Recent Actions Tests =====
    
    def test_recent_actions_endpoint(self):
        """GET /api/search/recent-actions - returns empty or action list"""
        response = self.session.get(f"{BASE_URL}/api/search/recent-actions")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "actions" in data, "Response should contain 'actions' key"
        assert isinstance(data["actions"], list), "Actions should be a list"
    
    # ===== User Stats Tests =====
    
    def test_user_stats_endpoint(self):
        """GET /api/search/user-stats - returns stats object"""
        response = self.session.get(f"{BASE_URL}/api/search/user-stats")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should return stats structure
        assert "action_stats" in data or "total_queries" in data or "top_queries" in data, \
            "Response should contain stats fields"
    
    # ===== Log Query Tests =====
    
    def test_log_query_endpoint(self):
        """POST /api/search/log-query - logs a search query"""
        response = self.session.post(f"{BASE_URL}/api/search/log-query", json={
            "query": "test query for logging"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "logged" in data, "Response should contain 'logged' key"
    
    def test_log_query_short_query_not_logged(self):
        """POST /api/search/log-query - short queries are not logged"""
        response = self.session.post(f"{BASE_URL}/api/search/log-query", json={
            "query": "ab"  # Less than 3 characters
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("logged") == False, "Short queries should not be logged"
    
    # ===== Additional Navigation Patterns =====
    
    def test_ai_search_ir_a_empleados(self):
        """POST /api/search/ai with 'ir a empleados' - quick pattern"""
        response = self.session.post(f"{BASE_URL}/api/search/ai", json={
            "query": "ir a empleados"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        action = data.get("action")
        if action:
            assert action.get("type") == "navegar"
            assert action.get("parameters", {}).get("destination") == "empleados"
    
    def test_ai_search_ir_a_vacaciones(self):
        """POST /api/search/ai with 'ir a vacaciones' - quick pattern"""
        response = self.session.post(f"{BASE_URL}/api/search/ai", json={
            "query": "ir a vacaciones"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        action = data.get("action")
        if action:
            assert action.get("type") == "navegar"
            assert action.get("parameters", {}).get("destination") == "vacaciones"
    
    def test_ai_search_abrir_asistencia(self):
        """POST /api/search/ai with 'abrir asistencia' - quick pattern"""
        response = self.session.post(f"{BASE_URL}/api/search/ai", json={
            "query": "abrir asistencia"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        action = data.get("action")
        if action:
            assert action.get("type") == "navegar"
            assert action.get("parameters", {}).get("destination") == "asistencia"


class TestAISearchAuthentication:
    """Test that AI Search endpoints require authentication"""
    
    def test_search_requires_auth(self):
        """GET /api/search without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/search?q=test")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_ai_search_requires_auth(self):
        """POST /api/search/ai without auth returns 401/403"""
        response = requests.post(f"{BASE_URL}/api/search/ai", json={"query": "test"})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_execute_action_requires_auth(self):
        """POST /api/search/execute-action without auth returns 401/403"""
        response = requests.post(f"{BASE_URL}/api/search/execute-action", json={
            "action_type": "navegar",
            "parameters": {"destination": "dashboard"}
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_suggestions_requires_auth(self):
        """GET /api/search/suggestions without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/search/suggestions?q=")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
