"""
Middleware that logs all requests and responses to the application.
"""

import logging
import time

from core.models import User
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger: logging.Logger = logging.getLogger("app.middleware")


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs all requests and responses to the application with:
    - 2xx/3xx status codes are logged as info
    - 4xx status codes are logged as warning
    - 5xx status codes are logged as error
    """

    def _get_user_detail_from_request(self, request: HttpRequest) -> str:
        """
        Extracts the user detail from the request object.

        Args:
            request (HttpRequest): The request object.

        Returns:
            str: The user detail.
        """
        authorization: str | None = request.headers.get("Authorization")

        if not authorization:
            return "Anonymous"

        try:
            token = authorization.split(" ")[1]
            user = User.objects.get(auth_token=token)
            return f"UUID: {user.id}"
        except (User.DoesNotExist, IndexError, ValueError):
            logger.warning("Auth Error: %s", authorization)
            return "Anonymous (Invalid Token)"

    def process_request(self, request: HttpRequest) -> None:
        """
        Logs all requests to the application and the user that made the request.
        """
        request._start_time = time.time()  # pylint: disable=protected-access

        method: str = request.method
        referer: str = request.headers.get("Referer", "")
        user_agent: str = request.headers.get("User-Agent", "")
        user_detail = self._get_user_detail_from_request(request)

        logger.info(
            "Request by User_detail: %s, Method: %s, Path: %s, Referer: %s, User_Agent: %s",
            user_detail,
            method,
            request.path,
            referer,
            user_agent,
        )

    def _get_user_detail_from_response(self, request: HttpRequest) -> str:
        """
        Extracts the user detail from the response object.

        Args:
            request (HttpRequest): The request object.

        Returns:
            str: The user detail.
        """
        user: str = getattr(request, "user", None)
        return (
            f"{user.user_id} (ID: {user.id})"
            if user and user.is_authenticated
            else "Anonymous"
        )

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Logs all responses to the application and the user that made the request.

        Args:
            request (HttpRequest): The request object.
            response (HttpResponse): The response object.

        Returns:
            HttpResponse: The response object.
        """
        duration: float = (
            time.time() - request._start_time  # pylint: disable=protected-access
        )

        user: str = self._get_user_detail_from_response(request)
        user_detail: str = (
            f"(ID: {user.id})" if user and user.is_authenticated else "Anonymous"
        )

        path: str = request.path

        logger.info(
            "Response User: %s, status: %s, Request_path: %s, Duration: %s",
            user_detail,
            response.status_code,
            path,
            duration,
        )

        if 400 <= response.status_code < 500:
            logger.warning(
                "Response User: %s, status: %s, Request_path: %s, Duration: %s",
                user_detail,
                response.status_code,
                path,
                duration,
            )
        elif 500 <= response.status_code:
            logger.error(
                "Response User: %s, status: %s, Request_path: %s, Duration: %s",
                user_detail,
                response.status_code,
                path,
                duration,
            )

        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """
        Args:
            request (_type_): The request object.
            exception (_type_): The exception object.
        """
        user: str = getattr(request, "user", None)
        user_detail: str = (
            f"{user.user_id} (ID: {user.id})"
            if user and user.is_authenticated
            else "Anonymous"
        )

        logger.error(
            "Exception %s encountered at %s by %s",
            exception,
            request.path,
            user_detail,
        )
