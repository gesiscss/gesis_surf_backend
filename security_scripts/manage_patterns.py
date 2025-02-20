"""
Manage security patterns for web application security middleware.
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = os.getenv("SECURITY_BASE_DIR", "/opt/web_tracker")
SECURE_DIR = Path(BASE_DIR) / "secure"
PATTERN_FILE = SECURE_DIR / "patterns.enc"


def generate_key() -> bytes:
    """Generate new encryption key"""
    return Fernet.generate_key()


def encrypt_patterns(patterns: list[dict], key: bytes) -> bytes:
    """
    Encrypt patterns for secure storage

    Args:
        patterns: List of pattern dictionaries
        key: Encryption key

    Returns:
        Encrypted patterns as bytes

    Raises:
        InvalidToken: If encryption key is invalid
    """
    try:
        f_encrypt = Fernet(key)
        return f_encrypt.encrypt(json.dumps(patterns).encode())
    except InvalidToken:
        logger.error("Invalid encryption key format")
        raise
    except Exception as err:
        logger.error("Encrypted failed: %s", str(err))
        raise


def validate_patterns(patterns: list[dict]) -> bool:
    """
    Validate pattern structure and regex syntax

    Args:
        patterns: List of pattern dictionaries

    Returns:
        bool: True if patterns are valid
    """
    try:
        for pattern in patterns:
            if not all(k in pattern for k in ["name", "pattern", "severity"]):
                logger.error("Invalid pattern structure: %s", pattern)
                return False
            # Validate severity range
            if (
                not isinstance(pattern["severity"], int)
                or not 1 <= pattern["severity"] <= 3
            ):
                logger.error("Invalid severity level: %s", pattern["severity"])
                return False
            # Test regex compilation
            re.compile(pattern["pattern"])
        return True
    except re.error as err:
        logger.error("Invalid regex pattern: %s", str(err))
        return False


def main() -> None:
    """Main entry point for pattern management"""
    parser = argparse.ArgumentParser(description="Manage security patterns")
    parser.add_argument(
        "--generate-key", action="store_true", help="Generate new encryption key"
    )
    parser.add_argument(
        "--update-patterns", action="store_true", help="Update security patterns"
    )
    args = parser.parse_args()

    try:
        # Create secure directory with proper permissions
        SECURE_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(SECURE_DIR, 0o700)  # Secure directory permissions

        if args.generate_key:
            key = generate_key()
            logger.info("New encryption key generated: %s", key.decode())
            return

        if args.update_patterns:
            key = os.getenv("PATTERN_ENCRYPTION_KEY")
            if not key:
                logger.error("Error: PATTERN_ENCRYPTION_KEY not set")
                return

            patterns = [
                {
                    "name": "SQL_Injection",
                    "pattern": r"(?i)(select|union|drop|exec)\s+",
                    "severity": 3,
                },
                {
                    "name": "XSS",
                    "pattern": r"(?i)(<script|javascript:|on\w+\s*=)",
                    "severity": 3,
                },
                {
                    "name": "Path_Traversal",
                    "pattern": r"(?i)(\.\.\/|\.\.\%2f|\.\.\%5c)",
                    "severity": 3,
                },
                {
                    "name": "Null_Byte",
                    "pattern": r"(?:\\x00|%00|\\u0000){2,}",
                    "severity": 3,
                },
                {
                    "name": "Command_Injection",
                    "pattern": r"(?:;|\||\`|\$\()\s*(?:bash|sh|ksh|cat|pwd)",
                    "severity": 3,
                },
            ]

            if not validate_patterns(patterns):
                sys.exit(1)

            try:
                encrypted = encrypt_patterns(patterns, key.encode())
                PATTERN_FILE.write_bytes(encrypted)
                os.chmod(PATTERN_FILE, 0o600)  # Secure file permissions
                logger.info("Patterns updated successfully to: %s", PATTERN_FILE)
            except Exception as err:  # pylint: disable=broad-except
                logger.error("Error updating patterns: %s", str(err))
                sys.exit(1)

    except Exception as err:  # pylint: disable=broad-except
        logger.error("Error: %s", str(err))
        sys.exit(1)


if __name__ == "__main__":
    main()
