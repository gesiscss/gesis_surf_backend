"""
Middleware that logs all requests and responses to the application.
"""

import logging

from core.models import User
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger: logging.Logger = logging.getLogger("app.middleware")


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs all requests and responses to the application.
    """

    def process_request(self, request: HttpRequest) -> None:
        """
        Logs all requests to the application and the user that made the request.
        """
        method: str = request.method
        authorization: str = request.headers.get("Authorization")
        referer: str = request.headers.get("Referer")
        user_agent: str = request.headers.get("User-Agent")

        # Extract uuid from incoming request
        if authorization:
            token = authorization.split(" ")[1]
            user = User.objects.get(auth_token=token)
            user_detail = f"UUID: {user.id}"
        else:
            user_detail = "Anonymous"

        logger.info(
            "Request by User_detail: %s, Method: %s, Path: %s, Referer: %s, User_Agent: %s",
            user_detail,
            method,
            request.path,
            referer,
            user_agent,
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
        user: str = getattr(request, "user", None)
        user_detail: str = (
            f"(ID: {user.id})" if user and user.is_authenticated else "Anonymous"
        )
        path: str = request.path

        logger.info(
            "Response User: %s, status: %s, Request_path: %s",
            user_detail,
            response.status_code,
            path,
        )

        if response.status_code >= 400:
            logger.error(
                "Response Error User: %s, status: %s, Request_path: %s",
                user_detail,
                response.status_code,
                path,
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
