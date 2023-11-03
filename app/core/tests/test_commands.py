"""
Test custom Django commands.
"""

from typing import Any
from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase
from psycopg2 import OperationalError as Psycopg2Error


@patch("core.management.commands.wait_for_db.Command.check")
class CommandTest(SimpleTestCase):
    """Test custom Django commands."""

    def test_wait_for_db_ready(self: "CommandTest", patched_check: Any) -> None:
        """Test custom Django commands."""
        patched_check.return_value = True

        call_command("wait_for_db")

        patched_check.asset_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_wait_for_db_delay(
        self: "CommandTest", patched_sleep: Any, patched_check: Any
    ) -> None:
        """Test waiting for database when getting OperationalError."""
        patched_check.side_effect = (
            [Psycopg2Error] * 2 + [OperationalError] * 3 + [True]
        )

        call_command("wait_for_db")

        self.assertEqual(patched_check.call_count, 6)
        patched_check.asset_called_once_with(databases=["default"])
