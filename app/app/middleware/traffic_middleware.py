"""
Middleware that logs all requests and responses to the application.
"""

import dataclasses
import logging
import time
from typing import Any

from core.models import User
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger: logging.Logger = logging.getLogger("app.middleware")

# Constants for logging messages
REQUEST_LOG_MSG = (
    "Request by %(user_detail)s, Method: %(method)s, Path: %(path)s, "
    "Referer: %(referer)s, User-Agent: %(user_agent)s, Origin: %(origin)s"
)
RESPONSE_LOG_MSG = (
    "Response User: %(user_detail)s, status: %(status)s, "
    "Request_path: %(path)s, Duration: %(duration).3fs"
)
EXCEPTION_LOG_MSG = "Exception %(exception)s encountered at %(path)s by %(user_detail)s"


@dataclasses.dataclass
class RequestLogData:
    """Structure for request logging data."""

    user_detail: str
    method: str
    path: str
    referer: str
    user_agent: str
    origin: str


@dataclasses.dataclass
class ResponseLogData:
    """Structure for response logging data."""

    user_detail: str
    status: int
    path: str
    duration: float


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs all requests and responses to the application with:
    - 2xx/3xx status codes are logged as info
    - 4xx status codes are logged as warning
    - 5xx status codes are logged as error
    """

    def _get_user_detail(
        self, user: Any | None = None, auth_header: str | None = None
    ) -> str:
        """
        Extracts the user detail from either a user object or auth header.

        Args:
            user: The user object from request.user
            auth_header: The Authorization header value

        Returns:
            str: The user detail string
        """
        if auth_header:
            try:
                scheme, token = auth_header.split(" ", 1)
                if scheme.lower() != "token":
                    raise ValueError("Invalid Authorization header format")

                user = User.objects.get(auth_token=token)
                return f"UUID: {user.id}"
            except (User.DoesNotExist, ValueError) as auth_error:
                logger.warning("Auth Error: %s - %s", auth_header, str(auth_error))
                return "Anonymous (Invalid Token)"
            except (AttributeError, TypeError) as validation_error:
                # Handle specific validation errors
                logger.error("Auth validation error: %s", str(validation_error))
                return "Anonymous (Validation Error)"

        if isinstance(user, str):
            logger.warning("User is a string: %s", user)
            return "Anonymous"

        if (
            isinstance(user, AnonymousUser)
            or not user
            or not getattr(user, "is_authenticated", False)
        ):
            return "Anonymous"

        return f"UUID: {user.id}"

    def process_request(self, request: HttpRequest) -> None:
        """
        Logs all requests to the application and the user that made the request.
        """
        # pylint: disable=protected-access
        # Using _start_time is the intended way to store timing data in Django middleware
        request._start_time = time.perf_counter()

        log_data = RequestLogData(
            user_detail=self._get_user_detail(
                auth_header=request.headers.get("Authorization")
            ),
            method=request.method,
            path=request.path,
            referer=request.headers.get("Referer", ""),
            user_agent=request.headers.get("User-Agent", ""),
            origin=request.headers.get("Origin", ""),
        )

        logger.info(REQUEST_LOG_MSG, dataclasses.asdict(log_data))

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """
        Logs all responses to the application with appropriate log levels based on status code.

        Args:
            request: The request object.
            response: The response object.

        Returns:
            HttpResponse: The response object.
        """
        try:
            # pylint: disable=protected-access
            # Using _start_time is the intended way to access timing data in Django middleware
            duration = time.perf_counter() - request._start_time
        except AttributeError:
            logger.warning("Request start time not found")
            duration = 0.0

        log_data = ResponseLogData(
            user_detail=self._get_user_detail(user=getattr(request, "user", None)),
            status=response.status_code,
            path=request.path,
            duration=duration,
        )
        log_dict = dataclasses.asdict(log_data)

        if response.status_code >= 500:
            logger.error(RESPONSE_LOG_MSG, log_dict)
        elif response.status_code >= 400:
            logger.warning(RESPONSE_LOG_MSG, log_dict)
        else:
            logger.info(RESPONSE_LOG_MSG, log_dict)

        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """
        Logs exceptions that occur during request processing.

        Args:
            request: The request object.
            exception: The exception object.
        """
        user_detail = self._get_user_detail(user=getattr(request, "user", None))

        logger.error(
            EXCEPTION_LOG_MSG,
            {
                "exception": str(exception),
                "path": request.path,
                "user_detail": user_detail,
            },
            exc_info=True,
        )
