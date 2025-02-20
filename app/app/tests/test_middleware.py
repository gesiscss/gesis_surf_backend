"""
Middleware tests
"""

from unittest.mock import MagicMock, patch

from core.models import User
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from rest_framework.authtoken.models import Token

from app.middleware.traffic_middleware import LoggingMiddleware


def request_headers(token: str) -> dict:
    """
    Return request headers
    """
    return {
        "Authorization": f"Token {token}",
        "User-Agent": "test-agent",
        "Origin": "test-origin",
        "Referer": "test-referer",
    }


class TestLoggingMiddleware(TestCase):
    """
    Test Logging Middleware
    """

    def setUp(self):
        """
        Setup the test
        """
        self.factory = RequestFactory()
        self.middleware = LoggingMiddleware(get_response=lambda x: x)
        self.user = User.objects.create_user("test_user", "test_password")
        self.token = Token.objects.create(user=self.user)
        self.user.save()

    def test_get_user_detail_anonymous(self) -> None:
        """
        Test get user detail with anonymous user
        """
        detail = self.middleware._get_user_detail(  # pylint: disable=protected-access
            AnonymousUser()
        )
        self.assertEqual(detail, "Anonymous")

    def test_get_user_detail_with_auth_header(self) -> None:
        """
        Test get user detail with auth header
        """
        auth_header = f"token {self.user.auth_token}"
        detail = self.middleware._get_user_detail(  # pylint: disable=protected-access
            auth_header=auth_header
        )
        self.assertEqual(detail, f"UUID: {self.user.id}")

    @patch("logging.Logger.info")
    def test_process_request(self, mock_logger: MagicMock) -> None:
        """
        Test process request
        """
        request = self.factory.get("/test-path")
        request.headers = request_headers(self.token.key)
        self.middleware.process_request(request)
        mock_logger.assert_called_once()
        self.assertTrue(hasattr(request, "_start_time"))

    @patch("logging.Logger.warning")
    def test_process_response_4xx(self, mock_logger: MagicMock) -> None:
        """
        Test process response with 4xx status code
        """
        request = self.factory.get("/test-path")
        request.headers = request_headers(self.token.key)
        response = HttpResponse(status=404)
        self.middleware.process_request(request)
        self.middleware.process_response(request, response)
        mock_logger.assert_called_once()

    @patch("logging.Logger.error")
    def test_process_response_5xx(self, mock_logger: MagicMock) -> None:
        """
        Test process response with 5xx status code
        """
        request = self.factory.get("/test-path")
        request.headers = request_headers(self.token.key)
        response = HttpResponse(status=500)
        self.middleware.process_request(request)
        self.middleware.process_response(request, response)
        mock_logger.assert_called_once()

    def test_get_user_detail_with_invalid_token(self) -> None:
        """
        Test get user detail with invalid token
        """
        auth_header = "invalid token"
        detail = self.middleware._get_user_detail(  # pylint: disable=protected-access
            auth_header=auth_header
        )
        self.assertEqual(detail, "Anonymous (Invalid Token)")

    def test_get_user_detail_invalid_format(self) -> None:
        """
        Test get user detail with invalid format
        """
        auth_header = "Bearer invalid_token"
        detail = self.middleware._get_user_detail(  # pylint: disable=protected-access
            auth_header=auth_header
        )
        self.assertEqual(detail, "Anonymous (Invalid Token)")
