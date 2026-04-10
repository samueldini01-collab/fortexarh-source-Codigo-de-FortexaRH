"""
Test ISR Override Feature for Payroll Entries
Tests the new feature: Make ISR column editable in the payroll sheet (Hoja de Nómina)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"

# Test data from the review request
DRAFT_PERIOD_ID = "period_0c7fdc679329"
TEST_ENTRY_ID = "pe_321564c774ef"  # TEST_Loan Employee - already has ISR override
MARIA_ENTRY_ID = "pe_239e2bfd8c9e"  # María García Pérez - no override


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture
def api_client(auth_token):
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestISROverrideBackend:
    """Test ISR override functionality in PUT /api/payroll/entries/{entry_id}"""
    
    def test_get_entry_with_existing_override(self, api_client):
        """Test that entry with existing ISR override shows the flag"""
        response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        assert response.status_code == 200, f"Failed to get entry: {response.text}"
        
        data = response.json()
        assert "isr" in data, "ISR field missing from response"
        assert data.get("isr_manual_override_entry") == True, "Expected isr_manual_override_entry to be True"
        print(f"Entry {TEST_ENTRY_ID} has ISR: {data['isr']} with override flag: {data.get('isr_manual_override_entry')}")
    
    def test_update_entry_with_isr_override(self, api_client):
        """Test PUT with isr_override field updates ISR to specified value"""
        # First get the current entry data
        get_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}")
        assert get_response.status_code == 200
        entry = get_response.json()
        
        # Set a custom ISR override value
        new_isr_value = 500.0
        
        update_data = {
            "period_id": entry["period_id"],
            "employee_id": entry["employee_id"],
            "base_salary": entry["base_salary"],
            "overtime_day_hours": entry.get("overtime_day_hours", 0),
            "overtime_night_hours": entry.get("overtime_night_hours", 0),
            "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
            "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
            "bonuses": entry.get("bonuses", 0),
            "commissions": entry.get("commissions", 0),
            "additional_deductions": entry.get("additional_deductions", []),
            "isr_override": new_isr_value  # The new ISR override field
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}",
            json=update_data
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        # Verify the update
        verify_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}")
        assert verify_response.status_code == 200
        updated_entry = verify_response.json()
        
        # Assert ISR was updated to the override value
        assert updated_entry["isr"] == new_isr_value, f"Expected ISR {new_isr_value}, got {updated_entry['isr']}"
        
        # Assert the override flag is set
        assert updated_entry.get("isr_manual_override_entry") == True, "isr_manual_override_entry should be True"
        
        # Verify net salary = gross - total_deductions (basic sanity check)
        gross = updated_entry.get("gross_salary", 0)
        total_ded = updated_entry.get("total_deductions", 0)
        net = updated_entry.get("net_salary", 0)
        
        # Net should equal gross minus deductions
        assert abs(net - (gross - total_ded)) < 0.01, \
            f"Net salary calculation incorrect: {net} != {gross} - {total_ded}"
        
        # Verify ISR is part of total_deductions
        sfs = updated_entry.get("sfs_employee", 0)
        afp = updated_entry.get("afp_employee", 0)
        isr = updated_entry.get("isr", 0)
        additional = updated_entry.get("total_additional_deductions", 0)
        loan = updated_entry.get("loan_deduction", 0)
        
        expected_deductions = sfs + afp + isr + additional + loan
        assert abs(total_ded - expected_deductions) < 0.01, \
            f"Total deductions incorrect: {total_ded} != {expected_deductions}"
        
        print(f"ISR Override Test PASSED:")
        print(f"  ISR set to: {updated_entry['isr']}")
        print(f"  Net salary: {updated_entry['net_salary']}")
        print(f"  Override flag: {updated_entry.get('isr_manual_override_entry')}")
    
    def test_update_entry_without_isr_override_calculates_normally(self, api_client):
        """Test PUT without isr_override should calculate ISR normally from employee settings"""
        # Get entry data
        get_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}")
        assert get_response.status_code == 200
        entry = get_response.json()
        
        # Update without isr_override - should recalculate ISR
        update_data = {
            "period_id": entry["period_id"],
            "employee_id": entry["employee_id"],
            "base_salary": entry["base_salary"],
            "overtime_day_hours": entry.get("overtime_day_hours", 0),
            "overtime_night_hours": entry.get("overtime_night_hours", 0),
            "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
            "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
            "bonuses": entry.get("bonuses", 0),
            "commissions": entry.get("commissions", 0),
            "additional_deductions": entry.get("additional_deductions", [])
            # Note: NO isr_override field
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}",
            json=update_data
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        # Verify the update
        verify_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}")
        assert verify_response.status_code == 200
        updated_entry = verify_response.json()
        
        # Assert the override flag is False (since we didn't send isr_override)
        assert updated_entry.get("isr_manual_override_entry") == False, \
            "isr_manual_override_entry should be False when no override sent"
        
        print(f"Normal ISR Calculation Test PASSED:")
        print(f"  ISR: {updated_entry['isr']} (calculated)")
        print(f"  Override flag: {updated_entry.get('isr_manual_override_entry')}")
    
    def test_isr_override_with_zero_value(self, api_client):
        """Test that ISR can be overridden to 0"""
        get_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}")
        assert get_response.status_code == 200
        entry = get_response.json()
        
        update_data = {
            "period_id": entry["period_id"],
            "employee_id": entry["employee_id"],
            "base_salary": entry["base_salary"],
            "overtime_day_hours": entry.get("overtime_day_hours", 0),
            "overtime_night_hours": entry.get("overtime_night_hours", 0),
            "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
            "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
            "bonuses": entry.get("bonuses", 0),
            "commissions": entry.get("commissions", 0),
            "additional_deductions": entry.get("additional_deductions", []),
            "isr_override": 0.0  # Override to zero
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}",
            json=update_data
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        verify_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}")
        updated_entry = verify_response.json()
        
        assert updated_entry["isr"] == 0.0, f"Expected ISR 0.0, got {updated_entry['isr']}"
        assert updated_entry.get("isr_manual_override_entry") == True, "Override flag should be True even for 0"
        
        print(f"Zero ISR Override Test PASSED: ISR = {updated_entry['isr']}")
    
    def test_restore_original_isr_value(self, api_client):
        """Cleanup: Restore María's entry to calculated ISR (no override)"""
        get_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}")
        assert get_response.status_code == 200
        entry = get_response.json()
        
        # Update without isr_override to restore calculated value
        update_data = {
            "period_id": entry["period_id"],
            "employee_id": entry["employee_id"],
            "base_salary": entry["base_salary"],
            "overtime_day_hours": entry.get("overtime_day_hours", 0),
            "overtime_night_hours": entry.get("overtime_night_hours", 0),
            "overtime_weekend_hours": entry.get("overtime_weekend_hours", 0),
            "overtime_holiday_hours": entry.get("overtime_holiday_hours", 0),
            "bonuses": entry.get("bonuses", 0),
            "commissions": entry.get("commissions", 0),
            "additional_deductions": entry.get("additional_deductions", [])
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}",
            json=update_data
        )
        assert response.status_code == 200
        
        verify_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{MARIA_ENTRY_ID}")
        updated_entry = verify_response.json()
        
        print(f"Cleanup: María's ISR restored to calculated value: {updated_entry['isr']}")
        print(f"  Override flag: {updated_entry.get('isr_manual_override_entry')}")


class TestPayrollEntryModel:
    """Test PayrollEntryCreate model accepts isr_override field"""
    
    def test_model_accepts_isr_override_field(self, api_client):
        """Verify the API accepts isr_override in the request body"""
        get_response = api_client.get(f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}")
        assert get_response.status_code == 200
        entry = get_response.json()
        
        # Send update with isr_override
        update_data = {
            "period_id": entry["period_id"],
            "employee_id": entry["employee_id"],
            "base_salary": entry["base_salary"],
            "overtime_day_hours": 0,
            "overtime_night_hours": 0,
            "overtime_weekend_hours": 0,
            "overtime_holiday_hours": 0,
            "bonuses": 0,
            "commissions": 0,
            "additional_deductions": [],
            "isr_override": 750.0  # Keep existing override
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/payroll/entries/{TEST_ENTRY_ID}",
            json=update_data
        )
        
        # Should not return 422 (validation error)
        assert response.status_code != 422, "API rejected isr_override field - model may not have the field"
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        print("Model accepts isr_override field: PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
