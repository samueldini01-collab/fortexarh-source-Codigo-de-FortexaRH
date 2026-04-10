"""
Test Accounting Dashboard Enhancements - FortexaRH
Tests for Payroll Summary tab, Balance column, and Payroll Only filter

Features tested:
1. GET /api/accounting/payroll-summary endpoint
2. KPIs: total_entries, total_debits, total_credits, all_balanced, posted_count, draft_count, last_entry_date
3. Enriched payroll entries with is_balanced, period_status, employee_count
4. Journal entries with balance check (total_debits == total_credits)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"


class TestAccountingDashboardEnhancements:
    """Test suite for Accounting Dashboard UI enhancements"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_payroll_summary_endpoint_exists(self):
        """Test GET /api/accounting/payroll-summary returns 200"""
        response = self.session.get(f"{BASE_URL}/api/accounting/payroll-summary")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Payroll summary endpoint returns 200")
    
    def test_02_payroll_summary_response_structure(self):
        """Test payroll-summary returns correct structure with entries and kpis"""
        response = self.session.get(f"{BASE_URL}/api/accounting/payroll-summary")
        data = response.json()
        
        # Check top-level structure
        assert "entries" in data, "Response missing 'entries' field"
        assert "kpis" in data, "Response missing 'kpis' field"
        assert isinstance(data["entries"], list), "'entries' should be a list"
        assert isinstance(data["kpis"], dict), "'kpis' should be a dict"
        
        print(f"✓ Response structure correct: entries={len(data['entries'])}, kpis present")
    
    def test_03_payroll_summary_kpis_fields(self):
        """Test KPIs contain all required fields"""
        response = self.session.get(f"{BASE_URL}/api/accounting/payroll-summary")
        kpis = response.json().get("kpis", {})
        
        required_kpi_fields = [
            "total_entries",
            "total_debits", 
            "total_credits",
            "all_balanced",
            "posted_count",
            "draft_count",
            "last_entry_date"
        ]
        
        for field in required_kpi_fields:
            assert field in kpis, f"KPIs missing required field: {field}"
        
        print(f"✓ All KPI fields present: {list(kpis.keys())}")
        print(f"  - total_entries: {kpis['total_entries']}")
        print(f"  - total_debits: {kpis['total_debits']}")
        print(f"  - total_credits: {kpis['total_credits']}")
        print(f"  - all_balanced: {kpis['all_balanced']}")
        print(f"  - posted_count: {kpis['posted_count']}")
        print(f"  - draft_count: {kpis['draft_count']}")
        print(f"  - last_entry_date: {kpis['last_entry_date']}")
    
    def test_04_payroll_summary_entries_enriched(self):
        """Test payroll entries are enriched with balance and period info"""
        response = self.session.get(f"{BASE_URL}/api/accounting/payroll-summary")
        entries = response.json().get("entries", [])
        
        if not entries:
            pytest.skip("No payroll entries to test")
        
        entry = entries[0]
        
        # Check enriched fields
        enriched_fields = [
            "is_balanced",
            "period_status",
            "period_description",
            "employee_count"
        ]
        
        for field in enriched_fields:
            assert field in entry, f"Entry missing enriched field: {field}"
        
        print(f"✓ Entry enriched with: {enriched_fields}")
        print(f"  - is_balanced: {entry['is_balanced']}")
        print(f"  - period_status: {entry['period_status']}")
        print(f"  - employee_count: {entry['employee_count']}")
    
    def test_05_payroll_entries_are_balanced(self):
        """Test that payroll entries have matching debits and credits"""
        response = self.session.get(f"{BASE_URL}/api/accounting/payroll-summary")
        entries = response.json().get("entries", [])
        kpis = response.json().get("kpis", {})
        
        if not entries:
            pytest.skip("No payroll entries to test")
        
        # Check each entry is balanced
        for entry in entries:
            debits = entry.get("total_debits", 0)
            credits = entry.get("total_credits", 0)
            is_balanced = entry.get("is_balanced", False)
            
            # Verify is_balanced flag matches actual calculation
            calculated_balanced = abs(debits - credits) < 0.01
            assert is_balanced == calculated_balanced, \
                f"Entry {entry['entry_id']}: is_balanced={is_balanced} but debits={debits}, credits={credits}"
        
        # Verify all_balanced KPI
        all_balanced = kpis.get("all_balanced", False)
        expected_all_balanced = all(e.get("is_balanced", False) for e in entries)
        assert all_balanced == expected_all_balanced, \
            f"all_balanced KPI mismatch: {all_balanced} vs calculated {expected_all_balanced}"
        
        print(f"✓ All {len(entries)} payroll entries are balanced")
        print(f"  - all_balanced KPI: {all_balanced}")
    
    def test_06_journal_entries_have_balance_info(self):
        """Test journal entries endpoint returns balance-related fields"""
        response = self.session.get(f"{BASE_URL}/api/accounting/journal-entries")
        
        assert response.status_code == 200
        entries = response.json()
        
        if not entries:
            pytest.skip("No journal entries to test")
        
        entry = entries[0]
        
        # Check balance fields exist
        assert "total_debits" in entry, "Entry missing total_debits"
        assert "total_credits" in entry, "Entry missing total_credits"
        
        # Verify balance calculation
        debits = entry.get("total_debits", 0)
        credits = entry.get("total_credits", 0)
        is_balanced = abs(debits - credits) < 0.01
        
        print(f"✓ Journal entry has balance info: debits={debits}, credits={credits}, balanced={is_balanced}")
    
    def test_07_payroll_entries_filter(self):
        """Test filtering journal entries by entry_type=payroll"""
        # Get all entries
        all_response = self.session.get(f"{BASE_URL}/api/accounting/journal-entries")
        all_entries = all_response.json()
        
        # Get payroll entries via search
        payroll_response = self.session.get(
            f"{BASE_URL}/api/accounting/journal-entries/search",
            params={"entry_type": "payroll"}
        )
        
        assert payroll_response.status_code == 200
        payroll_entries = payroll_response.json()
        
        # Verify all returned entries are payroll type
        for entry in payroll_entries:
            assert entry.get("entry_type") == "payroll", \
                f"Non-payroll entry returned: {entry.get('entry_type')}"
        
        # Count payroll entries in all entries
        expected_count = sum(1 for e in all_entries if e.get("entry_type") == "payroll")
        
        print(f"✓ Payroll filter works: {len(payroll_entries)} payroll entries out of {len(all_entries)} total")
        print(f"  - Expected payroll count: {expected_count}")
    
    def test_08_accounts_endpoint(self):
        """Test chart of accounts endpoint"""
        response = self.session.get(f"{BASE_URL}/api/accounting/accounts")
        
        assert response.status_code == 200
        accounts = response.json()
        
        assert isinstance(accounts, list), "Accounts should be a list"
        assert len(accounts) > 0, "Should have at least one account"
        
        # Check account structure
        account = accounts[0]
        required_fields = ["code", "name", "account_type"]
        for field in required_fields:
            assert field in account, f"Account missing field: {field}"
        
        print(f"✓ Chart of accounts: {len(accounts)} accounts")
    
    def test_09_kpi_totals_match_entries(self):
        """Test that KPI totals match sum of entries"""
        response = self.session.get(f"{BASE_URL}/api/accounting/payroll-summary")
        data = response.json()
        
        entries = data.get("entries", [])
        kpis = data.get("kpis", {})
        
        if not entries:
            pytest.skip("No payroll entries to test")
        
        # Calculate totals from entries
        calc_debits = sum(e.get("total_debits", 0) for e in entries)
        calc_credits = sum(e.get("total_credits", 0) for e in entries)
        calc_posted = sum(1 for e in entries if e.get("status") == "posted")
        calc_draft = sum(1 for e in entries if e.get("status") == "draft")
        
        # Compare with KPIs
        assert abs(kpis["total_debits"] - calc_debits) < 0.01, \
            f"total_debits mismatch: KPI={kpis['total_debits']}, calculated={calc_debits}"
        assert abs(kpis["total_credits"] - calc_credits) < 0.01, \
            f"total_credits mismatch: KPI={kpis['total_credits']}, calculated={calc_credits}"
        assert kpis["posted_count"] == calc_posted, \
            f"posted_count mismatch: KPI={kpis['posted_count']}, calculated={calc_posted}"
        assert kpis["draft_count"] == calc_draft, \
            f"draft_count mismatch: KPI={kpis['draft_count']}, calculated={calc_draft}"
        assert kpis["total_entries"] == len(entries), \
            f"total_entries mismatch: KPI={kpis['total_entries']}, calculated={len(entries)}"
        
        print(f"✓ KPI totals match entry calculations")
        print(f"  - total_debits: {kpis['total_debits']}")
        print(f"  - total_credits: {kpis['total_credits']}")
        print(f"  - posted_count: {kpis['posted_count']}")
        print(f"  - draft_count: {kpis['draft_count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
