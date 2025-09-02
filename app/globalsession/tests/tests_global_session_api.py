"""
Test for GlobalSession API
"""

from datetime import datetime, timezone
import random
from typing import Any, Union
from uuid import UUID

from core.models import GlobalSession
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from globalsession.serializers import GlobalSessionSerializer 


GLOBAL_SESSION_URL = reverse("globalsession:globalsession-list")


# Helper functions

# Create a sample user
def create_user(**params: Any) -> AbstractUser:
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(**params)

# Create a sample global session
def create_global_session(user: AbstractUser, **params: Any) -> GlobalSession:
    """
    Create and return a sample global session
    """
    defaults: dict[str, Any] = {
        "start_time": datetime.now(timezone.utc),
        "global_session_id": "session_{}".format(random.randint(10000, 99999))
    }
    defaults.update(params)
    
    return GlobalSession.objects.create(user=user, **defaults)

# Create detailed URL
def detailed_url(global_session_id: Union[str, UUID]) -> str:
    """
    Create and return the detailed URL for a global session
    """
    return reverse("globalsession:globalsession-detail", args=[global_session_id])

# Test in Public Access
class PublicGlobalSessionApiTests(APITestCase):
    """
    Test unauthenticated GlobalSession API access
    """

    def setUp(self) -> None:
        
        self.client = APIClient()

    def test_auth_required(self) -> None:
        """
        Test that authentication is required to access the GlobalSession API
        """
        res = self.client.get(GLOBAL_SESSION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

# Test in Private Access (Logged In Users)
class PrivateGlobalSessionApiTests(APITestCase):
    """
    Test authenticated GlobalSession API access
    """

    def setUp(self) -> None:

        self.client = APIClient()
        self.user = create_user(user_id="123", password="password123")
        self.client.force_authenticate(user=self.user)

    def test_auth_required(self) -> None:
        """
        Test that authentication is required to access the GlobalSession API
        """
        res = self.client.get(GLOBAL_SESSION_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_global_sessions(self) -> None:
        """
        Test retrieving global sessions
        """
        session = create_global_session(user=self.user)
        
        res = self.client.get(GLOBAL_SESSION_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(hasattr(res, 'data'))
        self.assertIsInstance(res.data, list, "Response data is not a list")
        self.assertEqual(str(res.data[0]["id"]), str(session.id))

    def test_list_global_sessions(self) -> None:
        """
        Test retrieving a list of global sessions
        """
        create_global_session(user=self.user)
        
        res = self.client.get(GLOBAL_SESSION_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_global_sessions_limited_to_user(self) -> None:
        """
        Test that global sessions returned are for the authenticated user
        """
        other_user = create_user(user_id="other", password="testpass")
        
        create_global_session(user=other_user)
        create_global_session(user=self.user)
        
        res = self.client.get(GLOBAL_SESSION_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(str(res.data[0]["user"]), str(self.user.pk))

    def test_get_global_session_detail(self) -> None:
        """
        Test retrieving a specific global session
        """
        session = create_global_session(user=self.user)

        url = detailed_url(session.id)
        serializer = GlobalSessionSerializer(session)
        self.assertEqual(str(serializer.data["id"]), str(session.id))

    def test_create_global_session_successful(self) -> None:
        """
        Test creating a new global session
        """
        
        data = {
            "start_time": datetime.now(timezone.utc),
            "global_session_id": "session_{}".format(random.randint(10000, 99999))
        }
        
        res = self.client.post(GLOBAL_SESSION_URL, data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(hasattr(res, 'data'))
        self.assertEqual(str(res.data["user"]), str(self.user.pk))
        
    def test_create_global_session_invalid(self) -> None:
        """
        Test creating a new global session with invalid payload
        """
        payload = {
            "start_time": "", 
            "global_session_id": "session_12345"
        }
        
        res = self.client.post(GLOBAL_SESSION_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_partial_update_global_session(self) -> None:
        """
        Test updating a global session with patch
        """
        session = create_global_session(
            user=self.user,
            global_session_id="session_12345"
        )

        payload = {
            "closing_time": datetime.now(timezone.utc)
        }

        url = detailed_url(session.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.closing_time, payload["closing_time"])

    def test_user_returns_error(self) -> None:
        """
        Test that a user receives an error when trying to access another user's session
        """
        other_user = create_user(user_id="other", password="testpass")
        session = create_global_session(user=other_user)

        url = detailed_url(session.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
