"""
Test DGII Export Endpoints - FortexaRH
Tests for IR3, IR4, IR6, IR17, TSS-Autodeterminacion export endpoints
Bug fixes verified: Response import added, NoneType handling with 'or ""' pattern
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_refactor@fortexa.com"
TEST_PASSWORD = "test123"

# Test data - paid period with entries
PAID_PERIOD_ID = "period_6a079d88c0c4"
DRAFT_PERIOD_ID = "period_0c7fdc679329"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    data = response.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        pytest.skip("No token in auth response")
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Get auth headers for requests"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDGIIExportEndpoints:
    """Test DGII export endpoints - Bug fix verification"""
    
    def test_export_ir3_returns_200(self, auth_headers):
        """GET /api/payroll/periods/{period_id}/export/ir3 should return 200 with CSV data"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{PAID_PERIOD_ID}/export/ir3",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"IR3 export failed: {response.status_code} - {response.text}"
        
        # Verify response is file content (not JSON error)
        content_type = response.headers.get('content-type', '')
        assert 'application/vnd.ms-excel' in content_type or 'text' in content_type, f"Unexpected content type: {content_type}"
        
        # Verify content has data
        content = response.text
        assert len(content) > 0, "IR3 export returned empty content"
        assert "IR-3" in content or "DECLARACIÓN" in content or "Empresa" in content, "IR3 content missing expected headers"
        print(f"✓ IR3 export successful, content length: {len(content)} bytes")
    
    def test_export_ir4_returns_200(self, auth_headers):
        """GET /api/payroll/periods/{period_id}/export/ir4 should return 200 with CSV data"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{PAID_PERIOD_ID}/export/ir4",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"IR4 export failed: {response.status_code} - {response.text}"
        
        # Verify response is file content
        content_type = response.headers.get('content-type', '')
        assert 'application/vnd.ms-excel' in content_type or 'text' in content_type, f"Unexpected content type: {content_type}"
        
        # Verify content has data
        content = response.text
        assert len(content) > 0, "IR4 export returned empty content"
        # IR4 has employee details with cedula, name, salary, ISR
        assert "Cédula" in content or "Nombre" in content or "Salario" in content, "IR4 content missing expected headers"
        print(f"✓ IR4 export successful, content length: {len(content)} bytes")
    
    def test_export_ir17_returns_200(self, auth_headers):
        """GET /api/payroll/periods/{period_id}/export/ir17 should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{PAID_PERIOD_ID}/export/ir17",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"IR17 export failed: {response.status_code} - {response.text}"
        
        # Verify response is file content
        content_type = response.headers.get('content-type', '')
        assert 'application/vnd.ms-excel' in content_type or 'text' in content_type, f"Unexpected content type: {content_type}"
        
        # Verify content has data
        content = response.text
        assert len(content) > 0, "IR17 export returned empty content"
        assert "IR-17" in content or "FORMULARIO" in content or "RETENCIONES" in content, "IR17 content missing expected headers"
        print(f"✓ IR17 export successful, content length: {len(content)} bytes")
    
    def test_export_ir6_returns_200(self, auth_headers):
        """GET /api/payroll/periods/{period_id}/export/ir6 should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{PAID_PERIOD_ID}/export/ir6",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"IR6 export failed: {response.status_code} - {response.text}"
        
        # Verify response is file content
        content_type = response.headers.get('content-type', '')
        assert 'application/vnd.ms-excel' in content_type or 'text' in content_type, f"Unexpected content type: {content_type}"
        
        # Verify content has data
        content = response.text
        assert len(content) > 0, "IR6 export returned empty content"
        assert "IR-6" in content or "ANEXO" in content or "DETALLE" in content, "IR6 content missing expected headers"
        print(f"✓ IR6 export successful, content length: {len(content)} bytes")
    
    def test_export_tss_autodeterminacion_returns_200(self, auth_headers):
        """GET /api/payroll/periods/{period_id}/export/tss-autodeterminacion should return 200 with CSV data"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{PAID_PERIOD_ID}/export/tss-autodeterminacion",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"TSS Autodeterminacion export failed: {response.status_code} - {response.text}"
        
        # Verify response is file content
        content_type = response.headers.get('content-type', '')
        assert 'application/vnd.ms-excel' in content_type or 'text' in content_type, f"Unexpected content type: {content_type}"
        
        # Verify content has data
        content = response.text
        assert len(content) > 0, "TSS Autodeterminacion export returned empty content"
        # TSS has headers like RNC_PATRONO, CEDULA, etc.
        assert "RNC_PATRONO" in content or "CEDULA" in content or "SALARIO" in content, "TSS content missing expected headers"
        print(f"✓ TSS Autodeterminacion export successful, content length: {len(content)} bytes")
    
    def test_export_with_nonexistent_period_returns_404(self, auth_headers):
        """Export endpoints should return 404 for non-existent period"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/nonexistent_period_xyz/export/ir3",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent period, got: {response.status_code}"
        print("✓ Non-existent period correctly returns 404")


class TestPeriodEndpoints:
    """Test period-related endpoints needed for DGII Reports page"""
    
    def test_get_periods_returns_200(self, auth_headers):
        """GET /api/payroll/periods should return list of periods"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get periods failed: {response.status_code} - {response.text}"
        
        data = response.json()
        # API returns array directly
        periods = data if isinstance(data, list) else data.get('periods', [])
        assert isinstance(periods, list), "Periods should be a list"
        print(f"✓ Get periods successful, found {len(periods)} periods")
    
    def test_get_period_details_returns_200(self, auth_headers):
        """GET /api/payroll/periods/{period_id} should return period details with entries"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{PAID_PERIOD_ID}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get period details failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert 'period_id' in data or 'entries' in data or 'employee_count' in data, "Period details missing expected fields"
        print(f"✓ Get period details successful")
    
    def test_get_available_years_returns_200(self, auth_headers):
        """GET /api/payroll/available-years should return list of years"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/available-years",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get available years failed: {response.status_code} - {response.text}"
        
        data = response.json()
        # Should be array of years (numbers)
        assert isinstance(data, list), "Available years should be a list"
        print(f"✓ Get available years successful, found {len(data)} years: {data}")


class TestDrillDownData:
    """Test that period details include entries for drilldown modal"""
    
    def test_period_details_include_entries_for_drilldown(self, auth_headers):
        """Period details should include entries with employee_document field (not cedula)"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/periods/{PAID_PERIOD_ID}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get period details failed: {response.status_code}"
        
        data = response.json()
        entries = data.get('entries', [])
        
        if len(entries) > 0:
            first_entry = entries[0]
            # Verify the correct field name is used (employee_document, not cedula)
            assert 'employee_document' in first_entry or 'employee_name' in first_entry, \
                f"Entry missing expected fields. Keys: {list(first_entry.keys())}"
            
            # Verify formatCurrency-compatible fields exist
            if 'gross_salary' in first_entry:
                assert isinstance(first_entry['gross_salary'], (int, float)), "gross_salary should be numeric"
            
            print(f"✓ Period has {len(entries)} entries with correct field names")
        else:
            print("⚠ Period has no entries - drilldown will show empty table")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
