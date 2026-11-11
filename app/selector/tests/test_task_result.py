"""
Test for selector API — task-result single-use semantics.

The selector async flow is the extension's ONLY selector fetch path
(async_selectors -> poll task-result), so it stays participant-open.
The result is single-use: it is forgotten from the backend right after
it is fetched (audit P0 #5, A-lite decision).
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from core.tests.helpers import create_user

ASYNC_SELECTORS_URL = reverse(
    "selector:selectorconfig-async-selectors"
)


class SelectorTaskResultTests(TestCase):
    """
    Selector task-result contract: participant-open, single-use results.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(user_id="participant", password="testpass12345")
        self.client.force_authenticate(self.user)

    def test_task_result_single_use(self):
        """
        A fetched selector task result cannot be fetched again.
        """

        class SingleUseTaskResult:
            """
            Behavioral model of a result that is forgotten after fetch.
            """

            def __init__(self, payload):
                self._payload = payload
                self.fetched = False

            def ready(self):
                return not self.fetched

            @property
            def result(self):
                return self._payload

            def forget(self):
                self.fetched = True

        fake = SingleUseTaskResult([{"provider": "facebook"}])
        result_url = reverse("selector:selector-task-result", args=["fake-task-id"])

        with patch("selector.views.AsyncResult", return_value=fake):
            first = self.client.get(result_url)
            self.assertEqual(first.status_code, status.HTTP_200_OK)
            self.assertIn("facebook", first.content.decode())

            second = self.client.get(result_url)
            self.assertEqual(second.status_code, status.HTTP_202_ACCEPTED)

    def test_unknown_task_id_returns_processing(self):
        """
        Unknown task IDs behave like pending ones: 202, no data.
        """
        res = self.client.get(
            reverse("selector:selector-task-result", args=["nonexistent"])
        )
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)

    def test_auth_required(self):
        """
        Anonymous access is rejected.
        """
        client = APIClient()
        res = client.get(
            reverse("selector:selector-task-result", args=["any-id"])
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
