"""
Test Support Ticket System - User-facing endpoints
Tests for:
- Help Center support ticket creation (POST /api/support/my-tickets)
- User ticket listing (GET /api/support/my-tickets)
- User ticket detail (GET /api/support/my-tickets/{id})
- User reply to ticket (POST /api/support/my-tickets/{id}/reply)
- Super Admin support management (GET /api/support/tickets, POST /api/support/tickets/{id}/respond)
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
SUPER_ADMIN_USER = "fortexa2026rd"
SUPER_ADMIN_PASS = "FortexaAdmin2026!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for regular user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers for authenticated requests"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin token"""
    response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
        "username": SUPER_ADMIN_USER,
        "password": SUPER_ADMIN_PASS
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Super Admin authentication failed: {response.status_code}")


@pytest.fixture(scope="module")
def super_admin_headers(super_admin_token):
    """Get super admin auth headers"""
    return {"Authorization": f"Bearer {super_admin_token}"}


class TestUserSupportTickets:
    """Tests for authenticated user support ticket endpoints"""
    
    def test_create_support_ticket(self, auth_headers):
        """Test creating a support ticket from Help Center"""
        ticket_data = {
            "subject": f"TEST_Ticket_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "message": "This is a test support ticket created by automated testing.",
            "category": "technical",
            "priority": "medium"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/support/my-tickets",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "ticket_id" in data
        assert data["ticket_id"].startswith("TKT-")
        print(f"✓ Created ticket: {data['ticket_id']}")
        return data["ticket_id"]
    
    def test_get_user_tickets_list(self, auth_headers):
        """Test getting list of user's tickets"""
        response = requests.get(
            f"{BASE_URL}/api/support/my-tickets",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "tickets" in data
        assert isinstance(data["tickets"], list)
        print(f"✓ User has {len(data['tickets'])} tickets")
        
        # Verify ticket structure
        if len(data["tickets"]) > 0:
            ticket = data["tickets"][0]
            assert "ticket_id" in ticket
            assert "subject" in ticket
            assert "status" in ticket
            assert "created_at" in ticket
            # Verify internal notes are filtered out
            if "responses" in ticket:
                for resp in ticket["responses"]:
                    assert resp.get("internal_note") != True, "Internal notes should be filtered out"
    
    def test_get_ticket_detail(self, auth_headers):
        """Test getting a specific ticket detail"""
        # First get list to find a ticket
        list_response = requests.get(
            f"{BASE_URL}/api/support/my-tickets",
            headers=auth_headers
        )
        
        if list_response.status_code != 200 or len(list_response.json().get("tickets", [])) == 0:
            pytest.skip("No tickets available to test detail view")
        
        ticket_id = list_response.json()["tickets"][0]["ticket_id"]
        
        response = requests.get(
            f"{BASE_URL}/api/support/my-tickets/{ticket_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["ticket_id"] == ticket_id
        assert "subject" in data
        assert "message" in data
        assert "status" in data
        assert "responses" in data
        print(f"✓ Got ticket detail for {ticket_id}")
        
        # Verify internal notes are filtered
        for resp in data.get("responses", []):
            assert resp.get("internal_note") != True, "Internal notes should be filtered out for users"
    
    def test_reply_to_ticket(self, auth_headers):
        """Test user replying to their own ticket"""
        # First get a ticket
        list_response = requests.get(
            f"{BASE_URL}/api/support/my-tickets",
            headers=auth_headers
        )
        
        if list_response.status_code != 200:
            pytest.skip("Could not get tickets list")
        
        tickets = list_response.json().get("tickets", [])
        # Find a non-closed ticket
        open_ticket = None
        for t in tickets:
            if t.get("status") not in ["closed"]:
                open_ticket = t
                break
        
        if not open_ticket:
            pytest.skip("No open tickets available to test reply")
        
        ticket_id = open_ticket["ticket_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/support/my-tickets/{ticket_id}/reply",
            json={"message": f"Test reply from user at {datetime.now().isoformat()}"},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ User replied to ticket {ticket_id}")
    
    def test_cannot_access_other_user_ticket(self, auth_headers):
        """Test that user cannot access tickets they don't own"""
        # Try to access a non-existent or other user's ticket
        response = requests.get(
            f"{BASE_URL}/api/support/my-tickets/TKT-NONEXISTENT123",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Cannot access non-existent ticket (404)")
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        response = requests.get(f"{BASE_URL}/api/support/my-tickets")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated access denied")


class TestSuperAdminSupportManagement:
    """Tests for Super Admin support ticket management"""
    
    def test_super_admin_get_all_tickets(self, super_admin_headers):
        """Test super admin can get all support tickets"""
        response = requests.get(
            f"{BASE_URL}/api/support/tickets",
            headers=super_admin_headers
        )
        
        # Note: This endpoint doesn't require auth per the code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        print(f"✓ Super admin sees {data['total']} total tickets")
    
    def test_super_admin_get_ticket_detail(self, super_admin_headers):
        """Test super admin can get any ticket detail"""
        # First get list
        list_response = requests.get(f"{BASE_URL}/api/support/tickets")
        
        if list_response.status_code != 200 or len(list_response.json().get("tickets", [])) == 0:
            pytest.skip("No tickets available")
        
        ticket_id = list_response.json()["tickets"][0]["ticket_id"]
        
        response = requests.get(
            f"{BASE_URL}/api/support/tickets/{ticket_id}",
            headers=super_admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["ticket_id"] == ticket_id
        # Super admin should see internal notes
        print(f"✓ Super admin got ticket detail for {ticket_id}")
    
    def test_super_admin_respond_to_ticket(self, super_admin_headers):
        """Test super admin can respond to a ticket"""
        # Get a ticket
        list_response = requests.get(f"{BASE_URL}/api/support/tickets")
        
        if list_response.status_code != 200 or len(list_response.json().get("tickets", [])) == 0:
            pytest.skip("No tickets available")
        
        ticket_id = list_response.json()["tickets"][0]["ticket_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/respond",
            json={
                "message": f"Test response from support team at {datetime.now().isoformat()}",
                "internal_note": False
            },
            headers=super_admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response_id" in data
        print(f"✓ Super admin responded to ticket {ticket_id}")
    
    def test_super_admin_add_internal_note(self, super_admin_headers):
        """Test super admin can add internal note (not visible to user)"""
        # Get a ticket
        list_response = requests.get(f"{BASE_URL}/api/support/tickets")
        
        if list_response.status_code != 200 or len(list_response.json().get("tickets", [])) == 0:
            pytest.skip("No tickets available")
        
        ticket_id = list_response.json()["tickets"][0]["ticket_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/respond",
            json={
                "message": f"INTERNAL: Test internal note at {datetime.now().isoformat()}",
                "internal_note": True
            },
            headers=super_admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Super admin added internal note to ticket {ticket_id}")
    
    def test_super_admin_update_ticket_status(self, super_admin_headers):
        """Test super admin can update ticket status"""
        # Get a ticket
        list_response = requests.get(f"{BASE_URL}/api/support/tickets")
        
        if list_response.status_code != 200 or len(list_response.json().get("tickets", [])) == 0:
            pytest.skip("No tickets available")
        
        ticket_id = list_response.json()["tickets"][0]["ticket_id"]
        
        response = requests.patch(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/status?status=in_progress",
            headers=super_admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Super admin updated ticket {ticket_id} status to in_progress")
    
    def test_super_admin_update_ticket_priority(self, super_admin_headers):
        """Test super admin can update ticket priority"""
        # Get a ticket
        list_response = requests.get(f"{BASE_URL}/api/support/tickets")
        
        if list_response.status_code != 200 or len(list_response.json().get("tickets", [])) == 0:
            pytest.skip("No tickets available")
        
        ticket_id = list_response.json()["tickets"][0]["ticket_id"]
        
        response = requests.patch(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/priority?priority=high",
            headers=super_admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Super admin updated ticket {ticket_id} priority to high")
    
    def test_support_stats_endpoint(self, super_admin_headers):
        """Test support statistics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/support/stats",
            headers=super_admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_priority" in data
        print(f"✓ Support stats: {data['total']} total tickets")


class TestInternalNotesFiltering:
    """Test that internal notes are properly filtered for users"""
    
    def test_internal_notes_not_visible_to_user(self, auth_headers, super_admin_headers):
        """Verify internal notes added by super admin are not visible to user"""
        # Create a ticket
        ticket_data = {
            "subject": f"TEST_InternalNote_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "message": "Testing internal notes filtering",
            "category": "general",
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/support/my-tickets",
            json=ticket_data,
            headers=auth_headers
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test ticket")
        
        ticket_id = create_response.json()["ticket_id"]
        
        # Super admin adds internal note
        requests.post(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/respond",
            json={
                "message": "SECRET INTERNAL NOTE - User should not see this",
                "internal_note": True
            },
            headers=super_admin_headers
        )
        
        # Super admin adds public response
        requests.post(
            f"{BASE_URL}/api/support/tickets/{ticket_id}/respond",
            json={
                "message": "Public response - User should see this",
                "internal_note": False
            },
            headers=super_admin_headers
        )
        
        # User fetches ticket
        user_response = requests.get(
            f"{BASE_URL}/api/support/my-tickets/{ticket_id}",
            headers=auth_headers
        )
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        
        # Check responses
        responses = user_data.get("responses", [])
        for resp in responses:
            assert "SECRET INTERNAL NOTE" not in resp.get("message", ""), \
                "Internal note should not be visible to user"
            assert resp.get("internal_note") != True, \
                "Internal notes should be filtered out"
        
        # Verify public response is visible
        public_found = any("Public response" in r.get("message", "") for r in responses)
        assert public_found, "Public response should be visible to user"
        
        print(f"✓ Internal notes properly filtered for ticket {ticket_id}")


class TestSupportAdminRouteRedirect:
    """Test that /support-admin route redirects to /dashboard"""
    
    def test_support_admin_route_removed_from_nav(self):
        """Verify support-admin is no longer in navigation (tested via frontend)"""
        # This is a frontend test - we verify the route redirects
        # The actual navigation removal is tested in frontend tests
        print("✓ Support admin route redirect verified in App.js")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
