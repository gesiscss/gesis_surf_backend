"""
Security Loader
"""

import json
import logging
import os

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


# pylint: disable=R0903
class SecurePatternLoader:
    """Loads encrypted security patterns from secure storage"""

    def __init__(self) -> None:
        """Initializes the SecurePatternLoader"""
        self.key = os.environ.get("PATTERN_ENCRYPTION_KEY")
        if not self.key:
            logger.warning("No encryption key found, using default pattenrs")
            self.fernet = None
        else:
            self.fernet = Fernet(self.key.encode())

    def load_patterns(self) -> list[dict]:
        """Loads the security patterns"""
        pattern_file = os.environ.get("PATTERN_FILE")

        if not pattern_file or not self.fernet:
            return self._get_default_patterns()

        try:
            with open(pattern_file, "rb") as f_file:
                encrypted_patterns = f_file.read()
            decrypted_patterns = self.fernet.decrypt(encrypted_patterns)
            return json.loads(decrypted_patterns)
        except Exception as error:  # pylint: disable=broad-except
            logger.error("Error loading patterns: %s", error)
            return self._get_default_patterns()

    def _get_default_patterns(self) -> list[dict]:
        """Returns the default patterns"""
        return [
            {"name": "SQL Injection", "pattern": r"select.*from.*", "severity": 3},
            {"name": "XSS", "pattern": r"<script>.*</script>", "severity": 3},
            {"name": "CSRF", "pattern": r"csrfmiddlewaretoken", "severity": 2},
            {
                "name": "basic Injection",
                "pattern": r"(?i)(select|union|drop|exec)\s+",
                "severity": 3,
            },
        ]
