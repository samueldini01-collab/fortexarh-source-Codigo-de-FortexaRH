"""
Two-Factor Authentication (2FA) Recovery Codes API Tests for FortexaRH
Tests: verify-setup returns recovery codes, regenerate-recovery-codes, verify-recovery login
Uses pyotp to generate valid TOTP codes for testing
"""
import pytest
import requests
import os
import pyotp
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "test_refactor@fortexa.com"
TEST_USER_PASSWORD = "test123"


class Test2FARecoveryCodes:
    """Tests for 2FA recovery codes feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login to get auth token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        if data.get("requires_2fa"):
            pytest.skip("2FA is currently enabled for test user - cannot run these tests")
        
        self.token = data["token"]
        self.user_id = data.get("user", {}).get("user_id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.totp_secret = None
        yield
        # Cleanup: ensure 2FA is disabled after tests
        self._cleanup_2fa()
    
    def _cleanup_2fa(self):
        """Ensure 2FA is disabled after test class"""
        try:
            status_res = self.session.get(f"{BASE_URL}/api/auth/2fa/status")
            if status_res.status_code == 200 and status_res.json().get("totp_enabled"):
                if self.totp_secret:
                    totp = pyotp.TOTP(self.totp_secret)
                    time.sleep(1)
                    code = totp.now()
                    self.session.post(f"{BASE_URL}/api/auth/2fa/disable", json={"code": code})
                    print("Cleanup: 2FA disabled")
        except Exception as e:
            print(f"Cleanup check failed: {e}")

    def test_01_status_returns_recovery_codes_remaining_field(self):
        """GET /api/auth/2fa/status should return recovery_codes_remaining field"""
        response = self.session.get(f"{BASE_URL}/api/auth/2fa/status")
        assert response.status_code == 200, f"Status check failed: {response.text}"
        data = response.json()
        
        assert "totp_enabled" in data, "Expected totp_enabled in response"
        assert "recovery_codes_remaining" in data, "Expected recovery_codes_remaining in response"
        assert isinstance(data["recovery_codes_remaining"], int), "recovery_codes_remaining should be int"
        
        print(f"PASSED: 2FA status returns recovery_codes_remaining={data['recovery_codes_remaining']}")

    def test_02_verify_setup_returns_recovery_codes(self):
        """POST /api/auth/2fa/verify-setup should return recovery_codes array when enabling 2FA"""
        # Step 1: Setup 2FA
        setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        if setup_response.status_code == 400:
            pytest.skip("2FA already enabled")
        
        assert setup_response.status_code == 200, f"Setup failed: {setup_response.text}"
        secret = setup_response.json()["secret"]
        self.totp_secret = secret
        print(f"Step 1 PASSED: 2FA setup successful")
        
        # Step 2: Verify setup with valid code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        verify_response = self.session.post(f"{BASE_URL}/api/auth/2fa/verify-setup", json={
            "code": code
        })
        assert verify_response.status_code == 200, f"Verify setup failed: {verify_response.text}"
        data = verify_response.json()
        
        # Check response structure
        assert "message" in data, "Expected message in response"
        assert data.get("totp_enabled") == True, "Expected totp_enabled=true"
        assert "recovery_codes" in data, "Expected recovery_codes in response"
        assert isinstance(data["recovery_codes"], list), "recovery_codes should be a list"
        assert len(data["recovery_codes"]) == 10, f"Expected 10 recovery codes, got {len(data['recovery_codes'])}"
        
        # Validate recovery code format (8 hex chars, uppercase)
        for code in data["recovery_codes"]:
            assert len(code) == 8, f"Recovery code should be 8 chars, got {len(code)}"
            assert code.isalnum(), f"Recovery code should be alphanumeric: {code}"
            assert code.isupper(), f"Recovery code should be uppercase: {code}"
        
        print(f"Step 2 PASSED: verify-setup returns {len(data['recovery_codes'])} recovery codes")
        
        # Step 3: Verify status shows 10 codes remaining
        status_response = self.session.get(f"{BASE_URL}/api/auth/2fa/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("recovery_codes_remaining") == 10, f"Expected 10 recovery codes remaining, got {status_data.get('recovery_codes_remaining')}"
        
        print(f"Step 3 PASSED: Status shows 10 recovery codes remaining")
        
        # Cleanup: disable 2FA
        time.sleep(1)
        disable_code = totp.now()
        disable_response = self.session.post(f"{BASE_URL}/api/auth/2fa/disable", json={"code": disable_code})
        assert disable_response.status_code == 200, f"Disable failed: {disable_response.text}"
        print("Cleanup PASSED: 2FA disabled")

    def test_03_regenerate_recovery_codes(self):
        """POST /api/auth/2fa/regenerate-recovery-codes should generate new codes with TOTP verification"""
        # Step 1: Setup and enable 2FA first
        setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        if setup_response.status_code == 400:
            pytest.skip("2FA already enabled")
        
        assert setup_response.status_code == 200
        secret = setup_response.json()["secret"]
        self.totp_secret = secret
        
        totp = pyotp.TOTP(secret)
        code = totp.now()
        verify_response = self.session.post(f"{BASE_URL}/api/auth/2fa/verify-setup", json={"code": code})
        assert verify_response.status_code == 200
        original_codes = verify_response.json()["recovery_codes"]
        print(f"Step 1 PASSED: 2FA enabled with initial recovery codes")
        
        # Step 2: Regenerate recovery codes
        time.sleep(1)  # Wait for new TOTP window
        regen_code = totp.now()
        regen_response = self.session.post(f"{BASE_URL}/api/auth/2fa/regenerate-recovery-codes", json={
            "code": regen_code
        })
        assert regen_response.status_code == 200, f"Regenerate failed: {regen_response.text}"
        regen_data = regen_response.json()
        
        assert "message" in regen_data, "Expected message in response"
        assert "recovery_codes" in regen_data, "Expected recovery_codes in response"
        assert len(regen_data["recovery_codes"]) == 10, f"Expected 10 new recovery codes"
        
        # Verify new codes are different from original
        new_codes = regen_data["recovery_codes"]
        assert new_codes != original_codes, "New codes should be different from original"
        
        print(f"Step 2 PASSED: Regenerated {len(new_codes)} new recovery codes")
        
        # Cleanup
        time.sleep(1)
        disable_code = totp.now()
        self.session.post(f"{BASE_URL}/api/auth/2fa/disable", json={"code": disable_code})

    def test_04_regenerate_requires_valid_totp(self):
        """POST /api/auth/2fa/regenerate-recovery-codes with invalid code should fail"""
        # Setup 2FA first
        setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        if setup_response.status_code == 400:
            pytest.skip("2FA already enabled")
        
        assert setup_response.status_code == 200
        secret = setup_response.json()["secret"]
        self.totp_secret = secret
        
        totp = pyotp.TOTP(secret)
        code = totp.now()
        self.session.post(f"{BASE_URL}/api/auth/2fa/verify-setup", json={"code": code})
        
        # Try regenerate with invalid code
        regen_response = self.session.post(f"{BASE_URL}/api/auth/2fa/regenerate-recovery-codes", json={
            "code": "000000"  # Invalid code
        })
        assert regen_response.status_code == 400, f"Expected 400 for invalid code, got {regen_response.status_code}"
        
        print(f"PASSED: Regenerate with invalid TOTP code returns 400")
        
        # Cleanup
        time.sleep(1)
        disable_code = totp.now()
        self.session.post(f"{BASE_URL}/api/auth/2fa/disable", json={"code": disable_code})

    def test_05_regenerate_requires_2fa_enabled(self):
        """POST /api/auth/2fa/regenerate-recovery-codes without 2FA enabled should fail"""
        # Make sure 2FA is disabled
        status_response = self.session.get(f"{BASE_URL}/api/auth/2fa/status")
        if status_response.json().get("totp_enabled"):
            pytest.skip("2FA is enabled, cannot test this case")
        
        regen_response = self.session.post(f"{BASE_URL}/api/auth/2fa/regenerate-recovery-codes", json={
            "code": "123456"
        })
        assert regen_response.status_code == 400, f"Expected 400 when 2FA not enabled, got {regen_response.status_code}"
        
        print(f"PASSED: Regenerate without 2FA enabled returns 400")

    def test_06_verify_recovery_code_login(self):
        """POST /api/auth/2fa/verify-recovery should allow login with recovery code"""
        # Step 1: Setup and enable 2FA
        setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        if setup_response.status_code == 400:
            pytest.skip("2FA already enabled")
        
        assert setup_response.status_code == 200
        secret = setup_response.json()["secret"]
        self.totp_secret = secret
        
        totp = pyotp.TOTP(secret)
        code = totp.now()
        verify_response = self.session.post(f"{BASE_URL}/api/auth/2fa/verify-setup", json={"code": code})
        assert verify_response.status_code == 200
        recovery_codes = verify_response.json()["recovery_codes"]
        first_recovery_code = recovery_codes[0]
        print(f"Step 1 PASSED: 2FA enabled, got recovery code: {first_recovery_code}")
        
        # Step 2: Login to get temp_token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get("requires_2fa") == True
        user_id = login_data["user_id"]
        temp_token = login_data["temp_token"]
        print(f"Step 2 PASSED: Login requires 2FA, got temp_token")
        
        # Step 3: Verify recovery code login
        recovery_response = requests.post(f"{BASE_URL}/api/auth/2fa/verify-recovery", json={
            "user_id": user_id,
            "temp_token": temp_token,
            "recovery_code": first_recovery_code
        })
        assert recovery_response.status_code == 200, f"Recovery login failed: {recovery_response.text}"
        recovery_data = recovery_response.json()
        
        assert "token" in recovery_data, "Expected token in response"
        assert "user" in recovery_data, "Expected user in response"
        assert recovery_data["user"]["email"] == TEST_USER_EMAIL
        assert "recovery_codes_remaining" in recovery_data, "Expected recovery_codes_remaining in response"
        assert recovery_data["recovery_codes_remaining"] == 9, f"Expected 9 codes remaining (one used), got {recovery_data['recovery_codes_remaining']}"
        
        print(f"Step 3 PASSED: Recovery code login successful, {recovery_data['recovery_codes_remaining']} codes remaining")
        
        # Cleanup: disable 2FA using new token
        new_token = recovery_data["token"]
        time.sleep(1)
        disable_code = totp.now()
        disable_response = requests.post(f"{BASE_URL}/api/auth/2fa/disable", json={"code": disable_code}, 
                                         headers={"Authorization": f"Bearer {new_token}", "Content-Type": "application/json"})
        assert disable_response.status_code == 200

    def test_07_recovery_code_one_time_use(self):
        """Recovery codes should be single-use (cannot reuse same code)"""
        # Setup 2FA
        setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        if setup_response.status_code == 400:
            pytest.skip("2FA already enabled")
        
        assert setup_response.status_code == 200
        secret = setup_response.json()["secret"]
        self.totp_secret = secret
        
        totp = pyotp.TOTP(secret)
        code = totp.now()
        verify_response = self.session.post(f"{BASE_URL}/api/auth/2fa/verify-setup", json={"code": code})
        assert verify_response.status_code == 200
        recovery_codes = verify_response.json()["recovery_codes"]
        first_recovery_code = recovery_codes[0]
        
        # First use of recovery code
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        login_data = login_response.json()
        temp_token = login_data["temp_token"]
        user_id = login_data["user_id"]
        
        recovery_response = requests.post(f"{BASE_URL}/api/auth/2fa/verify-recovery", json={
            "user_id": user_id,
            "temp_token": temp_token,
            "recovery_code": first_recovery_code
        })
        assert recovery_response.status_code == 200
        new_token = recovery_response.json()["token"]
        
        # Try to reuse same recovery code
        login_response2 = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        login_data2 = login_response2.json()
        temp_token2 = login_data2["temp_token"]
        
        reuse_response = requests.post(f"{BASE_URL}/api/auth/2fa/verify-recovery", json={
            "user_id": user_id,
            "temp_token": temp_token2,
            "recovery_code": first_recovery_code  # Same code again
        })
        assert reuse_response.status_code == 401, f"Expected 401 for reused recovery code, got {reuse_response.status_code}"
        
        print(f"PASSED: Recovery code cannot be reused (401 on second attempt)")
        
        # Cleanup
        time.sleep(1)
        disable_code = totp.now()
        requests.post(f"{BASE_URL}/api/auth/2fa/disable", json={"code": disable_code},
                     headers={"Authorization": f"Bearer {new_token}", "Content-Type": "application/json"})

    def test_08_invalid_recovery_code_fails(self):
        """POST /api/auth/2fa/verify-recovery with invalid code should fail"""
        # Setup 2FA
        setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        if setup_response.status_code == 400:
            pytest.skip("2FA already enabled")
        
        assert setup_response.status_code == 200
        secret = setup_response.json()["secret"]
        self.totp_secret = secret
        
        totp = pyotp.TOTP(secret)
        code = totp.now()
        self.session.post(f"{BASE_URL}/api/auth/2fa/verify-setup", json={"code": code})
        
        # Login to get temp_token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        login_data = login_response.json()
        temp_token = login_data["temp_token"]
        user_id = login_data["user_id"]
        
        # Try with invalid recovery code
        recovery_response = requests.post(f"{BASE_URL}/api/auth/2fa/verify-recovery", json={
            "user_id": user_id,
            "temp_token": temp_token,
            "recovery_code": "INVALID1"  # Invalid code
        })
        assert recovery_response.status_code == 401, f"Expected 401 for invalid recovery code"
        
        print(f"PASSED: Invalid recovery code returns 401")
        
        # Cleanup
        time.sleep(1)
        disable_code = totp.now()
        self.session.post(f"{BASE_URL}/api/auth/2fa/disable", json={"code": disable_code})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
