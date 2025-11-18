"""
Security middleware for detecting and blocking security violations.
"""

import logging
import re
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

from app.security.pattern_loader import SecurePatternLoader

logger = logging.getLogger(__name__)


# pylint: disable=R0903
class SecurityMiddleware(MiddlewareMixin):
    """SecurityMiddleware

    Args:
        MiddlewareMixin (_type_): _description_
    """

    def __init__(self, get_response: Callable | None = None) -> None:
        """_summary_

        Args:
            get_response (Callable | None, optional): _description_. Defaults to None.
        """
        super().__init__(get_response)
        self.secure_pattern_loader = SecurePatternLoader()
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """_summary_"""
        patterns = self.secure_pattern_loader.load_patterns()
        self.compiled_patterns = [
            (p["name"], re.compile(p["pattern"]), p["severity"]) for p in patterns
        ]

    def process_request(self, request: HttpRequest) -> HttpResponse | None:
        """_summary_

        Args:
            request (HttpRequest): _description_

        Returns:
            HttpResponse | None: _description_
        """
        check_data = self._get_request_data(request)

        for data in check_data:
            match = self._check_patterns(data)
            if match:
                self._log_violation(request, match)
                return HttpResponseForbidden("Security violation detected")
        return None

    def _get_request_data(self, request: HttpRequest) -> list[str]:
        """_summary_

        Args:
            request (HttpRequest): _description_

        Returns:
            list[str]: _description_
        """
        data = [
            request.path,
            request.GET.urlencode(),
            str(request.headers),
        ]

        if request.method == "POST":
            try:
                data.append(request.POST.copy().urlencode())
            except Exception as error:  # pylint: disable=broad-except
                logger.error("Error getting POST data: %s", error)
        return data

    def _check_patterns(self, data: str) -> tuple | None:
        """_summary_

        Args:
            data (str): _description_

        Returns:
            Optional[tuple]: _description_
        """
        for name, pattern, severity in self.compiled_patterns:
            if pattern.search(data):
                return (name, severity)
        return None

    def _log_violation(self, request: HttpRequest, match: tuple) -> None:
        """_summary_

        Args:
            request (HttpRequest): _description_
            match (tuple): _description_
        """
        name, severity = match
        logger.warning(
            "Security violation detected: %s, %s, %s",
            name,
            severity,
            request.META.get("REMOTE_ADDR"),
        )
