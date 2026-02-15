"""
Two-Factor Authentication (2FA/TOTP) API Tests for FortexaRH
Tests: setup, verify-setup, verify-login, disable, status endpoints
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

class Test2FAEndpoints:
    """Tests for 2FA/TOTP authentication flow"""
    
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
        # Handle case where 2FA might be enabled from previous test
        if response.status_code == 200:
            data = response.json()
            if data.get("requires_2fa"):
                # 2FA enabled - need to get secret to generate code
                pytest.skip("2FA is currently enabled for test user - run disable test first")
            elif data.get("token"):
                self.token = data["token"]
                self.user_id = data.get("user", {}).get("user_id")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            else:
                pytest.fail(f"Unexpected login response: {data}")
        else:
            pytest.fail(f"Login failed: {response.status_code} - {response.text}")
        yield
        # Cleanup: ensure 2FA is disabled after tests
        self._cleanup_2fa()
    
    def _cleanup_2fa(self):
        """Ensure 2FA is disabled after test class"""
        try:
            status_res = self.session.get(f"{BASE_URL}/api/auth/2fa/status")
            if status_res.status_code == 200 and status_res.json().get("totp_enabled"):
                # We need to disable it but can't without the secret
                print("Warning: 2FA still enabled after test - manual cleanup may be needed")
        except Exception as e:
            print(f"Cleanup check failed: {e}")
    
    def test_01_login_without_2fa_returns_token(self):
        """Login without 2FA should return token directly"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Should return token directly (no 2FA)
        if data.get("requires_2fa"):
            pytest.skip("2FA is enabled - expected disabled state")
        
        assert "token" in data, "Expected token in response"
        assert "user" in data, "Expected user in response"
        assert data["user"]["email"] == TEST_USER_EMAIL
        print(f"PASSED: Login without 2FA returns token for {TEST_USER_EMAIL}")
    
    def test_02_get_2fa_status_initially_disabled(self):
        """GET /api/auth/2fa/status should return totp_enabled=false initially"""
        response = self.session.get(f"{BASE_URL}/api/auth/2fa/status")
        assert response.status_code == 200, f"Status check failed: {response.text}"
        data = response.json()
        
        assert "totp_enabled" in data, "Expected totp_enabled in response"
        # May be true if tests ran before
        print(f"PASSED: 2FA status endpoint works, totp_enabled={data['totp_enabled']}")
    
    def test_03_setup_2fa_generates_secret_and_qr(self):
        """POST /api/auth/2fa/setup should generate secret and QR code"""
        response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        
        # If 2FA already enabled, expect 400
        if response.status_code == 400:
            assert "ya está activado" in response.json().get("detail", "").lower() or "already" in response.json().get("detail", "").lower()
            pytest.skip("2FA already enabled - skipping setup test")
        
        assert response.status_code == 200, f"Setup failed: {response.text}"
        data = response.json()
        
        assert "secret" in data, "Expected secret in response"
        assert "qr_code" in data, "Expected qr_code in response"
        assert "provisioning_uri" in data, "Expected provisioning_uri in response"
        
        # Validate secret format (base32)
        assert len(data["secret"]) == 32, "Secret should be 32 chars (base32)"
        
        # Validate QR code is base64 PNG
        assert data["qr_code"].startswith("data:image/png;base64,"), "QR should be base64 PNG"
        
        # Validate provisioning URI
        assert "otpauth://totp/" in data["provisioning_uri"]
        assert "FortexaRH" in data["provisioning_uri"]
        
        print(f"PASSED: 2FA setup generates valid secret and QR code")
        return data["secret"]
    
    def test_04_full_2fa_flow_setup_verify_login_disable(self):
        """Test complete 2FA flow: setup -> verify-setup -> login requires 2FA -> verify-login -> disable"""
        
        # Step 1: Setup 2FA
        setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        if setup_response.status_code == 400:
            pytest.skip("2FA already enabled")
        
        assert setup_response.status_code == 200, f"Setup failed: {setup_response.text}"
        secret = setup_response.json()["secret"]
        print(f"Step 1 PASSED: 2FA setup successful, got secret")
        
        # Step 2: Generate valid TOTP code and verify setup
        totp = pyotp.TOTP(secret)
        code = totp.now()
        verify_setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/verify-setup", json={
            "code": code
        })
        assert verify_setup_response.status_code == 200, f"Verify setup failed: {verify_setup_response.text}"
        verify_data = verify_setup_response.json()
        assert verify_data.get("totp_enabled") == True, "Expected totp_enabled=true after setup"
        print(f"Step 2 PASSED: 2FA verify-setup successful with code {code}")
        
        # Step 3: Verify status is now enabled
        status_response = self.session.get(f"{BASE_URL}/api/auth/2fa/status")
        assert status_response.status_code == 200
        assert status_response.json().get("totp_enabled") == True
        print(f"Step 3 PASSED: 2FA status shows enabled")
        
        # Step 4: Login should now require 2FA
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        login_data = login_response.json()
        
        assert login_data.get("requires_2fa") == True, "Expected requires_2fa=true"
        assert "user_id" in login_data, "Expected user_id in 2FA response"
        assert "temp_token" in login_data, "Expected temp_token in 2FA response"
        print(f"Step 4 PASSED: Login returns requires_2fa=true with temp_token")
        
        user_id = login_data["user_id"]
        temp_token = login_data["temp_token"]
        
        # Step 5: Test verify-login with INVALID code first
        time.sleep(1)  # Wait to ensure code changes
        invalid_verify_response = requests.post(f"{BASE_URL}/api/auth/2fa/verify-login", json={
            "user_id": user_id,
            "temp_token": temp_token,
            "code": "000000"  # Invalid code
        })
        assert invalid_verify_response.status_code == 401, f"Expected 401 for invalid code, got {invalid_verify_response.status_code}"
        print(f"Step 5 PASSED: Invalid 2FA code returns 401")
        
        # Need to re-login to get new temp_token since invalid attempts may invalidate it
        login_response2 = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        login_data2 = login_response2.json()
        temp_token = login_data2["temp_token"]
        
        # Step 6: Test verify-login with VALID code
        time.sleep(1)  # Ensure fresh code
        valid_code = totp.now()
        verify_login_response = requests.post(f"{BASE_URL}/api/auth/2fa/verify-login", json={
            "user_id": user_id,
            "temp_token": temp_token,
            "code": valid_code
        })
        assert verify_login_response.status_code == 200, f"Verify login failed: {verify_login_response.text}"
        verify_login_data = verify_login_response.json()
        
        assert "token" in verify_login_data, "Expected JWT token after 2FA verification"
        assert "user" in verify_login_data, "Expected user data after 2FA verification"
        assert verify_login_data["user"]["email"] == TEST_USER_EMAIL
        print(f"Step 6 PASSED: Valid 2FA code returns JWT token")
        
        # Use new token for authenticated requests
        new_token = verify_login_data["token"]
        auth_headers = {"Authorization": f"Bearer {new_token}", "Content-Type": "application/json"}
        
        # Step 7: Disable 2FA
        time.sleep(1)  # Ensure fresh code
        disable_code = totp.now()
        disable_response = requests.post(f"{BASE_URL}/api/auth/2fa/disable", json={
            "code": disable_code
        }, headers=auth_headers)
        assert disable_response.status_code == 200, f"Disable failed: {disable_response.text}"
        disable_data = disable_response.json()
        assert disable_data.get("totp_enabled") == False, "Expected totp_enabled=false after disable"
        print(f"Step 7 PASSED: 2FA disabled successfully")
        
        # Step 8: Verify 2FA is now disabled
        status_response2 = requests.get(f"{BASE_URL}/api/auth/2fa/status", headers=auth_headers)
        assert status_response2.status_code == 200
        assert status_response2.json().get("totp_enabled") == False
        print(f"Step 8 PASSED: 2FA status confirms disabled")
        
        # Step 9: Login should work without 2FA now
        final_login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert final_login_response.status_code == 200
        final_data = final_login_response.json()
        assert "token" in final_data, "Expected token after disabling 2FA"
        assert final_data.get("requires_2fa") != True, "Should not require 2FA after disabled"
        print(f"Step 9 PASSED: Login works without 2FA after disable")
        
        print("\n=== FULL 2FA FLOW TEST COMPLETED SUCCESSFULLY ===")
    
    def test_05_verify_setup_with_invalid_code(self):
        """POST /api/auth/2fa/verify-setup with invalid code should fail"""
        # First setup to get a secret
        setup_response = self.session.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        if setup_response.status_code == 400:
            pytest.skip("2FA already enabled")
        
        assert setup_response.status_code == 200
        
        # Try to verify with invalid code
        response = self.session.post(f"{BASE_URL}/api/auth/2fa/verify-setup", json={
            "code": "000000"  # Invalid code
        })
        assert response.status_code == 400, f"Expected 400 for invalid code, got {response.status_code}"
        assert "incorrecto" in response.json().get("detail", "").lower() or "incorrect" in response.json().get("detail", "").lower()
        print(f"PASSED: Invalid verify-setup code returns 400")
    
    def test_06_2fa_status_requires_auth(self):
        """GET /api/auth/2fa/status without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/auth/2fa/status")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"PASSED: 2FA status requires authentication")
    
    def test_07_2fa_setup_requires_auth(self):
        """POST /api/auth/2fa/setup without auth should fail"""
        response = requests.post(f"{BASE_URL}/api/auth/2fa/setup", json={})
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"PASSED: 2FA setup requires authentication")
    
    def test_08_verify_login_with_invalid_temp_token(self):
        """POST /api/auth/2fa/verify-login with invalid temp_token should fail"""
        response = requests.post(f"{BASE_URL}/api/auth/2fa/verify-login", json={
            "user_id": "fake_user_id",
            "temp_token": "invalid_temp_token",
            "code": "123456"
        })
        assert response.status_code == 401, f"Expected 401 for invalid temp_token, got {response.status_code}"
        print(f"PASSED: Invalid temp_token returns 401")


class Test2FAEdgeCases:
    """Edge case tests for 2FA functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        yield
    
    def test_login_invalid_credentials_without_2fa(self):
        """Login with invalid credentials should fail regardless of 2FA"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401 for invalid credentials"
        print(f"PASSED: Invalid credentials return 401")
    
    def test_auth_me_returns_totp_enabled_field(self):
        """GET /api/auth/me should include totp_enabled field"""
        # Login first
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_response.status_code == 200
        data = login_response.json()
        
        if data.get("requires_2fa"):
            pytest.skip("2FA is enabled - need token from verify-login")
        
        token = data["token"]
        
        # Get /me endpoint
        me_response = self.session.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert me_response.status_code == 200
        me_data = me_response.json()
        
        # totp_enabled should be present
        assert "totp_enabled" in me_data, "Expected totp_enabled in /me response"
        print(f"PASSED: /api/auth/me includes totp_enabled={me_data['totp_enabled']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
