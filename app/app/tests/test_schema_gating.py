"""
Tests for the API schema and docs permission gating.

Audit P1 #10: the OpenAPI schema and Swagger docs exposed the full
API surface to unauthenticated users. They are now admin-only.
"""

from core.tests.helpers import create_user
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

SCHEMA_URL = reverse("api-schema")
DOCS_URL = reverse("api-docs")


class PublicSchemaApiTests(TestCase):
    """
    Unauthenticated access to schema/docs must be rejected.
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_schema_requires_auth(self) -> None:
        """
        Anonymous schema requests get 401/403, not the API surface.
        """
        res = self.client.get(SCHEMA_URL)
        self.assertIn(
            res.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_docs_requires_auth(self) -> None:
        """
        Anonymous docs requests get 401/403, not the Swagger UI.
        """
        res = self.client.get(DOCS_URL)
        self.assertIn(
            res.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


class AdminSchemaApiTests(TestCase):
    """
    Admin access to schema/docs keeps working.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = create_user(user_id="admin", is_staff=True, password="adminpass123")
        self.admin.is_superuser = True
        self.admin.save()
        self.client.force_authenticate(self.admin)

    def test_admin_can_fetch_schema(self) -> None:
        """
        Admin schema requests still return the OpenAPI document.
        """
        res = self.client.get(SCHEMA_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_view_docs(self) -> None:
        """
        Admin docs requests still return the Swagger UI.
        """
        res = self.client.get(DOCS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
