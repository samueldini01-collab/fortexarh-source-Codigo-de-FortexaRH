"""
Test TSS and IR Export Endpoints - Phase 2 FortexaRH
Tests for:
- GET /api/payroll-v2/periods/{id}/export/tss-autodeterminacion
- GET /api/payroll-v2/periods/{id}/export/tss-novedades
- GET /api/payroll-v2/periods/{id}/export/ir3
- GET /api/payroll-v2/periods/{id}/export/ir4 (NEW - Detalle Mensual de Retenciones)
- GET /api/payroll-v2/periods/{id}/export/ir17
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTSSIRExports:
    """Test TSS and IR export endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed - skipping tests")
    
    def test_get_paid_periods(self):
        """Get list of paid periods to use for export tests"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        assert response.status_code == 200
        
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        print(f"Found {len(paid_periods)} paid periods")
        if paid_periods:
            print(f"First paid period: {paid_periods[0].get('period_id')}")
        
        return paid_periods
    
    def test_tss_autodeterminacion_export_requires_paid_period(self):
        """Test that TSS Autodeterminación export requires a paid period"""
        # First get periods
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        assert response.status_code == 200
        
        periods = response.json()
        unpaid_periods = [p for p in periods if p.get("status") != "paid"]
        
        if unpaid_periods:
            period_id = unpaid_periods[0]["period_id"]
            response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/tss-autodeterminacion")
            # Should return 400 for unpaid periods
            assert response.status_code == 400
            print(f"Correctly rejected unpaid period: {response.json()}")
        else:
            print("No unpaid periods to test - skipping")
    
    def test_tss_autodeterminacion_export_success(self):
        """Test TSS Autodeterminación Excel export for paid period"""
        # Get paid periods
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        assert response.status_code == 200
        
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods available for testing")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/tss-autodeterminacion")
        
        assert response.status_code == 200
        assert "application/vnd.ms-excel" in response.headers.get("Content-Type", "")
        assert "Content-Disposition" in response.headers
        assert "TSS_Autodeterminacion" in response.headers.get("Content-Disposition", "")
        
        # Verify file size is reasonable (should be > 1KB for valid Excel)
        content_length = len(response.content)
        assert content_length > 1000, f"File too small: {content_length} bytes"
        print(f"TSS Autodeterminación downloaded: {content_length} bytes")
    
    def test_tss_novedades_export_success(self):
        """Test TSS Novedades Excel export for paid period"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        assert response.status_code == 200
        
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods available for testing")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/tss-novedades")
        
        assert response.status_code == 200
        assert "application/vnd.ms-excel" in response.headers.get("Content-Type", "")
        assert "Content-Disposition" in response.headers
        assert "TSS_Novedades" in response.headers.get("Content-Disposition", "")
        
        content_length = len(response.content)
        assert content_length > 1000, f"File too small: {content_length} bytes"
        print(f"TSS Novedades downloaded: {content_length} bytes")
    
    def test_ir3_export_success(self):
        """Test IR-3 (Retenciones) Excel export for paid period"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        assert response.status_code == 200
        
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods available for testing")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/ir3")
        
        assert response.status_code == 200
        assert "application/vnd.ms-excel" in response.headers.get("Content-Type", "")
        assert "Content-Disposition" in response.headers
        assert "IR3_Retenciones" in response.headers.get("Content-Disposition", "")
        
        content_length = len(response.content)
        assert content_length > 1000, f"File too small: {content_length} bytes"
        print(f"IR-3 downloaded: {content_length} bytes")
    
    def test_ir4_export_success(self):
        """Test IR-4 (Detalle Mensual de Retenciones) Excel export for paid period"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        assert response.status_code == 200
        
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods available for testing")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/ir4")
        
        assert response.status_code == 200
        assert "application/vnd.ms-excel" in response.headers.get("Content-Type", "")
        assert "Content-Disposition" in response.headers
        assert "IR4_Detalle_Retenciones" in response.headers.get("Content-Disposition", "")
        
        content_length = len(response.content)
        assert content_length > 1000, f"File too small: {content_length} bytes"
        print(f"IR-4 downloaded: {content_length} bytes")
    
    def test_ir17_export_success(self):
        """Test IR-17 (Declaración) Excel export for paid period"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        assert response.status_code == 200
        
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods available for testing")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/ir17")
        
        assert response.status_code == 200
        assert "application/vnd.ms-excel" in response.headers.get("Content-Type", "")
        assert "Content-Disposition" in response.headers
        assert "IR17_Declaracion" in response.headers.get("Content-Disposition", "")
        
        content_length = len(response.content)
        assert content_length > 1000, f"File too small: {content_length} bytes"
        print(f"IR-17 downloaded: {content_length} bytes")
    
    def test_export_nonexistent_period(self):
        """Test export with non-existent period ID"""
        fake_period_id = "period_nonexistent123"
        
        # Test all export endpoints with fake period
        endpoints = [
            "tss-autodeterminacion",
            "tss-novedades",
            "ir3",
            "ir4",
            "ir17"
        ]
        
        for endpoint in endpoints:
            response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{fake_period_id}/export/{endpoint}")
            assert response.status_code == 404, f"Expected 404 for {endpoint}, got {response.status_code}"
            print(f"{endpoint}: Correctly returned 404 for non-existent period")
    
    def test_specific_period_export(self):
        """Test export with specific period ID from test request"""
        # Use the period ID mentioned in the test request
        period_id = "period_880327467270"
        
        # Try to export - may fail if period doesn't exist or isn't paid
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/tss-autodeterminacion")
        
        if response.status_code == 200:
            print(f"Successfully exported TSS Autodeterminación for {period_id}")
            assert "application/vnd.ms-excel" in response.headers.get("Content-Type", "")
        elif response.status_code == 404:
            print(f"Period {period_id} not found - may need to create test data")
        elif response.status_code == 400:
            print(f"Period {period_id} exists but is not paid: {response.json()}")
        else:
            print(f"Unexpected status {response.status_code}: {response.text}")


class TestTSSGeneratorFunctions:
    """Test the tss_generator.py functions directly via API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_excel_file_structure_autodeterminacion(self):
        """Verify TSS Autodeterminación Excel has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/tss-autodeterminacion")
        
        assert response.status_code == 200
        
        # Check Excel magic bytes (xls format starts with D0 CF 11 E0)
        content = response.content
        assert content[:4] == b'\xd0\xcf\x11\xe0', "Not a valid XLS file"
        print("TSS Autodeterminación: Valid XLS format confirmed")
    
    def test_excel_file_structure_novedades(self):
        """Verify TSS Novedades Excel has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/tss-novedades")
        
        assert response.status_code == 200
        
        content = response.content
        assert content[:4] == b'\xd0\xcf\x11\xe0', "Not a valid XLS file"
        print("TSS Novedades: Valid XLS format confirmed")
    
    def test_excel_file_structure_ir3(self):
        """Verify IR-3 Excel has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/ir3")
        
        assert response.status_code == 200
        
        content = response.content
        assert content[:4] == b'\xd0\xcf\x11\xe0', "Not a valid XLS file"
        print("IR-3: Valid XLS format confirmed")
    
    def test_excel_file_structure_ir17(self):
        """Verify IR-17 Excel has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/ir17")
        
        assert response.status_code == 200
        
        content = response.content
        assert content[:4] == b'\xd0\xcf\x11\xe0', "Not a valid XLS file"
        print("IR-17: Valid XLS format confirmed")
    
    def test_excel_file_structure_ir4(self):
        """Verify IR-4 Excel has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        periods = response.json()
        paid_periods = [p for p in periods if p.get("status") == "paid"]
        
        if not paid_periods:
            pytest.skip("No paid periods")
        
        period_id = paid_periods[0]["period_id"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods/{period_id}/export/ir4")
        
        assert response.status_code == 200
        
        content = response.content
        assert content[:4] == b'\xd0\xcf\x11\xe0', "Not a valid XLS file"
        print("IR-4: Valid XLS format confirmed")
