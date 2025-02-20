"""
Test cases for SecurityMiddleware
"""

import os

from cryptography.fernet import Fernet
from django.http import HttpResponse, HttpResponseForbidden
from django.test import RequestFactory, TestCase

from app.middleware.security_middleware import SecurityMiddleware


class TestSecurityMiddleware(TestCase):
    """Test cases for SecurityMiddleware"""

    def setUp(self):
        """Set up test environment"""
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(get_response=lambda x: HttpResponse())
        test_key = Fernet.generate_key()
        os.environ["PATTERN_ENCRYPTION_KEY"] = test_key.decode()

    def test_clean_request(self):
        """Test that normal requests pass through"""
        request = self.factory.get("/api/domain/domains")
        response = self.middleware.process_request(request)
        self.assertIsNone(response)

    def test_malicious_request(self):
        """Test that requests with malicious content are blocked"""
        request = self.factory.get("/api/domain/domains?query=select * from users")
        response = self.middleware.process_request(request)
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_null_byte(self):
        """Test that requests with null bytes are blocked"""
        null_byte_tests = [
            (r"%00", "URL encoded null byte"),
            (r"\x00", "Escaped hex null byte"),
            (r"\u0000", "Escaped unicode null byte"),
            ("\x00", "Raw null byte"),
            ("\u0000", "Unicode null byte"),
        ]

        for test_byte, description in null_byte_tests:
            request = self.factory.get(f"/api/domain/domains?query={test_byte}")
            response = self.middleware.process_request(request)
            self.assertIsInstance(
                response,
                HttpResponseForbidden,
                f"Failed to block {description}: {test_byte!r}",
            )
