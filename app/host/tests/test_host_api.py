"""
Test cases for the host app.
"""

from core.models import Host
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from host.serializers import HostSerializer
from rest_framework import status
from rest_framework.test import APIClient

HOST_URL = reverse("host:host-list")


def create_user(**params):
    """
    Create a user object.
    """
    return get_user_model().objects.create_user(**params)


def create_host(**params):
    """
    Create a host object.
    """
    return Host.objects.create(**params)


def detail_url(host_id):
    """
    Return host detail URL.
    """
    return reverse("host:host-detail", args=[host_id])


class PublicHostApiTests(TestCase):
    """
    Test the host API (public).
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required.
        """
        res = self.client.get(HOST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateHostApiTests(TestCase):
    """
    Test the host API (private).
    """

    def setUp(self):
        self.client = APIClient()
        self.create_user = create_user(user_id="test", password="test")
        self.client.force_authenticate(self.create_user)

    def test_auth_required(self):
        """
        Test that authentication is required.
        """
        res = self.client.get(HOST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrive_hosts(self):
        """
        Test retrieving a list of hosts.
        """
        create_host(hostname="test1")
        create_host(hostname="test2")

        res = self.client.get(HOST_URL)
        hosts = Host.objects.all().order_by("-id")
        serializer = HostSerializer(hosts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
