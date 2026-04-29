"""
Tests for Payslip PDF Generation and HR Alerts System
- GET /api/payroll/payslip/{entry_id}/pdf - Payslip PDF generation
- GET /api/hr-alerts - HR Alerts system
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPayslipPDFGeneration:
    """Tests for payslip PDF generation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_get_payroll_periods(self):
        """Test getting payroll periods to find entry_id"""
        response = self.session.get(f"{BASE_URL}/api/payroll/periods")
        assert response.status_code == 200
        periods = response.json()
        assert isinstance(periods, list)
        print(f"Found {len(periods)} payroll periods")
        return periods
    
    def test_get_period_with_entries(self):
        """Test getting a period with entries to find entry_id"""
        periods = self.test_get_payroll_periods()
        
        # Find a period with entries
        for period in periods:
            if period.get("employee_count", 0) > 0:
                period_id = period.get("period_id")
                response = self.session.get(f"{BASE_URL}/api/payroll/periods/{period_id}")
                assert response.status_code == 200
                period_data = response.json()
                entries = period_data.get("entries", [])
                if entries:
                    print(f"Found period {period_id} with {len(entries)} entries")
                    return period_data
        
        pytest.skip("No payroll periods with entries found")
    
    def test_payslip_pdf_generation_valid_entry(self):
        """Test PDF generation for a valid payroll entry"""
        period_data = self.test_get_period_with_entries()
        entries = period_data.get("entries", [])
        
        if not entries:
            pytest.skip("No entries found in any period")
        
        entry_id = entries[0].get("entry_id")
        print(f"Testing PDF generation for entry_id: {entry_id}")
        
        response = self.session.get(f"{BASE_URL}/api/payroll/payslip/{entry_id}/pdf")
        
        # Check response
        assert response.status_code == 200, f"PDF generation failed: {response.text}"
        
        # Verify it's a PDF
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF, got {content_type}"
        
        # Verify content disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition, "Missing attachment header"
        assert ".pdf" in content_disposition, "Missing .pdf extension in filename"
        
        # Verify PDF content starts with PDF magic bytes
        content = response.content
        assert content[:4] == b'%PDF', "Response is not a valid PDF file"
        
        print(f"PDF generated successfully, size: {len(content)} bytes")
        print(f"Content-Disposition: {content_disposition}")
    
    def test_payslip_pdf_nonexistent_entry(self):
        """Test PDF generation for non-existent entry returns 404"""
        response = self.session.get(f"{BASE_URL}/api/payroll/payslip/nonexistent_entry_12345/pdf")
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent entry")
    
    def test_payslip_pdf_unauthenticated(self):
        """Test PDF generation without authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/payroll/payslip/pe_test123/pdf")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Correctly denied unauthenticated access")


class TestHRAlerts:
    """Tests for HR Alerts system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_get_hr_alerts(self):
        """Test getting HR alerts"""
        response = self.session.get(f"{BASE_URL}/api/hr-alerts")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response structure
        assert "alerts" in data, "Missing 'alerts' key in response"
        assert "summary" in data, "Missing 'summary' key in response"
        
        alerts = data["alerts"]
        summary = data["summary"]
        
        # Verify alerts is a list
        assert isinstance(alerts, list), "Alerts should be a list"
        
        # Verify summary structure
        assert "total" in summary, "Missing 'total' in summary"
        assert "critical" in summary, "Missing 'critical' in summary"
        assert "high" in summary, "Missing 'high' in summary"
        assert "medium" in summary, "Missing 'medium' in summary"
        assert "low" in summary, "Missing 'low' in summary"
        
        print(f"HR Alerts Summary: {summary}")
        print(f"Total alerts: {len(alerts)}")
        
        return data
    
    def test_hr_alerts_structure(self):
        """Test that each alert has required fields"""
        data = self.test_get_hr_alerts()
        alerts = data["alerts"]
        
        if not alerts:
            print("No alerts found - this is valid if no employees have upcoming events")
            return
        
        # Check first alert structure
        alert = alerts[0]
        required_fields = ["type", "priority", "employee_id", "employee_name", "message", "date", "days_remaining"]
        
        for field in required_fields:
            assert field in alert, f"Missing required field '{field}' in alert"
        
        # Verify type is one of expected values
        valid_types = ["contract_expiring", "probation_ending", "work_anniversary", "birthday"]
        assert alert["type"] in valid_types, f"Invalid alert type: {alert['type']}"
        
        # Verify priority is one of expected values
        valid_priorities = ["critical", "high", "medium", "low"]
        assert alert["priority"] in valid_priorities, f"Invalid priority: {alert['priority']}"
        
        print(f"First alert: {alert['type']} - {alert['employee_name']} - {alert['message']}")
    
    def test_hr_alerts_sorted_by_priority(self):
        """Test that alerts are sorted by priority"""
        data = self.test_get_hr_alerts()
        alerts = data["alerts"]
        
        if len(alerts) < 2:
            print("Not enough alerts to verify sorting")
            return
        
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        for i in range(len(alerts) - 1):
            current_priority = priority_order.get(alerts[i]["priority"], 4)
            next_priority = priority_order.get(alerts[i + 1]["priority"], 4)
            
            # If same priority, check days_remaining
            if current_priority == next_priority:
                current_days = alerts[i].get("days_remaining", 999)
                next_days = alerts[i + 1].get("days_remaining", 999)
                assert current_days <= next_days, f"Alerts not sorted by days_remaining within same priority"
            else:
                assert current_priority <= next_priority, f"Alerts not sorted by priority"
        
        print("Alerts are correctly sorted by priority and days_remaining")
    
    def test_hr_alerts_summary_counts(self):
        """Test that summary counts match actual alerts"""
        data = self.test_get_hr_alerts()
        alerts = data["alerts"]
        summary = data["summary"]
        
        # Count alerts by priority
        actual_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for alert in alerts:
            priority = alert.get("priority")
            if priority in actual_counts:
                actual_counts[priority] += 1
        
        # Verify counts match
        assert summary["total"] == len(alerts), f"Total mismatch: {summary['total']} vs {len(alerts)}"
        assert summary["critical"] == actual_counts["critical"], f"Critical count mismatch"
        assert summary["high"] == actual_counts["high"], f"High count mismatch"
        assert summary["medium"] == actual_counts["medium"], f"Medium count mismatch"
        assert summary["low"] == actual_counts["low"], f"Low count mismatch"
        
        print(f"Summary counts verified: {actual_counts}")
    
    def test_hr_alerts_unauthenticated(self):
        """Test HR alerts without authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/hr-alerts")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Correctly denied unauthenticated access")


class TestPayrollEntryDetails:
    """Tests to verify payroll entry data for PDF generation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_payroll_entry_has_required_fields(self):
        """Test that payroll entries have all fields needed for PDF"""
        # Get periods
        response = self.session.get(f"{BASE_URL}/api/payroll/periods")
        assert response.status_code == 200
        periods = response.json()
        
        # Find a period with entries
        for period in periods:
            if period.get("employee_count", 0) > 0:
                period_id = period.get("period_id")
                response = self.session.get(f"{BASE_URL}/api/payroll/periods/{period_id}")
                assert response.status_code == 200
                period_data = response.json()
                entries = period_data.get("entries", [])
                
                if entries:
                    entry = entries[0]
                    
                    # Check required fields for PDF
                    required_fields = [
                        "entry_id", "employee_id", "employee_name",
                        "base_salary", "gross_salary", "net_salary",
                        "sfs_employee", "afp_employee", "isr"
                    ]
                    
                    for field in required_fields:
                        assert field in entry, f"Missing required field '{field}' in entry"
                    
                    print(f"Entry {entry['entry_id']} has all required fields")
                    print(f"  Employee: {entry['employee_name']}")
                    print(f"  Base Salary: {entry['base_salary']}")
                    print(f"  Gross Salary: {entry['gross_salary']}")
                    print(f"  Net Salary: {entry['net_salary']}")
                    print(f"  SFS: {entry['sfs_employee']}, AFP: {entry['afp_employee']}, ISR: {entry['isr']}")
                    return
        
        pytest.skip("No payroll entries found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
