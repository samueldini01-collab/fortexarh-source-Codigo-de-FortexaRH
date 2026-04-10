"""
Test Payroll Entry Override Features: SFS, AFP, Overtime
Tests:
1. PUT /api/payroll/entries/{entry_id} with sfs_override should update SFS to custom value
2. PUT /api/payroll/entries/{entry_id} with afp_override should update AFP to custom value
3. PUT /api/payroll/entries/{entry_id} with overtime_override should update overtime amounts and recalculate gross/net
4. Entries should store override flags (sfs_manual_override_entry, afp_manual_override_entry, overtime_manual_override_entry)
5. Without overrides, SFS should calculate at 3.04% rate (not 3.07%)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"

# Test data from review request
TEST_PERIOD_ID = "period_0c7fdc679329"
TEST_ENTRY_ID = "pe_239e2bfd8c9e"  # María García with base_salary 32500


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestSFSOverride:
    """Test SFS override functionality"""
    
    def test_sfs_override_updates_entry(self, api_client):
        """PUT /api/payroll/entries/{entry_id} with sfs_override should update SFS to custom value"""
        # First get the entry to get current values
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Test entry {TEST_ENTRY_ID} not found")
        
        assert response.status_code == 200, f"Failed to get entry: {response.text}"
        entry = response.json()
        
        # Store original values for comparison
        original_sfs = entry.get("sfs_employee", 0)
        base_salary = entry.get("base_salary", 32500)
        
        # Calculate expected auto SFS at 3.04%
        expected_auto_sfs = round(base_salary * 0.0304, 2)
        
        # Custom SFS override value
        custom_sfs = 500.00
        
        # Update with SFS override
        update_payload = {
            "period_id": entry.get("period_id", TEST_PERIOD_ID),
            "employee_id": entry.get("employee_id"),
            "base_salary": base_salary,
            "overtime_day_hours": entry.get("overtime_day_hours", 0),
            "overtime_night_hours": entry.get("overtime_night_hours", 0),
            "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
            "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
            "bonuses": entry.get("bonuses", 0),
            "commissions": entry.get("commissions", 0),
            "additional_deductions": entry.get("additional_deductions", []),
            "sfs_override": custom_sfs
        }
        
        response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
        assert response.status_code == 200, f"Failed to update entry with SFS override: {response.text}"
        
        # Verify the update
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        assert response.status_code == 200
        
        updated_entry = response.json()
        assert updated_entry.get("sfs_employee") == custom_sfs, f"SFS should be {custom_sfs}, got {updated_entry.get('sfs_employee')}"
        assert updated_entry.get("sfs_manual_override_entry") == True, "sfs_manual_override_entry flag should be True"
        
        print(f"PASSED: SFS override works - set to {custom_sfs}")
        print(f"  - Original SFS: {original_sfs}")
        print(f"  - Expected auto SFS (3.04%): {expected_auto_sfs}")
        print(f"  - Custom SFS override: {custom_sfs}")
        print(f"  - sfs_manual_override_entry: {updated_entry.get('sfs_manual_override_entry')}")
        
        # Reset to auto-calc (no override)
        update_payload["sfs_override"] = None
        del update_payload["sfs_override"]
        response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
        assert response.status_code == 200, "Failed to reset SFS override"
        
        # Verify reset
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        reset_entry = response.json()
        assert reset_entry.get("sfs_manual_override_entry") == False, "sfs_manual_override_entry should be False after reset"
        
        print(f"PASSED: SFS reset to auto-calc - now {reset_entry.get('sfs_employee')}")


class TestAFPOverride:
    """Test AFP override functionality"""
    
    def test_afp_override_updates_entry(self, api_client):
        """PUT /api/payroll/entries/{entry_id} with afp_override should update AFP to custom value"""
        # First get the entry
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Test entry {TEST_ENTRY_ID} not found")
        
        assert response.status_code == 200
        entry = response.json()
        
        original_afp = entry.get("afp_employee", 0)
        base_salary = entry.get("base_salary", 32500)
        
        # Calculate expected auto AFP at 2.87%
        expected_auto_afp = round(base_salary * 0.0287, 2)
        
        # Custom AFP override value
        custom_afp = 750.00
        
        # Update with AFP override
        update_payload = {
            "period_id": entry.get("period_id", TEST_PERIOD_ID),
            "employee_id": entry.get("employee_id"),
            "base_salary": base_salary,
            "overtime_day_hours": entry.get("overtime_day_hours", 0),
            "overtime_night_hours": entry.get("overtime_night_hours", 0),
            "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
            "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
            "bonuses": entry.get("bonuses", 0),
            "commissions": entry.get("commissions", 0),
            "additional_deductions": entry.get("additional_deductions", []),
            "afp_override": custom_afp
        }
        
        response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
        assert response.status_code == 200, f"Failed to update entry with AFP override: {response.text}"
        
        # Verify the update
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        assert response.status_code == 200
        
        updated_entry = response.json()
        assert updated_entry.get("afp_employee") == custom_afp, f"AFP should be {custom_afp}, got {updated_entry.get('afp_employee')}"
        assert updated_entry.get("afp_manual_override_entry") == True, "afp_manual_override_entry flag should be True"
        
        print(f"PASSED: AFP override works - set to {custom_afp}")
        print(f"  - Original AFP: {original_afp}")
        print(f"  - Expected auto AFP (2.87%): {expected_auto_afp}")
        print(f"  - Custom AFP override: {custom_afp}")
        print(f"  - afp_manual_override_entry: {updated_entry.get('afp_manual_override_entry')}")
        
        # Reset to auto-calc
        del update_payload["afp_override"]
        response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
        assert response.status_code == 200
        
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        reset_entry = response.json()
        assert reset_entry.get("afp_manual_override_entry") == False, "afp_manual_override_entry should be False after reset"
        
        print(f"PASSED: AFP reset to auto-calc - now {reset_entry.get('afp_employee')}")


class TestOvertimeOverride:
    """Test Overtime override functionality"""
    
    def test_overtime_override_updates_entry(self, api_client):
        """PUT /api/payroll/entries/{entry_id} with overtime_override should update overtime amounts and recalculate gross/net"""
        # First get the entry
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Test entry {TEST_ENTRY_ID} not found")
        
        assert response.status_code == 200
        entry = response.json()
        
        original_overtime_day = entry.get("overtime_day_amount", 0)
        original_gross = entry.get("gross_salary", 0)
        base_salary = entry.get("base_salary", 32500)
        
        # Custom overtime override value
        custom_overtime = 2500.00
        
        # Update with overtime override
        update_payload = {
            "period_id": entry.get("period_id", TEST_PERIOD_ID),
            "employee_id": entry.get("employee_id"),
            "base_salary": base_salary,
            "overtime_day_hours": entry.get("overtime_day_hours", 0),
            "overtime_night_hours": entry.get("overtime_night_hours", 0),
            "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
            "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
            "bonuses": entry.get("bonuses", 0),
            "commissions": entry.get("commissions", 0),
            "additional_deductions": entry.get("additional_deductions", []),
            "overtime_override": custom_overtime
        }
        
        response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
        assert response.status_code == 200, f"Failed to update entry with overtime override: {response.text}"
        
        # Verify the update
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        assert response.status_code == 200
        
        updated_entry = response.json()
        
        # When overtime_override is set, it goes to overtime_day_amount and others are zeroed
        assert updated_entry.get("overtime_day_amount") == custom_overtime, f"overtime_day_amount should be {custom_overtime}, got {updated_entry.get('overtime_day_amount')}"
        assert updated_entry.get("overtime_night_amount") == 0, "overtime_night_amount should be 0 when override is used"
        assert updated_entry.get("overtime_weekend_amount") == 0, "overtime_weekend_amount should be 0 when override is used"
        assert updated_entry.get("overtime_holiday_amount") == 0, "overtime_holiday_amount should be 0 when override is used"
        assert updated_entry.get("overtime_manual_override_entry") == True, "overtime_manual_override_entry flag should be True"
        
        # Verify gross salary includes the overtime
        expected_gross = base_salary + custom_overtime + entry.get("bonuses", 0) + entry.get("commissions", 0) + entry.get("other_income", 0)
        assert updated_entry.get("gross_salary") == round(expected_gross, 2), f"Gross salary should be {expected_gross}, got {updated_entry.get('gross_salary')}"
        
        print(f"PASSED: Overtime override works - set to {custom_overtime}")
        print(f"  - Original overtime_day_amount: {original_overtime_day}")
        print(f"  - Original gross: {original_gross}")
        print(f"  - Custom overtime override: {custom_overtime}")
        print(f"  - New gross: {updated_entry.get('gross_salary')}")
        print(f"  - overtime_manual_override_entry: {updated_entry.get('overtime_manual_override_entry')}")
        
        # Reset to auto-calc
        del update_payload["overtime_override"]
        response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
        assert response.status_code == 200
        
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        reset_entry = response.json()
        assert reset_entry.get("overtime_manual_override_entry") == False, "overtime_manual_override_entry should be False after reset"
        
        print(f"PASSED: Overtime reset to auto-calc")


class TestSFSRateCalculation:
    """Test that SFS calculates at 3.04% rate (not 3.07%)"""
    
    def test_sfs_rate_is_304_percent(self, api_client):
        """Without overrides, SFS should calculate at 3.04% rate"""
        # Get the entry
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Test entry {TEST_ENTRY_ID} not found")
        
        assert response.status_code == 200
        entry = response.json()
        
        # Skip if there's a manual override
        if entry.get("sfs_manual_override_entry"):
            # Reset the override first
            update_payload = {
                "period_id": entry.get("period_id", TEST_PERIOD_ID),
                "employee_id": entry.get("employee_id"),
                "base_salary": entry.get("base_salary"),
                "overtime_day_hours": entry.get("overtime_day_hours", 0),
                "overtime_night_hours": entry.get("overtime_night_hours", 0),
                "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
                "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
                "bonuses": entry.get("bonuses", 0),
                "commissions": entry.get("commissions", 0),
                "additional_deductions": entry.get("additional_deductions", [])
            }
            response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
            assert response.status_code == 200
            
            response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
            entry = response.json()
        
        gross_salary = entry.get("gross_salary", 0)
        sfs_employee = entry.get("sfs_employee", 0)
        
        # Calculate expected SFS at 3.04%
        expected_sfs_304 = round(gross_salary * 0.0304, 2)
        # Calculate what it would be at 3.07% (old rate)
        expected_sfs_307 = round(gross_salary * 0.0307, 2)
        
        # SFS should match 3.04% rate, not 3.07%
        assert sfs_employee == expected_sfs_304, f"SFS should be {expected_sfs_304} (3.04%), got {sfs_employee}"
        assert sfs_employee != expected_sfs_307, f"SFS should NOT be {expected_sfs_307} (3.07%)"
        
        print(f"PASSED: SFS rate is 3.04%")
        print(f"  - Gross salary: {gross_salary}")
        print(f"  - SFS employee: {sfs_employee}")
        print(f"  - Expected at 3.04%: {expected_sfs_304}")
        print(f"  - Would be at 3.07%: {expected_sfs_307}")


class TestCombinedOverrides:
    """Test multiple overrides at once"""
    
    def test_all_overrides_together(self, api_client):
        """Test SFS, AFP, and overtime overrides all at once"""
        # Get the entry
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Test entry {TEST_ENTRY_ID} not found")
        
        assert response.status_code == 200
        entry = response.json()
        
        base_salary = entry.get("base_salary", 32500)
        
        # Custom override values
        custom_sfs = 400.00
        custom_afp = 600.00
        custom_overtime = 1500.00
        
        # Update with all overrides
        update_payload = {
            "period_id": entry.get("period_id", TEST_PERIOD_ID),
            "employee_id": entry.get("employee_id"),
            "base_salary": base_salary,
            "overtime_day_hours": entry.get("overtime_day_hours", 0),
            "overtime_night_hours": entry.get("overtime_night_hours", 0),
            "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
            "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
            "bonuses": entry.get("bonuses", 0),
            "commissions": entry.get("commissions", 0),
            "additional_deductions": entry.get("additional_deductions", []),
            "sfs_override": custom_sfs,
            "afp_override": custom_afp,
            "overtime_override": custom_overtime
        }
        
        response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
        assert response.status_code == 200, f"Failed to update entry with all overrides: {response.text}"
        
        # Verify the update
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        assert response.status_code == 200
        
        updated_entry = response.json()
        
        assert updated_entry.get("sfs_employee") == custom_sfs, f"SFS should be {custom_sfs}"
        assert updated_entry.get("afp_employee") == custom_afp, f"AFP should be {custom_afp}"
        assert updated_entry.get("overtime_day_amount") == custom_overtime, f"Overtime should be {custom_overtime}"
        assert updated_entry.get("sfs_manual_override_entry") == True
        assert updated_entry.get("afp_manual_override_entry") == True
        assert updated_entry.get("overtime_manual_override_entry") == True
        
        print(f"PASSED: All overrides work together")
        print(f"  - SFS: {updated_entry.get('sfs_employee')}")
        print(f"  - AFP: {updated_entry.get('afp_employee')}")
        print(f"  - Overtime: {updated_entry.get('overtime_day_amount')}")
        
        # Reset all overrides
        del update_payload["sfs_override"]
        del update_payload["afp_override"]
        del update_payload["overtime_override"]
        response = api_client.put(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}", json=update_payload)
        assert response.status_code == 200
        
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        reset_entry = response.json()
        assert reset_entry.get("sfs_manual_override_entry") == False
        assert reset_entry.get("afp_manual_override_entry") == False
        assert reset_entry.get("overtime_manual_override_entry") == False
        
        print(f"PASSED: All overrides reset successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
