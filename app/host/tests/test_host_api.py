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
TASK_RESULT_URL = reverse("host:host-task-result", args=["nonexistent-task-id"])


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
        hosts = Host.objects.all()
        serializer = HostSerializer(hosts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_participant_cannot_create_host(self):
        """
        Participant POST is rejected — host writes schedule version
        pushes to every participant extension (audit P0 #3).
        """
        payload = {"hostname": "attacker.example"}
        res = self.client.post(HOST_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Host.objects.filter(hostname="attacker.example").exists()  # pylint: disable=no-member
        )

    def test_participant_cannot_update_host(self):
        """
        Participant PATCH is rejected (audit P0 #3).
        """
        host = create_host(hostname="example.com")
        res = self.client.patch(
            detail_url(host.id), {"hostname": "evil.example"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        host.refresh_from_db()
        self.assertEqual(host.hostname, "example.com")

    def test_participant_cannot_delete_host(self):
        """
        Participant DELETE is rejected (audit P0 #3).
        """
        host = create_host(hostname="example.com")
        res = self.client.delete(detail_url(host.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Host.objects.filter(pk=host.pk).exists())  # pylint: disable=no-member

    def test_participant_cannot_bulk_create_hosts(self):
        """
        Participant bulk_hosts is rejected (tamper channel).
        """
        res = self.client.post(
            reverse("host:host-bulk-hosts"),
            [{"hostname": "a.example"}, {"hostname": "b.example"}],
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Host.objects.count(), 0)  # pylint: disable=no-member

    def test_participant_cannot_trigger_async_hosts(self):
        """
        Participant cannot trigger the async host dump task.
        """
        res = self.client.get(reverse("host:host-async-hosts"))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_participant_cannot_read_task_result(self):
        """
        Participant cannot poll arbitrary Celery task results
        (task-id oracle, audit P0 #5).
        """
        res = self.client.get(TASK_RESULT_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminHostApiTests(TestCase):
    """
    Test the host API (admin).

    Admins retain full management: mutations, bulk, and the
    async/task-result endpoints.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = create_user(user_id="admin", is_staff=True, password="adminpass123")
        self.admin.is_superuser = True
        self.admin.save()
        self.client.force_authenticate(self.admin)

    def test_admin_can_create_host(self):
        """
        Admin POST works.
        """
        payload = {"hostname": "admin.example"}
        res = self.client.post(HOST_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_admin_can_list_hosts(self):
        """
        Admin reads work.
        """
        create_host(hostname="adminhost.example")
        res = self.client.get(HOST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_trigger_async_hosts(self):
        """
        Admin async task trigger works.
        """
        res = self.client.get(reverse("host:host-async-hosts"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
