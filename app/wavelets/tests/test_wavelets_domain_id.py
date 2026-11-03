"""
BOLA regression tests for wavelets domain_id ownership validation
(audit P0 #2): /api/llm/ and /api/social/ must reject domain_ids the
sender does not own; blank stays allowed (the extension sends it for
masked/denied or not-yet-persisted domains — resolveDomainId).
"""

from core.tests.helpers import create_domain, create_user
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

LLM_URL = reverse("llm:llm-data")
SOCIAL_URL = reverse("social:social-post")

LLM_PAYLOAD = {
    "chat_session_id": "session-1",
    "message_content": "hello",
    "timestamp": "2026-11-03T10:00:00Z",
    "message_id": "m-1",
    "message_type": "prompt",
    "llm_provider": "chatgpt",
    "turn_index": 0,
    "page_title": "t",
    "url": "http://example.com",
    "domain_id": "",
}

SOCIAL_PAYLOAD = {
    "post_id": "post-1",
    "platform": "x",
    "signal_type": "feed",
    "author_handle": "someone",
    "permalink": "http://example.com/p/1",
    "captured_at": "2026-11-03T10:00:00Z",
    "page_url": "http://example.com",
    "domain_id": "",
}


class WaveletDomainIdOwnershipTests(APITestCase):
    """
    domain_id must belong to the authenticated user, or be blank.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(user_id="owner", password="testpass12345")
        self.client.force_authenticate(self.user)
        self.domain = create_domain(user=self.user)

    def test_llm_with_own_domain_id_accepted(self):
        res = self.client.post(
            LLM_URL, {**LLM_PAYLOAD, "domain_id": str(self.domain.id)}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_llm_with_foreign_domain_id_rejected(self):
        other = create_user(user_id="other", password="testpass12345")
        foreign = create_domain(user=other)
        res = self.client.post(
            LLM_URL, {**LLM_PAYLOAD, "domain_id": str(foreign.id)}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("domain_id", res.data)

    def test_llm_with_blank_domain_id_accepted(self):
        res = self.client.post(LLM_URL, LLM_PAYLOAD, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_llm_with_garbage_domain_id_rejected(self):
        res = self.client.post(
            LLM_URL,
            {**LLM_PAYLOAD, "domain_id": "not-a-real-uuid-xyz"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_social_with_own_domain_id_accepted(self):
        res = self.client.post(
            SOCIAL_URL,
            {**SOCIAL_PAYLOAD, "domain_id": str(self.domain.id)},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_social_with_foreign_domain_id_rejected(self):
        other = create_user(user_id="other", password="testpass12345")
        foreign = create_domain(user=other)
        res = self.client.post(
            SOCIAL_URL,
            {**SOCIAL_PAYLOAD, "domain_id": str(foreign.id)},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("domain_id", res.data)

    def test_social_with_blank_domain_id_accepted(self):
        res = self.client.post(SOCIAL_URL, SOCIAL_PAYLOAD, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
