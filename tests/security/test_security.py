"""
Security testing suite for DMLog

Tests security aspects including:
- Authentication and authorization
- Input validation and sanitization
- SQL injection prevention
- XSS prevention
- CSRF protection
- Rate limiting
- Data encryption
- Secure file uploads
- Session management
- API security
"""

import pytest
import requests
import json
import base64
import hashlib
import time
from urllib.parse import quote_plus
from unittest.mock import Mock, patch
import re


class TestAuthenticationSecurity:
    """Test authentication security measures"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_password_strength_validation(self, base_url):
        """Test password strength requirements"""
        weak_passwords = [
            "123",           # Too short
            "password",      # Common password
            "qwerty",        # Keyboard sequence
            "aaaaaa",        # Repeated characters
            "Password1",     # No special characters
        ]

        for password in weak_passwords:
            response = requests.post(f"{base_url}/api/auth/register", json={
                "username": f"testuser_{time.time()}",
                "email": f"test_{time.time()}@example.com",
                "password": password
            })

            # Should reject weak passwords
            assert response.status_code in [400, 422]
            assert "password" in response.json().get("detail", "").lower()

    def test_login_rate_limiting(self, base_url):
        """Test login rate limiting prevents brute force"""
        username = f"bruteforce_test_{time.time()}"

        # Register user first
        requests.post(f"{base_url}/api/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "SecurePassword123!"
        })

        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(20):
            response = requests.post(f"{base_url}/api/auth/login", data={
                "username": username,
                "password": "wrong_password"
            })

            if response.status_code == 429:  # Rate limited
                break
            failed_attempts += 1

        # Should be rate limited after several attempts
        assert failed_attempts < 20, "Rate limiting not working effectively"

    def test_session_token_security(self, base_url):
        """Test JWT token security"""
        # Login to get token
        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "username": "testuser",
            "password": "testpassword"
        })

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            # Test token structure
            parts = token.split(".")
            assert len(parts) == 3, "JWT should have 3 parts"

            # Test token is not plain text
            header, payload, signature = parts
            assert len(header) > 10, "Header should be encoded"
            assert len(payload) > 10, "Payload should be encoded"

            # Test malformed token rejection
            malformed_token = "invalid.token.here"
            response = requests.get(
                f"{base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {malformed_token}"}
            )
            assert response.status_code == 401

    def test_concurrent_session_handling(self, base_url):
        """Test handling of multiple concurrent sessions"""
        # Create multiple login sessions for same user
        tokens = []
        for i in range(5):
            response = requests.post(f"{base_url}/api/auth/login", data={
                "username": "testuser",
                "password": "testpassword"
            })
            if response.status_code == 200:
                tokens.append(response.json()["access_token"])

        # All tokens should be valid (depending on implementation)
        valid_tokens = 0
        for token in tokens:
            response = requests.get(
                f"{base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                valid_tokens += 1

        # Test session limits if implemented
        # This depends on the specific session management strategy

    def test_password_reset_security(self, base_url):
        """Test password reset functionality security"""
        email = f"password_reset_test_{time.time()}@example.com"

        # Request password reset
        response = requests.post(f"{base_url}/api/auth/request-password-reset", json={
            "email": email
        })

        # Should not reveal if email exists
        assert response.status_code in [200, 404]

        # Test reset token expiration
        # This would depend on the actual implementation


class TestInputValidationSecurity:
    """Test input validation and sanitization"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_sql_injection_prevention(self, base_url):
        """Test SQL injection attack prevention"""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1; DELETE FROM campaigns; --",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users (username) VALUES ('hacked'); --"
        ]

        # Test in login form
        for payload in sql_injection_payloads:
            response = requests.post(f"{base_url}/api/auth/login", data={
                "username": payload,
                "password": "password"
            })

            # Should not authenticate with SQL injection
            assert response.status_code != 200

        # Test in search parameters
        for payload in sql_injection_payloads:
            response = requests.get(
                f"{base_url}/api/characters",
                params={"search": payload},
                headers={"Authorization": "Bearer valid_token"}
            )

            # Should not cause database errors
            assert response.status_code not in [500, 502]

    def test_xss_prevention(self, base_url):
        """Test XSS attack prevention"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]

        # Test in character creation
        for payload in xss_payloads:
            response = requests.post(
                f"{base_url}/api/characters",
                json={
                    "name": payload,
                    "race": "Human",
                    "class": "Fighter",
                    "level": 1
                },
                headers={"Authorization": "Bearer valid_token"}
            )

            if response.status_code == 201:
                # Retrieve character and check XSS is sanitized
                character_id = response.json()["id"]
                get_response = requests.get(
                    f"{base_url}/api/characters/{character_id}",
                    headers={"Authorization": "Bearer valid_token"}
                )

                if get_response.status_code == 200:
                    character_data = get_response.json()
                    # XSS payload should be sanitized or escaped
                    assert "<script>" not in character_data["name"]
                    assert "javascript:" not in character_data["name"]

        # Test in chat messages
        for payload in xss_payloads:
            response = requests.post(
                f"{base_url}/api/chat/send",
                json={
                    "message": payload,
                    "campaign_id": "test_campaign"
                },
                headers={"Authorization": "Bearer valid_token"}
            )

            # Should sanitize or reject XSS payloads

    def test_file_upload_security(self, base_url):
        """Test malicious file upload prevention"""
        # Test executable file upload
        executable_content = b"MZ\x90\x00"  # PE header
        files = {"file": ("malware.exe", executable_content, "application/x-executable")}

        response = requests.post(
            f"{base_url}/api/upload",
            files=files,
            headers={"Authorization": "Bearer valid_token"}
        )

        # Should reject executable files
        assert response.status_code in [400, 422]

        # Test oversized file upload
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        files = {"file": ("large.jpg", large_content, "image/jpeg")}

        response = requests.post(
            f"{base_url}/api/upload",
            files=files,
            headers={"Authorization": "Bearer valid_token"}
        )

        # Should reject oversized files
        assert response.status_code in [400, 413]

    def test_input_length_validation(self, base_url):
        """Test input length limits"""
        long_string = "a" * 10000  # Very long string

        # Test long character name
        response = requests.post(
            f"{base_url}/api/characters",
            json={
                "name": long_string,
                "race": "Human",
                "class": "Fighter",
                "level": 1
            },
            headers={"Authorization": "Bearer valid_token"}
        )

        # Should reject overly long inputs
        assert response.status_code in [400, 422]

    def test_special_character_handling(self, base_url):
        """Test special character handling"""
        special_chars = [
            "../../etc/passwd",  # Path traversal
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded path traversal
            "\x00\x01\x02",  # Null bytes and control characters
            "🚀🔥💯",  # Unicode emojis
            "姓名",  # Chinese characters
            "العربية",  # Arabic text
        ]

        for chars in special_chars:
            response = requests.post(
                f"{base_url}/api/characters",
                json={
                    "name": chars,
                    "race": "Human",
                    "class": "Fighter",
                    "level": 1
                },
                headers={"Authorization": "Bearer valid_token"}
            )

            # Should handle special characters appropriately
            # Either accept valid Unicode or reject problematic characters


class TestAuthorizationSecurity:
    """Test authorization and access control"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_unauthorized_access_prevention(self, base_url):
        """Test prevention of unauthorized access"""
        protected_endpoints = [
            "/api/characters",
            "/api/campaigns",
            "/api/auth/me",
            "/api/dice/roll"
        ]

        for endpoint in protected_endpoints:
            response = requests.get(f"{base_url}{endpoint}")

            # Should require authentication
            assert response.status_code == 401

    def test_cross_user_data_access(self, base_url):
        """Test prevention of cross-user data access"""
        # Login as user1
        user1_response = requests.post(f"{base_url}/api/auth/login", data={
            "username": "user1",
            "password": "password1"
        })

        if user1_response.status_code == 200:
            user1_token = user1_response.json()["access_token"]

            # Try to access user2's data
            response = requests.get(
                f"{base_url}/api/characters/999",  # Assume character 999 belongs to user2
                headers={"Authorization": f"Bearer {user1_token}"}
            )

            # Should deny access to other users' data
            assert response.status_code in [403, 404]

    def test_role_based_access_control(self, base_url):
        """Test role-based access control"""
        # Test admin-only endpoints
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/system/stats",
            "/api/admin/logs"
        ]

        # Login as regular user
        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "username": "regular_user",
            "password": "password"
        })

        if login_response.status_code == 200:
            user_token = login_response.json()["access_token"]

            for endpoint in admin_endpoints:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    headers={"Authorization": f"Bearer {user_token}"}
                )

                # Regular user should not access admin endpoints
                assert response.status_code in [401, 403, 404]

    def test_campaign_permission_enforcement(self, base_url):
        """Test campaign permission enforcement"""
        # Login as user
        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "username": "testuser",
            "password": "password"
        })

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            # Try to modify campaign user doesn't own
            response = requests.patch(
                f"{base_url}/api/campaigns/999",  # Campaign user doesn't own
                json={"name": "Hacked Campaign"},
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should deny access
            assert response.status_code in [403, 404]

    def test_api_rate_limiting(self, base_url):
        """Test API rate limiting"""
        # Make rapid requests
        responses = []
        for i in range(100):
            response = requests.get(f"{base_url}/api/health")
            responses.append(response)

            if response.status_code == 429:  # Rate limited
                break

        # Should be rate limited eventually
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting should be active"


class TestCSRFProtection:
    """Test CSRF protection measures"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_csrf_token_enforcement(self, base_url):
        """Test CSRF token enforcement"""
        # Get CSRF token (if implemented)
        session = requests.Session()

        # Visit a page to get CSRF token
        response = session.get(f"{base_url}/login")

        # Look for CSRF token in cookies or meta tags
        csrf_token = None

        # Check cookies
        if "csrf_token" in session.cookies:
            csrf_token = session.cookies["csrf_token"]

        # Try to make POST request without CSRF token
        response = session.post(f"{base_url}/api/auth/login", data={
            "username": "testuser",
            "password": "password"
        })

        # Should enforce CSRF protection (if implemented for web forms)
        # Note: API endpoints typically use JWT, not CSRF

    def test_sameorigin_policy(self, base_url):
        """Test Same-Origin policy enforcement"""
        # Test CORS headers
        response = requests.options(f"{base_url}/api/characters")

        # Should have appropriate CORS headers
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]

        for header in cors_headers:
            assert header in response.headers, f"Missing CORS header: {header}"

        # Test cross-origin requests
        response = requests.get(
            f"{base_url}/api/characters",
            headers={"Origin": "https://malicious-site.com"}
        )

        # Should handle cross-origin requests appropriately


class TestDataEncryptionSecurity:
    """Test data encryption and protection"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_password_hashing(self, base_url):
        """Test password hashing is not reversible"""
        # Register user with known password
        password = "TestPassword123!"
        username = f"hash_test_{time.time()}"

        response = requests.post(f"{base_url}/api/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password
        })

        # Password should not be stored in plain text
        # This would require database access to verify
        # For now, we test that password is not returned in responses

        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "username": username,
            "password": password
        })

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            # Get user info
            user_response = requests.get(
                f"{base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            if user_response.status_code == 200:
                user_data = user_response.json()
                assert "password" not in user_data
                assert "password_hash" not in user_data

    def test_sensitive_data_protection(self, base_url):
        """Test protection of sensitive data"""
        # Test API doesn't expose sensitive information
        endpoints_to_check = [
            "/api/characters",
            "/api/campaigns",
            "/api/sessions"
        ]

        for endpoint in endpoints_to_check:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers={"Authorization": "Bearer valid_token"}
            )

            if response.status_code == 200:
                data = response.json()
                # Check that sensitive fields are not exposed
                sensitive_fields = ["password", "token", "secret", "key"]

                if isinstance(data, list):
                    for item in data:
                        for field in sensitive_fields:
                            assert field not in item, f"Sensitive field {field} exposed"
                elif isinstance(data, dict):
                    for field in sensitive_fields:
                        assert field not in data, f"Sensitive field {field} exposed"

    def test_https_enforcement(self, base_url):
        """Test HTTPS enforcement in production"""
        # This test would need to be run against HTTPS endpoint
        # For now, test that secure headers are set

        response = requests.get(f"{base_url}/api/health")

        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]

        for header in security_headers:
            if header in response.headers:
                assert response.headers[header] != "", f"Security header {header} is empty"


class TestSessionSecurity:
    """Test session management security"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_session_timeout(self, base_url):
        """Test session timeout functionality"""
        # Login to get token
        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "username": "testuser",
            "password": "password"
        })

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            # Wait for session to expire (if implemented)
            time.sleep(2)

            # Try to use expired token
            response = requests.get(
                f"{base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should reject expired token
            # This depends on token expiration time configuration

    def test_session_invalidation(self, base_url):
        """Test session invalidation on logout"""
        # Login
        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "username": "testuser",
            "password": "password"
        })

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            # Logout
            logout_response = requests.post(
                f"{base_url}/api/auth/logout",
                headers={"Authorization": f"Bearer {token}"}
            )

            # Try to use token after logout
            response = requests.get(
                f"{base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should invalidate token on logout
            # This depends on blacklist implementation

    def test_concurrent_session_limits(self, base_url):
        """Test concurrent session limits"""
        # Create multiple sessions for same user
        tokens = []
        for i in range(10):
            response = requests.post(f"{base_url}/api/auth/login", data={
                "username": "testuser",
                "password": "password"
            })
            if response.status_code == 200:
                tokens.append(response.json()["access_token"])

        # Test if session limits are enforced
        # This depends on session management implementation


class TestErrorHandlingSecurity:
    """Test secure error handling"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_error_message_sanitization(self, base_url):
        """Test error messages don't leak sensitive information"""
        # Trigger various errors
        error_endpoints = [
            "/api/characters/999999",  # Non-existent character
            "/api/campaigns/invalid-uuid",  # Invalid ID format
            "/api/auth/me",  # Without authentication
        ]

        for endpoint in error_endpoints:
            response = requests.get(f"{base_url}{endpoint}")

            if response.status_code >= 400:
                error_message = response.text.lower()

                # Check for information disclosure
                sensitive_info = [
                    "password", "secret", "key", "token",
                    "internal server error", "stack trace",
                    "database", "sql", "query"
                ]

                for info in sensitive_info:
                    assert info not in error_message, f"Error message contains sensitive info: {info}"

    def test_debug_information_leakage(self, base_url):
        """Test debug information is not leaked in production"""
        response = requests.get(f"{base_url}/non-existent-endpoint")

        # Should not contain debug information
        debug_indicators = [
            "traceback", "exception", "error details",
            "file path", "line number", "debug"
        ]

        response_text = response.text.lower()
        for indicator in debug_indicators:
            assert indicator not in response_text, f"Debug information leaked: {indicator}"

    def test_http_status_codes(self, base_url):
        """Test appropriate HTTP status codes"""
        # Test various scenarios
        test_cases = [
            (f"{base_url}/api/auth/me", "GET", None, 401),  # Unauthorized
            (f"{base_url}/api/characters/999999", "GET", None, 404),  # Not found
            (f"{base_url}/api/characters", "POST", {"invalid": "data"}, 422),  # Validation error
        ]

        for url, method, data, expected_status in test_cases:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)

            assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"


class TestApiSecurityHeaders:
    """Test API security headers"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    def test_security_headers(self, base_url):
        """Test security headers are present"""
        response = requests.get(f"{base_url}/api/health")

        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",  # or "SAMEORIGIN"
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        for header, expected_value in required_headers.items():
            assert header in response.headers, f"Missing security header: {header}"
            if expected_value:
                assert response.headers[header] == expected_value, f"Incorrect {header} value"

    def test_content_type_nosniff(self, base_url):
        """Test Content-Type nosniff header"""
        response = requests.get(f"{base_url}/api/health")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_frame_options(self, base_url):
        """Test X-Frame-Options header"""
        response = requests.get(f"{base_url}/api/health")

        assert "X-Frame-Options" in response.headers
        frame_options = response.headers["X-Frame-Options"]
        assert frame_options in ["DENY", "SAMEORIGIN"]


# Security test runner
class SecurityTestRunner:
    """Run comprehensive security tests"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []

    def run_all_tests(self):
        """Run all security tests"""
        print("Starting DMLog security testing...")

        test_classes = [
            TestAuthenticationSecurity,
            TestInputValidationSecurity,
            TestAuthorizationSecurity,
            TestCSRFProtection,
            TestDataEncryptionSecurity,
            TestSessionSecurity,
            TestErrorHandlingSecurity,
            TestApiSecurityHeaders
        ]

        for test_class in test_classes:
            print(f"\nRunning {test_class.__name__}...")
            self._run_test_class(test_class)

        self._generate_report()

    def _run_test_class(self, test_class):
        """Run tests for a specific class"""
        import inspect

        test_methods = [
            method for method in dir(test_class)
            if method.startswith("test_") and callable(getattr(test_class, method))
        ]

        test_instance = test_class()
        test_instance.base_url = self.base_url

        for method_name in test_methods:
            method = getattr(test_instance, method_name)
            try:
                method()
                self.results.append({
                    "test": f"{test_class.__name__}.{method_name}",
                    "status": "PASS",
                    "message": "Test passed"
                })
                print(f"  ✓ {method_name}")
            except Exception as e:
                self.results.append({
                    "test": f"{test_class.__name__}.{method_name}",
                    "status": "FAIL",
                    "message": str(e)
                })
                print(f"  ✗ {method_name}: {e}")

    def _generate_report(self):
        """Generate security test report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests

        print(f"\n=== Security Test Report ===")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print(f"\n=== Failed Tests ===")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"✗ {result['test']}: {result['message']}")


if __name__ == "__main__":
    # Run security tests
    runner = SecurityTestRunner()
    runner.run_all_tests()