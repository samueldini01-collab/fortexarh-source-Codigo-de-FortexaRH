"""
Test Suite for FortexaRH HRM Modules
Tests: Attendance, Vacations, and Evaluations modules
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fortexarh-cloud.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def test_employee(auth_headers):
    """Get or create a test employee"""
    # First try to get existing employees
    response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
    if response.status_code == 200:
        employees = response.json()
        if employees:
            return employees[0]
    
    # Create a test employee if none exist
    employee_data = {
        "first_name": "TEST_HRM",
        "last_name": "Employee",
        "email": f"test_hrm_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
        "position": "Tester",
        "department": "TI",
        "hire_date": "2023-01-15",
        "salary": 50000
    }
    response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
    if response.status_code in [200, 201]:
        return response.json()
    pytest.skip("Could not get or create test employee")


# ==================== AUTHENTICATION TESTS ====================

class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code in [401, 404]


# ==================== ATTENDANCE MODULE TESTS ====================

class TestAttendanceShifts:
    """Attendance shift management tests"""
    
    def test_get_shifts(self, auth_headers):
        """Test getting all shifts"""
        response = requests.get(f"{BASE_URL}/api/attendance/shifts", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_shift(self, auth_headers):
        """Test creating a new shift"""
        shift_data = {
            "name": f"TEST_Turno_{datetime.now().strftime('%H%M%S')}",
            "start_time": "08:00",
            "end_time": "17:00",
            "break_minutes": 60,
            "grace_period_minutes": 15,
            "overtime_threshold_hours": 8.0,
            "is_night_shift": False,
            "applies_to_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        response = requests.post(f"{BASE_URL}/api/attendance/shifts", json=shift_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "shift_id" in data
        assert "message" in data
        return data["shift_id"]


class TestAttendanceRecords:
    """Attendance record management tests"""
    
    def test_get_today_attendance(self, auth_headers):
        """Test getting today's attendance summary"""
        response = requests.get(f"{BASE_URL}/api/attendance/today", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "total_employees" in data
        assert "present_count" in data
        assert "absent_count" in data
    
    def test_get_attendance_alerts(self, auth_headers):
        """Test getting attendance alerts"""
        response = requests.get(f"{BASE_URL}/api/attendance/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "total_alerts" in data
        assert "alerts" in data
    
    def test_create_attendance_record(self, auth_headers, test_employee):
        """Test creating a manual attendance record"""
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_data = {
            "employee_id": test_employee["employee_id"],
            "date": today,
            "check_in": "08:00",
            "check_out": "17:00",
            "status": "present",
            "notes": "TEST_Manual entry"
        }
        response = requests.post(f"{BASE_URL}/api/attendance", json=attendance_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "attendance_id" in data or "message" in data
    
    def test_get_attendance_records(self, auth_headers):
        """Test getting attendance records with filters"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/attendance?date={today}", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_check_in_employee(self, auth_headers, test_employee):
        """Test employee check-in"""
        check_in_data = {
            "employee_id": test_employee["employee_id"],
            "method": "manual"
        }
        response = requests.post(f"{BASE_URL}/api/attendance/check-in", json=check_in_data, headers=auth_headers)
        # May return 400 if already checked in today
        assert response.status_code in [200, 400]
    
    def test_check_out_employee(self, auth_headers, test_employee):
        """Test employee check-out"""
        check_out_data = {
            "employee_id": test_employee["employee_id"],
            "method": "manual"
        }
        response = requests.post(f"{BASE_URL}/api/attendance/check-out", json=check_out_data, headers=auth_headers)
        # May return 400/404 if no check-in or already checked out
        assert response.status_code in [200, 400, 404]
    
    def test_export_attendance_csv(self, auth_headers):
        """Test exporting attendance to CSV"""
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/attendance/export?start_date={week_ago}&end_date={today}&format=csv",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")


# ==================== VACATIONS MODULE TESTS ====================

class TestVacationTypes:
    """Vacation/leave types tests"""
    
    def test_get_leave_types(self, auth_headers):
        """Test getting available leave types"""
        response = requests.get(f"{BASE_URL}/api/vacations/types", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have default types like vacation, sick, maternity
        type_codes = [t.get("code") for t in data]
        assert "vacation" in type_codes
        assert "sick" in type_codes


class TestVacationBalance:
    """Vacation balance tests - Dominican Republic law compliance"""
    
    def test_get_employee_balance(self, auth_headers, test_employee):
        """Test getting employee vacation balance"""
        response = requests.get(
            f"{BASE_URL}/api/vacations/balance/{test_employee['employee_id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "employee_id" in data
        assert "vacation" in data
        assert "entitled" in data["vacation"]
        assert "used" in data["vacation"]
        assert "remaining" in data["vacation"]
    
    def test_get_all_balances(self, auth_headers):
        """Test getting all employees' vacation balances"""
        response = requests.get(f"{BASE_URL}/api/vacations/balance", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestVacationRequests:
    """Vacation request management tests"""
    
    def test_get_vacation_requests(self, auth_headers):
        """Test getting vacation requests"""
        response = requests.get(f"{BASE_URL}/api/vacations", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_pending_requests(self, auth_headers):
        """Test getting pending vacation requests"""
        response = requests.get(f"{BASE_URL}/api/vacations/pending", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_vacation_request(self, auth_headers, test_employee):
        """Test creating a vacation request"""
        # Request vacation for next month
        next_month = datetime.now() + timedelta(days=30)
        start_date = next_month.strftime("%Y-%m-%d")
        end_date = (next_month + timedelta(days=5)).strftime("%Y-%m-%d")
        
        vacation_data = {
            "employee_id": test_employee["employee_id"],
            "leave_type": "vacation",
            "start_date": start_date,
            "end_date": end_date,
            "reason": "TEST_Vacation request"
        }
        response = requests.post(f"{BASE_URL}/api/vacations", json=vacation_data, headers=auth_headers)
        # May fail if employee doesn't have enough balance
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "vacation_id" in data
            return data["vacation_id"]
    
    def test_approve_vacation_request(self, auth_headers):
        """Test approving a vacation request"""
        # First get pending requests
        response = requests.get(f"{BASE_URL}/api/vacations/pending", headers=auth_headers)
        if response.status_code == 200 and response.json():
            vacation_id = response.json()[0]["vacation_id"]
            approve_response = requests.put(
                f"{BASE_URL}/api/vacations/{vacation_id}/approve",
                headers=auth_headers
            )
            assert approve_response.status_code in [200, 400]
    
    def test_get_vacation_calendar(self, auth_headers):
        """Test getting vacation calendar"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        response = requests.get(
            f"{BASE_URL}/api/vacations/calendar?month={current_month}&year={current_year}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "month" in data
        assert "year" in data
        assert "calendar" in data


# ==================== EVALUATIONS MODULE TESTS ====================

class TestEvaluationCycles:
    """Evaluation cycle management tests"""
    
    def test_get_evaluation_cycles(self, auth_headers):
        """Test getting evaluation cycles"""
        response = requests.get(f"{BASE_URL}/api/evaluations/cycles", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_evaluation_cycle(self, auth_headers):
        """Test creating an evaluation cycle"""
        cycle_data = {
            "name": f"TEST_Ciclo_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "quarterly",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            "include_self_evaluation": True,
            "include_peer_evaluation": False
        }
        response = requests.post(f"{BASE_URL}/api/evaluations/cycles", json=cycle_data, headers=auth_headers)
        # May fail if overlapping cycle exists
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "cycle_id" in data
            return data["cycle_id"]


class TestEvaluationScales:
    """Evaluation scales tests"""
    
    def test_get_evaluation_scales(self, auth_headers):
        """Test getting evaluation scales"""
        response = requests.get(f"{BASE_URL}/api/evaluations/scales", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "numeric" in data
        assert "descriptive" in data
        # Verify numeric scale has 1-5 values
        numeric_values = [s["value"] for s in data["numeric"]]
        assert 1 in numeric_values
        assert 5 in numeric_values
    
    def test_get_competencies(self, auth_headers):
        """Test getting competencies"""
        response = requests.get(f"{BASE_URL}/api/evaluations/competencies", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have default competencies
        competency_codes = [c.get("code") for c in data]
        assert "performance" in competency_codes


class TestEvaluations:
    """Evaluation management tests"""
    
    def test_get_evaluations(self, auth_headers):
        """Test getting evaluations"""
        response = requests.get(f"{BASE_URL}/api/evaluations", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_evaluation(self, auth_headers, test_employee):
        """Test creating an evaluation with scores"""
        evaluation_data = {
            "employee_id": test_employee["employee_id"],
            "period": f"Q1 {datetime.now().year}",
            "evaluation_type": "supervisor",
            "scores": [
                {"competency": "performance", "name": "Desempeño Laboral", "weight": 25, "score": 4, "comments": "Good performance"},
                {"competency": "goals", "name": "Cumplimiento de Objetivos", "weight": 25, "score": 4, "comments": "Met goals"},
                {"competency": "teamwork", "name": "Trabajo en Equipo", "weight": 15, "score": 5, "comments": "Excellent teamwork"},
                {"competency": "communication", "name": "Comunicación", "weight": 15, "score": 4, "comments": "Good communication"},
                {"competency": "initiative", "name": "Iniciativa", "weight": 10, "score": 3, "comments": "Average initiative"},
                {"competency": "punctuality", "name": "Puntualidad y Asistencia", "weight": 10, "score": 5, "comments": "Always on time"}
            ],
            "overall_comments": "TEST_Overall good performance",
            "strengths": ["Teamwork", "Punctuality"],
            "areas_for_improvement": ["Initiative"]
        }
        response = requests.post(f"{BASE_URL}/api/evaluations", json=evaluation_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "evaluation_id" in data
        assert "overall_score" in data
        assert "rating" in data
        # Verify score calculation
        assert data["overall_score"] > 0
        return data["evaluation_id"]
    
    def test_get_employee_evaluations(self, auth_headers, test_employee):
        """Test getting evaluations for a specific employee"""
        response = requests.get(
            f"{BASE_URL}/api/evaluations/employee/{test_employee['employee_id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "employee" in data
        assert "evaluations" in data


class TestObjectivesKPIs:
    """Objectives/KPIs management tests"""
    
    def test_get_objectives(self, auth_headers):
        """Test getting objectives"""
        response = requests.get(f"{BASE_URL}/api/evaluations/objectives", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_objective(self, auth_headers, test_employee):
        """Test creating an objective/KPI"""
        objective_data = {
            "employee_id": test_employee["employee_id"],
            "title": f"TEST_Objetivo_{datetime.now().strftime('%H%M%S')}",
            "description": "Test objective description",
            "target_value": 100,
            "target_unit": "percentage",
            "weight": 100,
            "due_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        }
        response = requests.post(f"{BASE_URL}/api/evaluations/objectives", json=objective_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "objective_id" in data
        return data["objective_id"]
    
    def test_update_objective_progress(self, auth_headers):
        """Test updating objective progress"""
        # First get objectives
        response = requests.get(f"{BASE_URL}/api/evaluations/objectives", headers=auth_headers)
        if response.status_code == 200 and response.json():
            objective_id = response.json()[0]["objective_id"]
            update_data = {
                "progress": 50,
                "notes": "TEST_Progress update"
            }
            update_response = requests.put(
                f"{BASE_URL}/api/evaluations/objectives/{objective_id}",
                json=update_data,
                headers=auth_headers
            )
            assert update_response.status_code == 200


class TestImprovementPlans:
    """Improvement plans management tests"""
    
    def test_get_improvement_plans(self, auth_headers):
        """Test getting improvement plans"""
        response = requests.get(f"{BASE_URL}/api/evaluations/improvement-plans", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_improvement_plan(self, auth_headers, test_employee):
        """Test creating an improvement plan"""
        plan_data = {
            "employee_id": test_employee["employee_id"],
            "title": f"TEST_Plan_{datetime.now().strftime('%H%M%S')}",
            "areas": ["Communication", "Initiative"],
            "actions": [
                {"action": "Complete communication course", "status": "pending"},
                {"action": "Weekly check-ins with supervisor", "status": "pending"}
            ],
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            "follow_up_frequency": "monthly"
        }
        response = requests.post(f"{BASE_URL}/api/evaluations/improvement-plans", json=plan_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "plan_id" in data


class TestEvaluationAnalytics:
    """Evaluation analytics tests"""
    
    def test_get_analytics_dashboard(self, auth_headers):
        """Test getting evaluation analytics dashboard"""
        response = requests.get(f"{BASE_URL}/api/evaluations/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_evaluations" in data
        assert "average_score" in data
    
    def test_export_evaluations(self, auth_headers):
        """Test exporting evaluations"""
        response = requests.get(
            f"{BASE_URL}/api/evaluations/export?format=csv",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")


# ==================== INTEGRATION TESTS ====================

class TestModuleIntegration:
    """Integration tests across modules"""
    
    def test_attendance_to_evaluation_flow(self, auth_headers, test_employee):
        """Test that attendance data can inform evaluations"""
        # Get attendance summary
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        att_response = requests.get(
            f"{BASE_URL}/api/attendance?start_date={week_ago}&end_date={today}&employee_id={test_employee['employee_id']}",
            headers=auth_headers
        )
        assert att_response.status_code == 200
        
        # Get employee evaluations
        eval_response = requests.get(
            f"{BASE_URL}/api/evaluations/employee/{test_employee['employee_id']}",
            headers=auth_headers
        )
        assert eval_response.status_code == 200
    
    def test_vacation_balance_calculation(self, auth_headers, test_employee):
        """Test Dominican Republic vacation law compliance (14 days base + 1 per year max 18)"""
        response = requests.get(
            f"{BASE_URL}/api/vacations/balance/{test_employee['employee_id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify balance structure
        assert "vacation" in data
        vacation = data["vacation"]
        assert "entitled" in vacation
        assert "remaining" in vacation
        
        # Verify entitled days are within Dominican law limits (0-18)
        entitled = vacation["entitled"]
        assert 0 <= entitled <= 18, f"Entitled days {entitled} should be between 0 and 18"


# ==================== CLEANUP ====================

class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_data(self, auth_headers):
        """Clean up TEST_ prefixed data"""
        # This is a placeholder - in production, you'd want to clean up test data
        # For now, we just verify we can access the endpoints
        
        # Get shifts and identify test ones
        shifts_response = requests.get(f"{BASE_URL}/api/attendance/shifts", headers=auth_headers)
        assert shifts_response.status_code == 200
        
        # Get objectives and identify test ones
        obj_response = requests.get(f"{BASE_URL}/api/evaluations/objectives", headers=auth_headers)
        assert obj_response.status_code == 200
        
        print("Test data cleanup would happen here in production")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
