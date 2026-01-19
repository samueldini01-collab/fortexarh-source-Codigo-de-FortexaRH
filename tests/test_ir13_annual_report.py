"""
Test IR-13 Annual Report and Available Years Endpoints
Tests the new IR-13 annual declaration feature that consolidates monthly IR-4 data
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from previous iterations
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"


class TestIR13AnnualReport:
    """Tests for IR-13 annual report generation and available years endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    # ==================== Available Years Endpoint Tests ====================
    
    def test_available_years_endpoint_returns_200(self):
        """Test GET /api/payroll-v2/available-years returns 200"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_available_years_returns_array(self):
        """Test available-years returns an array"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
    
    def test_available_years_structure(self):
        """Test available-years returns correct structure with year and periods_count"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            year_info = data[0]
            assert "year" in year_info, "Missing 'year' field"
            assert "periods_count" in year_info, "Missing 'periods_count' field"
            assert isinstance(year_info["year"], int), "Year should be integer"
            assert isinstance(year_info["periods_count"], int), "periods_count should be integer"
            print(f"Available years: {data}")
    
    def test_available_years_sorted_descending(self):
        """Test available-years returns years sorted in descending order"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 1:
            years = [y["year"] for y in data]
            assert years == sorted(years, reverse=True), "Years should be sorted descending"
    
    def test_available_years_requires_auth(self):
        """Test available-years requires authentication"""
        unauth_session = requests.Session()
        response = unauth_session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    # ==================== IR-13 Export Endpoint Tests ====================
    
    def test_ir13_export_requires_auth(self):
        """Test IR-13 export requires authentication"""
        unauth_session = requests.Session()
        response = unauth_session.get(f"{BASE_URL}/api/payroll-v2/annual-report/ir13/2024")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_ir13_export_invalid_year_returns_404(self):
        """Test IR-13 export with year that has no data returns 404"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/annual-report/ir13/1999")
        assert response.status_code == 404, f"Expected 404 for year with no data, got {response.status_code}"
    
    def test_ir13_export_with_valid_year(self):
        """Test IR-13 export with a valid year returns Excel file"""
        # First get available years
        years_response = self.session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        assert years_response.status_code == 200
        years = years_response.json()
        
        if not years:
            pytest.skip("No available years with payroll data")
        
        # Use the most recent year
        test_year = years[0]["year"]
        print(f"Testing IR-13 export for year: {test_year}")
        
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/annual-report/ir13/{test_year}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify it's an Excel file
        content_type = response.headers.get("Content-Type", "")
        assert "excel" in content_type.lower() or "application/vnd.ms-excel" in content_type, \
            f"Expected Excel content type, got {content_type}"
        
        # Verify content disposition header
        content_disp = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp, "Should have attachment disposition"
        assert f"IR13" in content_disp, "Filename should contain IR13"
        assert str(test_year) in content_disp, f"Filename should contain year {test_year}"
        
        # Verify file has content
        assert len(response.content) > 0, "Excel file should have content"
        print(f"IR-13 Excel file size: {len(response.content)} bytes")
    
    def test_ir13_export_file_structure(self):
        """Test IR-13 export generates valid Excel with expected structure"""
        years_response = self.session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        years = years_response.json()
        
        if not years:
            pytest.skip("No available years with payroll data")
        
        test_year = years[0]["year"]
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/annual-report/ir13/{test_year}")
        
        assert response.status_code == 200
        
        # Check Excel magic bytes (XLS format starts with D0 CF 11 E0)
        content = response.content
        if len(content) >= 4:
            # XLS files start with compound document header
            xls_magic = content[:4]
            # D0 CF 11 E0 is the magic number for OLE compound documents (XLS)
            expected_magic = bytes([0xD0, 0xCF, 0x11, 0xE0])
            assert xls_magic == expected_magic, f"Invalid XLS file header: {xls_magic.hex()}"
            print("Valid XLS file format confirmed")
    
    # ==================== Integration Tests ====================
    
    def test_ir13_consolidates_monthly_data(self):
        """Test that IR-13 endpoint processes all monthly periods for the year"""
        years_response = self.session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        years = years_response.json()
        
        if not years:
            pytest.skip("No available years with payroll data")
        
        test_year = years[0]["year"]
        periods_count = years[0]["periods_count"]
        
        print(f"Year {test_year} has {periods_count} periods")
        
        # Get the IR-13 report
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/annual-report/ir13/{test_year}")
        assert response.status_code == 200
        
        # The report should be generated successfully if there are periods
        assert len(response.content) > 1000, "IR-13 report should have substantial content"
    
    def test_periods_endpoint_returns_data_for_year(self):
        """Verify periods endpoint returns data that matches available years"""
        years_response = self.session.get(f"{BASE_URL}/api/payroll-v2/available-years")
        years = years_response.json()
        
        if not years:
            pytest.skip("No available years")
        
        # Get all periods
        periods_response = self.session.get(f"{BASE_URL}/api/payroll-v2/periods")
        assert periods_response.status_code == 200
        periods = periods_response.json()
        
        # Verify periods exist for the available years
        test_year = years[0]["year"]
        year_periods = [p for p in periods if p.get("year") == test_year]
        
        assert len(year_periods) == years[0]["periods_count"], \
            f"Periods count mismatch: expected {years[0]['periods_count']}, found {len(year_periods)}"
        
        print(f"Verified {len(year_periods)} periods for year {test_year}")


class TestIR13EdgeCases:
    """Edge case tests for IR-13 functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_ir13_future_year_returns_404(self):
        """Test IR-13 for future year returns 404"""
        future_year = datetime.now().year + 5
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/annual-report/ir13/{future_year}")
        assert response.status_code == 404
    
    def test_ir13_invalid_year_format(self):
        """Test IR-13 with invalid year format returns error"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/annual-report/ir13/invalid")
        # Should return 422 (validation error) for non-integer year
        assert response.status_code == 422, f"Expected 422 for invalid year, got {response.status_code}"
    
    def test_ir13_negative_year(self):
        """Test IR-13 with negative year"""
        response = self.session.get(f"{BASE_URL}/api/payroll-v2/annual-report/ir13/-2024")
        # Should return 404 (no data) or 422 (validation)
        assert response.status_code in [404, 422], f"Expected 404/422 for negative year, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
