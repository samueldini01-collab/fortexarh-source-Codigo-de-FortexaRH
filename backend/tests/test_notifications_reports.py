"""
Test Suite for New Features - FortexaRH
1. Notifications System (in-app notifications with bell icon)
2. Advanced PDF Reports (Payroll, Attendance, Evaluations)
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"

# Known payroll periods from context
KNOWN_PERIOD_IDS = ["period_02989e9e3331", "period_6a079d88c0c4"]


class TestAuth:
    """Authentication tests"""
    
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


@pytest.fixture(scope="module")
def auth_headers():
    """Get auth headers for all tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["token"]
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


# ============== NOTIFICATIONS SYSTEM TESTS ==============

class TestNotificationsSystem:
    """Test in-app notification system"""
    
    def test_get_notifications_list(self, auth_headers):
        """Test GET /api/notifications - Get list of notifications"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If there are notifications, verify structure
        if len(data) > 0:
            notif = data[0]
            assert "notification_id" in notif
            assert "title" in notif
            assert "message" in notif
            assert "type" in notif
            assert "created_at" in notif
            print(f"Found {len(data)} notifications")
    
    def test_get_notifications_with_limit(self, auth_headers):
        """Test GET /api/notifications with limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/notifications?limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_notifications_unread_only(self, auth_headers):
        """Test GET /api/notifications with unread_only filter"""
        response = requests.get(
            f"{BASE_URL}/api/notifications?unread_only=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All returned notifications should be unread
        for notif in data:
            assert notif.get("is_read") == False, "Unread filter should return only unread notifications"
    
    def test_get_unread_count(self, auth_headers):
        """Test GET /api/notifications/count - Get unread count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/count",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "unread_count" in data, "Response should contain unread_count"
        assert isinstance(data["unread_count"], int), "unread_count should be an integer"
        assert data["unread_count"] >= 0, "unread_count should be non-negative"
        print(f"Unread count: {data['unread_count']}")
    
    def test_mark_notifications_as_read(self, auth_headers):
        """Test POST /api/notifications/mark-read - Mark specific notifications as read"""
        # First get some notifications
        get_response = requests.get(
            f"{BASE_URL}/api/notifications?limit=5",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        notifications = get_response.json()
        
        if len(notifications) > 0:
            # Get IDs of unread notifications
            unread_ids = [n["notification_id"] for n in notifications if not n.get("is_read")]
            
            if len(unread_ids) > 0:
                # Mark them as read
                response = requests.post(
                    f"{BASE_URL}/api/notifications/mark-read",
                    headers=auth_headers,
                    json={"notification_ids": unread_ids[:2]}  # Mark first 2
                )
                assert response.status_code == 200, f"Failed: {response.text}"
                data = response.json()
                assert "marked_count" in data
                print(f"Marked {data['marked_count']} notifications as read")
            else:
                print("No unread notifications to mark")
        else:
            print("No notifications found to test mark-read")
    
    def test_mark_all_notifications_as_read(self, auth_headers):
        """Test POST /api/notifications/mark-all-read - Mark all as read"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/mark-all-read",
            headers=auth_headers,
            json={}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "marked_count" in data
        print(f"Marked all ({data['marked_count']}) notifications as read")
        
        # Verify count is now 0
        count_response = requests.get(
            f"{BASE_URL}/api/notifications/count",
            headers=auth_headers
        )
        assert count_response.status_code == 200
        count_data = count_response.json()
        assert count_data["unread_count"] == 0, "After mark-all-read, unread count should be 0"


class TestNotificationTriggers:
    """Test notification trigger endpoints"""
    
    def test_trigger_payroll_approval_notification(self, auth_headers):
        """Test POST /api/notifications/trigger/payroll-approval"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/trigger/payroll-approval",
            headers=auth_headers,
            params={
                "period_id": "test_period_123",
                "period_description": "Test Period Jan 2026"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "notification_id" in data
        print(f"Created notification: {data['notification_id']}")
    
    def test_trigger_payroll_available_notification(self, auth_headers):
        """Test POST /api/notifications/trigger/payroll-available"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/trigger/payroll-available",
            headers=auth_headers,
            params={
                "period_id": "test_period_123",
                "period_description": "Test Period Jan 2026"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"Payroll available notification sent")
    
    def test_trigger_vacation_status_notification(self, auth_headers):
        """Test POST /api/notifications/trigger/vacation-status"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/trigger/vacation-status",
            headers=auth_headers,
            params={
                "employee_id": "test_emp_123",
                "employee_name": "Test Employee",
                "status": "approved",
                "vacation_dates": "2026-02-01 al 2026-02-05"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
    
    def test_trigger_evaluation_scheduled_notification(self, auth_headers):
        """Test POST /api/notifications/trigger/evaluation-scheduled"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/trigger/evaluation-scheduled",
            headers=auth_headers,
            params={
                "employee_id": "test_emp_123",
                "employee_name": "Test Employee",
                "evaluation_type": "Anual",
                "scheduled_date": "2026-03-15"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data


# ============== ADVANCED REPORTS TESTS ==============

class TestAdvancedReportsAvailable:
    """Test available reports endpoint"""
    
    def test_get_available_reports(self, auth_headers):
        """Test GET /api/reports-advanced/available - List available reports"""
        response = requests.get(
            f"{BASE_URL}/api/reports-advanced/available",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "reports" in data, "Response should contain 'reports'"
        assert "filters" in data, "Response should contain 'filters'"
        
        reports = data["reports"]
        assert isinstance(reports, list)
        assert len(reports) >= 3, "Should have at least 3 report types"
        
        # Verify report types
        report_ids = [r["id"] for r in reports]
        assert "payroll" in report_ids, "Should have payroll report"
        assert "attendance" in report_ids, "Should have attendance report"
        assert "evaluations" in report_ids, "Should have evaluations report"
        
        # Verify each report has required fields
        for report in reports:
            assert "id" in report
            assert "name" in report
            assert "description" in report
            assert "endpoint" in report
        
        print(f"Available reports: {report_ids}")
        print(f"Filters: {list(data['filters'].keys())}")


class TestPayrollPDFReport:
    """Test payroll PDF generation"""
    
    def test_generate_payroll_pdf_with_known_period(self, auth_headers):
        """Test GET /api/reports-advanced/payroll/{period_id}/pdf"""
        # Use known approved period
        period_id = KNOWN_PERIOD_IDS[0]
        
        response = requests.get(
            f"{BASE_URL}/api/reports-advanced/payroll/{period_id}/pdf",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # Verify it's a PDF
            content_type = response.headers.get("Content-Type", "")
            assert "application/pdf" in content_type, f"Expected PDF, got {content_type}"
            
            # Verify content disposition
            content_disp = response.headers.get("Content-Disposition", "")
            assert "attachment" in content_disp, "Should be downloadable attachment"
            assert ".pdf" in content_disp, "Filename should have .pdf extension"
            
            # Verify PDF content starts with PDF header
            assert response.content[:4] == b'%PDF', "Content should be valid PDF"
            print(f"PDF generated successfully, size: {len(response.content)} bytes")
        elif response.status_code == 404:
            print(f"Period {period_id} not found - may have been deleted")
        else:
            pytest.fail(f"Unexpected status: {response.status_code}, {response.text}")
    
    def test_generate_payroll_pdf_invalid_period(self, auth_headers):
        """Test PDF generation with invalid period ID"""
        response = requests.get(
            f"{BASE_URL}/api/reports-advanced/payroll/invalid_period_xyz/pdf",
            headers=auth_headers
        )
        assert response.status_code == 404, "Should return 404 for invalid period"


class TestAttendancePDFReport:
    """Test attendance PDF generation"""
    
    def test_generate_attendance_pdf(self, auth_headers):
        """Test GET /api/reports-advanced/attendance/pdf"""
        # Use date range for last month
        today = datetime.now()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/reports-advanced/attendance/pdf",
            headers=auth_headers,
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify it's a PDF
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF, got {content_type}"
        
        # Verify PDF content
        assert response.content[:4] == b'%PDF', "Content should be valid PDF"
        print(f"Attendance PDF generated, size: {len(response.content)} bytes")
    
    def test_generate_attendance_pdf_with_department_filter(self, auth_headers):
        """Test attendance PDF with department filter"""
        today = datetime.now()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/reports-advanced/attendance/pdf",
            headers=auth_headers,
            params={
                "start_date": start_date,
                "end_date": end_date,
                "department": "Tecnología"
            }
        )
        
        # Should work even if department has no data
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "application/pdf" in response.headers.get("Content-Type", "")


class TestEvaluationsPDFReport:
    """Test evaluations PDF generation"""
    
    def test_generate_evaluations_pdf(self, auth_headers):
        """Test GET /api/reports-advanced/evaluations/pdf"""
        response = requests.get(
            f"{BASE_URL}/api/reports-advanced/evaluations/pdf",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # Verify it's a PDF
            content_type = response.headers.get("Content-Type", "")
            assert "application/pdf" in content_type, f"Expected PDF, got {content_type}"
            
            # Verify PDF content
            assert response.content[:4] == b'%PDF', "Content should be valid PDF"
            print(f"Evaluations PDF generated, size: {len(response.content)} bytes")
        elif response.status_code == 404:
            # No evaluations found - this is acceptable
            print("No evaluations found - 404 is acceptable")
        else:
            pytest.fail(f"Unexpected status: {response.status_code}, {response.text}")
    
    def test_generate_evaluations_pdf_with_cycle(self, auth_headers):
        """Test evaluations PDF with cycle_id filter"""
        # First get available cycles
        available_response = requests.get(
            f"{BASE_URL}/api/reports-advanced/available",
            headers=auth_headers
        )
        
        if available_response.status_code == 200:
            data = available_response.json()
            cycles = data.get("filters", {}).get("evaluation_cycles", [])
            
            if len(cycles) > 0:
                cycle_id = cycles[0].get("cycle_id")
                response = requests.get(
                    f"{BASE_URL}/api/reports-advanced/evaluations/pdf",
                    headers=auth_headers,
                    params={"cycle_id": cycle_id}
                )
                # Should return 200 or 404 (no evaluations in cycle)
                assert response.status_code in [200, 404], f"Unexpected: {response.status_code}"
            else:
                print("No evaluation cycles found")


# ============== INTEGRATION TESTS ==============

class TestNotificationsReportsIntegration:
    """Integration tests for notifications and reports"""
    
    def test_notifications_after_report_generation(self, auth_headers):
        """Test that notifications work after generating reports"""
        # Generate a report
        today = datetime.now()
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        report_response = requests.get(
            f"{BASE_URL}/api/reports-advanced/attendance/pdf",
            headers=auth_headers,
            params={"start_date": start_date, "end_date": end_date}
        )
        assert report_response.status_code == 200
        
        # Notifications should still work
        notif_response = requests.get(
            f"{BASE_URL}/api/notifications/count",
            headers=auth_headers
        )
        assert notif_response.status_code == 200
        assert "unread_count" in notif_response.json()
    
    def test_full_notification_workflow(self, auth_headers):
        """Test complete notification workflow: create -> list -> mark read"""
        # 1. Trigger a notification
        trigger_response = requests.post(
            f"{BASE_URL}/api/notifications/trigger/payroll-approval",
            headers=auth_headers,
            params={
                "period_id": "workflow_test_period",
                "period_description": "Workflow Test Period"
            }
        )
        assert trigger_response.status_code == 200
        
        # 2. Get notifications list
        list_response = requests.get(
            f"{BASE_URL}/api/notifications?limit=10",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        notifications = list_response.json()
        
        # 3. Get unread count
        count_response = requests.get(
            f"{BASE_URL}/api/notifications/count",
            headers=auth_headers
        )
        assert count_response.status_code == 200
        
        # 4. Mark all as read
        mark_response = requests.post(
            f"{BASE_URL}/api/notifications/mark-all-read",
            headers=auth_headers,
            json={}
        )
        assert mark_response.status_code == 200
        
        print("Full notification workflow completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
