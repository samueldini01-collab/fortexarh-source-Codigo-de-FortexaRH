"""
Support Admin Panel API Tests
Tests for support ticket management endpoints:
- GET /api/support/stats - Ticket statistics
- GET /api/support/tickets - List tickets with filters
- GET /api/support/tickets/{ticket_id} - Ticket detail
- POST /api/support/tickets/{ticket_id}/respond - Add response to ticket
- PATCH /api/support/tickets/{ticket_id}/status - Update ticket status
- PATCH /api/support/tickets/{ticket_id}/priority - Update ticket priority
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"


class TestSupportStats:
    """Tests for GET /api/support/stats endpoint"""
    
    def test_get_stats_returns_200(self):
        """Stats endpoint should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/support/stats")
        assert response.status_code == 200
        
    def test_get_stats_structure(self):
        """Stats should contain required fields"""
        response = requests.get(f"{BASE_URL}/api/support/stats")
        data = response.json()
        
        # Verify required fields exist
        assert "total" in data
        assert "by_status" in data
        assert "by_priority" in data
        assert "by_category" in data
        assert "status_labels" in data
        assert "priority_labels" in data
        assert "category_labels" in data
        
    def test_get_stats_total_is_number(self):
        """Total should be a non-negative integer"""
        response = requests.get(f"{BASE_URL}/api/support/stats")
        data = response.json()
        
        assert isinstance(data["total"], int)
        assert data["total"] >= 0
        
    def test_get_stats_by_status_is_dict(self):
        """by_status should be a dictionary"""
        response = requests.get(f"{BASE_URL}/api/support/stats")
        data = response.json()
        
        assert isinstance(data["by_status"], dict)
        
    def test_get_stats_labels_present(self):
        """Status and priority labels should be present"""
        response = requests.get(f"{BASE_URL}/api/support/stats")
        data = response.json()
        
        # Check status labels
        assert "open" in data["status_labels"]
        assert "in_progress" in data["status_labels"]
        assert "resolved" in data["status_labels"]
        assert "closed" in data["status_labels"]
        
        # Check priority labels
        assert "low" in data["priority_labels"]
        assert "medium" in data["priority_labels"]
        assert "high" in data["priority_labels"]
        assert "critical" in data["priority_labels"]


class TestSupportTicketsList:
    """Tests for GET /api/support/tickets endpoint"""
    
    def test_get_tickets_returns_200(self):
        """Tickets list endpoint should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/support/tickets")
        assert response.status_code == 200
        
    def test_get_tickets_structure(self):
        """Response should contain tickets array and total"""
        response = requests.get(f"{BASE_URL}/api/support/tickets")
        data = response.json()
        
        assert "tickets" in data
        assert "total" in data
        assert isinstance(data["tickets"], list)
        assert isinstance(data["total"], int)
        
    def test_get_tickets_with_limit(self):
        """Should respect limit parameter"""
        response = requests.get(f"{BASE_URL}/api/support/tickets?limit=2")
        data = response.json()
        
        assert len(data["tickets"]) <= 2
        
    def test_get_tickets_filter_by_status(self):
        """Should filter by status"""
        response = requests.get(f"{BASE_URL}/api/support/tickets?status=open")
        data = response.json()
        
        # All returned tickets should have status=open
        for ticket in data["tickets"]:
            assert ticket["status"] == "open"
            
    def test_get_tickets_filter_by_priority(self):
        """Should filter by priority"""
        response = requests.get(f"{BASE_URL}/api/support/tickets?priority=high")
        data = response.json()
        
        # All returned tickets should have priority=high
        for ticket in data["tickets"]:
            assert ticket["priority"] == "high"
            
    def test_ticket_has_required_fields(self):
        """Each ticket should have required fields"""
        response = requests.get(f"{BASE_URL}/api/support/tickets?limit=1")
        data = response.json()
        
        if len(data["tickets"]) > 0:
            ticket = data["tickets"][0]
            required_fields = ["ticket_id", "name", "email", "category", "priority", "subject", "message", "status", "created_at"]
            for field in required_fields:
                assert field in ticket, f"Missing field: {field}"


class TestSupportTicketDetail:
    """Tests for GET /api/support/tickets/{ticket_id} endpoint"""
    
    @pytest.fixture
    def existing_ticket_id(self):
        """Get an existing ticket ID for testing"""
        response = requests.get(f"{BASE_URL}/api/support/tickets?limit=1")
        data = response.json()
        if len(data["tickets"]) > 0:
            return data["tickets"][0]["ticket_id"]
        pytest.skip("No tickets available for testing")
        
    def test_get_ticket_detail_returns_200(self, existing_ticket_id):
        """Ticket detail endpoint should return 200 OK for existing ticket"""
        response = requests.get(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}")
        assert response.status_code == 200
        
    def test_get_ticket_detail_structure(self, existing_ticket_id):
        """Ticket detail should contain all required fields"""
        response = requests.get(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}")
        data = response.json()
        
        required_fields = ["ticket_id", "name", "email", "category", "priority", "subject", "message", "status", "created_at", "responses"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            
    def test_get_ticket_detail_responses_is_list(self, existing_ticket_id):
        """Responses field should be a list"""
        response = requests.get(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}")
        data = response.json()
        
        assert isinstance(data["responses"], list)
        
    def test_get_nonexistent_ticket_returns_404(self):
        """Should return 404 for non-existent ticket"""
        response = requests.get(f"{BASE_URL}/api/support/tickets/TKT-NONEXISTENT")
        assert response.status_code == 404


class TestSupportTicketStatusUpdate:
    """Tests for PATCH /api/support/tickets/{ticket_id}/status endpoint"""
    
    @pytest.fixture
    def existing_ticket_id(self):
        """Get an existing ticket ID for testing"""
        response = requests.get(f"{BASE_URL}/api/support/tickets?limit=1")
        data = response.json()
        if len(data["tickets"]) > 0:
            return data["tickets"][0]["ticket_id"]
        pytest.skip("No tickets available for testing")
        
    def test_update_status_to_in_progress(self, existing_ticket_id):
        """Should update ticket status to in_progress"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/status?status=in_progress")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "ticket_id" in data
        
    def test_update_status_to_resolved(self, existing_ticket_id):
        """Should update ticket status to resolved"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/status?status=resolved")
        assert response.status_code == 200
        
    def test_update_status_to_closed(self, existing_ticket_id):
        """Should update ticket status to closed"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/status?status=closed")
        assert response.status_code == 200
        
    def test_update_status_to_open(self, existing_ticket_id):
        """Should update ticket status back to open"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/status?status=open")
        assert response.status_code == 200
        
    def test_update_status_invalid_returns_400(self, existing_ticket_id):
        """Should return 400 for invalid status"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/status?status=invalid_status")
        assert response.status_code == 400
        
    def test_update_status_nonexistent_ticket_returns_404(self):
        """Should return 404 for non-existent ticket"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/TKT-NONEXISTENT/status?status=open")
        assert response.status_code == 404


class TestSupportTicketPriorityUpdate:
    """Tests for PATCH /api/support/tickets/{ticket_id}/priority endpoint"""
    
    @pytest.fixture
    def existing_ticket_id(self):
        """Get an existing ticket ID for testing"""
        response = requests.get(f"{BASE_URL}/api/support/tickets?limit=1")
        data = response.json()
        if len(data["tickets"]) > 0:
            return data["tickets"][0]["ticket_id"]
        pytest.skip("No tickets available for testing")
        
    def test_update_priority_to_high(self, existing_ticket_id):
        """Should update ticket priority to high"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/priority?priority=high")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "ticket_id" in data
        
    def test_update_priority_to_critical(self, existing_ticket_id):
        """Should update ticket priority to critical"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/priority?priority=critical")
        assert response.status_code == 200
        
    def test_update_priority_to_medium(self, existing_ticket_id):
        """Should update ticket priority to medium"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/priority?priority=medium")
        assert response.status_code == 200
        
    def test_update_priority_to_low(self, existing_ticket_id):
        """Should update ticket priority to low"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/priority?priority=low")
        assert response.status_code == 200
        
    def test_update_priority_invalid_returns_400(self, existing_ticket_id):
        """Should return 400 for invalid priority"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/priority?priority=invalid_priority")
        assert response.status_code == 400
        
    def test_update_priority_nonexistent_ticket_returns_404(self):
        """Should return 404 for non-existent ticket"""
        response = requests.patch(f"{BASE_URL}/api/support/tickets/TKT-NONEXISTENT/priority?priority=high")
        assert response.status_code == 404


class TestSupportTicketRespond:
    """Tests for POST /api/support/tickets/{ticket_id}/respond endpoint"""
    
    @pytest.fixture
    def existing_ticket_id(self):
        """Get an existing ticket ID for testing"""
        response = requests.get(f"{BASE_URL}/api/support/tickets?limit=1")
        data = response.json()
        if len(data["tickets"]) > 0:
            return data["tickets"][0]["ticket_id"]
        pytest.skip("No tickets available for testing")
        
    def test_add_response_returns_200(self, existing_ticket_id):
        """Should add response to ticket"""
        payload = {
            "message": f"TEST_Response added at {datetime.now().isoformat()}",
            "internal_note": False
        }
        response = requests.post(
            f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/respond",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "ticket_id" in data
        assert "response_id" in data
        
    def test_add_internal_note_returns_200(self, existing_ticket_id):
        """Should add internal note to ticket"""
        payload = {
            "message": f"TEST_Internal note added at {datetime.now().isoformat()}",
            "internal_note": True
        }
        response = requests.post(
            f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/respond",
            json=payload
        )
        assert response.status_code == 200
        
    def test_response_appears_in_ticket_detail(self, existing_ticket_id):
        """Response should appear in ticket detail"""
        # Add a response
        test_message = f"TEST_Verification response {datetime.now().isoformat()}"
        payload = {
            "message": test_message,
            "internal_note": False
        }
        requests.post(
            f"{BASE_URL}/api/support/tickets/{existing_ticket_id}/respond",
            json=payload
        )
        
        # Get ticket detail and verify response is there
        response = requests.get(f"{BASE_URL}/api/support/tickets/{existing_ticket_id}")
        data = response.json()
        
        assert len(data["responses"]) > 0
        # Check if our test message is in the responses
        messages = [r["message"] for r in data["responses"]]
        assert any(test_message in msg for msg in messages)
        
    def test_respond_nonexistent_ticket_returns_404(self):
        """Should return 404 for non-existent ticket"""
        payload = {
            "message": "Test response",
            "internal_note": False
        }
        response = requests.post(
            f"{BASE_URL}/api/support/tickets/TKT-NONEXISTENT/respond",
            json=payload
        )
        assert response.status_code == 404


class TestSupportTicketCreate:
    """Tests for POST /api/support/ticket endpoint (create new ticket)"""
    
    def test_create_ticket_returns_200(self):
        """Should create a new support ticket"""
        payload = {
            "name": "TEST_User",
            "email": "test_support@example.com",
            "company": "Test Company",
            "phone": "+1809555999",
            "category": "general",
            "priority": "medium",
            "subject": "TEST_Support Ticket Creation",
            "message": "This is a test ticket created by automated tests."
        }
        response = requests.post(f"{BASE_URL}/api/support/ticket", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "ticket_id" in data
        assert "message" in data
        assert "status" in data
        assert data["status"] == "open"
        
    def test_create_ticket_with_minimal_fields(self):
        """Should create ticket with only required fields"""
        payload = {
            "name": "TEST_Minimal User",
            "email": "minimal@example.com",
            "category": "technical",
            "subject": "TEST_Minimal Ticket",
            "message": "Minimal test message"
        }
        response = requests.post(f"{BASE_URL}/api/support/ticket", json=payload)
        assert response.status_code == 200
        
    def test_create_ticket_invalid_email_returns_422(self):
        """Should return 422 for invalid email"""
        payload = {
            "name": "Test User",
            "email": "invalid-email",
            "category": "general",
            "subject": "Test",
            "message": "Test message"
        }
        response = requests.post(f"{BASE_URL}/api/support/ticket", json=payload)
        assert response.status_code == 422


class TestSupportIntegration:
    """Integration tests for support ticket workflow"""
    
    def test_full_ticket_workflow(self):
        """Test complete ticket lifecycle: create -> respond -> update status -> close"""
        # 1. Create ticket
        create_payload = {
            "name": "TEST_Integration User",
            "email": "integration@example.com",
            "category": "technical",
            "priority": "high",
            "subject": "TEST_Integration Test Ticket",
            "message": "This ticket tests the full workflow."
        }
        create_response = requests.post(f"{BASE_URL}/api/support/ticket", json=create_payload)
        assert create_response.status_code == 200
        ticket_id = create_response.json()["ticket_id"]
        
        # 2. Verify ticket appears in list
        list_response = requests.get(f"{BASE_URL}/api/support/tickets")
        tickets = list_response.json()["tickets"]
        ticket_ids = [t["ticket_id"] for t in tickets]
        assert ticket_id in ticket_ids
        
        # 3. Get ticket detail
        detail_response = requests.get(f"{BASE_URL}/api/support/tickets/{ticket_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["status"] == "open"
        assert detail["priority"] == "high"
        
        # 4. Add response (should change status to in_progress)
        respond_payload = {
            "message": "TEST_We are looking into this issue.",
            "internal_note": False
        }
        respond_response = requests.post(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/respond",
            json=respond_payload
        )
        assert respond_response.status_code == 200
        
        # 5. Verify status changed to in_progress
        detail_response = requests.get(f"{BASE_URL}/api/support/tickets/{ticket_id}")
        detail = detail_response.json()
        assert detail["status"] == "in_progress"
        
        # 6. Add internal note
        internal_payload = {
            "message": "TEST_Internal: Customer has been contacted.",
            "internal_note": True
        }
        requests.post(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/respond",
            json=internal_payload
        )
        
        # 7. Update priority to critical
        priority_response = requests.patch(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/priority?priority=critical"
        )
        assert priority_response.status_code == 200
        
        # 8. Resolve ticket
        status_response = requests.patch(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/status?status=resolved"
        )
        assert status_response.status_code == 200
        
        # 9. Verify final state
        final_response = requests.get(f"{BASE_URL}/api/support/tickets/{ticket_id}")
        final = final_response.json()
        assert final["status"] == "resolved"
        assert final["priority"] == "critical"
        assert len(final["responses"]) >= 2  # At least 2 responses added
        
        # 10. Close ticket
        close_response = requests.patch(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/status?status=closed"
        )
        assert close_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
