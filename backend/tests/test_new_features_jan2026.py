"""
Test new features: CSV Preview and OBREROS_NG payroll type
January 2026 iteration
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hrpayroll-1.preview.emergentagent.com')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_refactor@fortexa.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}


class TestPayrollTypes(TestAuth):
    """Test payroll types including OBREROS_NG"""
    
    def test_get_payroll_types_includes_obreros_ng(self, headers):
        """Verify OBREROS_NG is in the list of payroll types"""
        response = requests.get(f"{BASE_URL}/api/payroll-v2/payroll-types", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        codes = [t['code'] for t in data]
        assert 'OBREROS_NG' in codes, "OBREROS_NG should be in payroll types"
        
        # Verify OBREROS_NG details
        obreros = next((t for t in data if t['code'] == 'OBREROS_NG'), None)
        assert obreros is not None
        assert obreros['name'] == 'Obreros NG 07/2027'
        assert 'ISR 2%' in obreros['description'] or 'Solo ISR' in obreros['description']


class TestObrerosNGPayroll(TestAuth):
    """Test OBREROS_NG payroll calculations"""
    
    def test_obreros_ng_period_exists(self, headers):
        """Verify OBREROS_NG period was created"""
        response = requests.get(f"{BASE_URL}/api/payroll-v2/periods", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        obreros_periods = [p for p in data if p.get('payroll_type') == 'OBREROS_NG']
        assert len(obreros_periods) >= 1, "At least one OBREROS_NG period should exist"
    
    def test_obreros_ng_period_details(self, headers):
        """Verify OBREROS_NG period has correct deductions"""
        # Get periods
        response = requests.get(f"{BASE_URL}/api/payroll-v2/periods", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        obreros_period = next((p for p in data if p.get('payroll_type') == 'OBREROS_NG'), None)
        assert obreros_period is not None, "OBREROS_NG period should exist"
        
        # Get period details
        period_id = obreros_period['period_id']
        response = requests.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}", headers=headers)
        assert response.status_code == 200
        
        period_data = response.json()
        entries = period_data.get('entries', [])
        assert len(entries) > 0, "Period should have employees"
        
        # Verify each entry has correct deductions
        for entry in entries:
            # SFS and AFP should be 0 for OBREROS_NG
            assert entry.get('sfs_employee') == 0, f"SFS employee should be 0, got {entry.get('sfs_employee')}"
            assert entry.get('afp_employee') == 0, f"AFP employee should be 0, got {entry.get('afp_employee')}"
            
            # ISR should be 2% of gross salary
            gross = entry.get('gross_salary', 0)
            expected_isr = round(gross * 0.02, 2)
            actual_isr = entry.get('isr', 0)
            assert abs(actual_isr - expected_isr) < 0.01, f"ISR should be {expected_isr}, got {actual_isr}"
            
            # Employer contributions should be 0
            assert entry.get('sfs_employer') == 0, f"SFS employer should be 0"
            assert entry.get('afp_employer') == 0, f"AFP employer should be 0"
            assert entry.get('srl_employer') == 0, f"SRL employer should be 0"
            assert entry.get('infotep_employer') == 0, f"INFOTEP employer should be 0"
            
            # Total deductions should equal ISR only
            assert entry.get('total_deductions') == actual_isr, f"Total deductions should equal ISR"
            
            # Net salary should be gross - ISR
            expected_net = round(gross - actual_isr, 2)
            actual_net = entry.get('net_salary', 0)
            assert abs(actual_net - expected_net) < 0.01, f"Net salary should be {expected_net}, got {actual_net}"


class TestAccountingPreview(TestAuth):
    """Test CSV preview functionality for journal entries"""
    
    def test_get_journal_entries(self, headers):
        """Verify journal entries exist"""
        response = requests.get(f"{BASE_URL}/api/accounting/journal-entries", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "Should have at least one journal entry"
    
    def test_preview_summary_format(self, headers):
        """Test preview endpoint with summary format"""
        # Get first journal entry
        response = requests.get(f"{BASE_URL}/api/accounting/journal-entries", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) > 0
        
        entry_id = entries[0]['entry_id']
        
        # Test preview with summary format
        response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/{entry_id}/preview?format=summary",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('entry_id') == entry_id
        assert data.get('format') == 'summary'
        assert 'rows' in data
        assert 'totals' in data
        assert 'debits' in data['totals']
        assert 'credits' in data['totals']
        
        # Verify totals are balanced
        assert data['totals']['debits'] == data['totals']['credits'], "Debits should equal credits"
    
    def test_preview_detailed_format(self, headers):
        """Test preview endpoint with detailed format"""
        # Get first journal entry
        response = requests.get(f"{BASE_URL}/api/accounting/journal-entries", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) > 0
        
        entry_id = entries[0]['entry_id']
        
        # Test preview with detailed format
        response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/{entry_id}/preview?format=detailed",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('entry_id') == entry_id
        assert data.get('format') == 'detailed'
        assert 'rows' in data
        assert 'totals' in data
        assert 'has_cost_center' in data
        
        # Verify row structure for detailed format
        if len(data['rows']) > 0:
            row = data['rows'][0]
            assert 'account_code' in row
            assert 'account_name' in row
            assert 'debit' in row
            assert 'credit' in row
    
    def test_preview_invalid_entry_returns_404(self, headers):
        """Test preview with invalid entry ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/invalid_entry_id/preview?format=summary",
            headers=headers
        )
        assert response.status_code == 404
    
    def test_export_csv_summary(self, headers):
        """Test CSV export with summary format"""
        # Get first journal entry
        response = requests.get(f"{BASE_URL}/api/accounting/journal-entries", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) > 0
        
        entry_id = entries[0]['entry_id']
        
        # Test export with summary format
        response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/{entry_id}/export?format=summary",
            headers=headers
        )
        assert response.status_code == 200
        assert 'text/csv' in response.headers.get('Content-Type', '')
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        assert 'resumido' in response.headers.get('Content-Disposition', '')
    
    def test_export_csv_detailed(self, headers):
        """Test CSV export with detailed format"""
        # Get first journal entry
        response = requests.get(f"{BASE_URL}/api/accounting/journal-entries", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) > 0
        
        entry_id = entries[0]['entry_id']
        
        # Test export with detailed format
        response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries/{entry_id}/export?format=detailed",
            headers=headers
        )
        assert response.status_code == 200
        assert 'text/csv' in response.headers.get('Content-Type', '')
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        assert 'detallado' in response.headers.get('Content-Disposition', '')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
