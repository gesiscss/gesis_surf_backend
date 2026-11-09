"""
BOLA regression tests for wavelets domain_id ownership validation
(audit P0 #2): /api/llm/ and /api/social/ must reject domain_ids the
sender does not own; blank stays allowed for domain creation races and
older clients that do not send a domain ID.
"""

from unittest.mock import patch

from core.indexes.base_index import BaseIndex
from core.indexes.chatgpt_index import ChatGPTIndex
from core.indexes.twitter_index import TwitterIndex
from core.tests.helpers import create_domain, create_user
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from wavelets.llm.serializers import INDEX_MAPPING as LLM_INDEX_MAPPING
from wavelets.social.serializers import INDEX_MAPPING as SOCIAL_INDEX_MAPPING

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

    def fake_elasticsearch_save(self, document, *args, **kwargs):
        document.meta.id = "test-document-id"

    def test_llm_with_own_domain_id_accepted(self):
        with patch.object(ChatGPTIndex, "save", autospec=True) as save:
            save.side_effect = self.fake_elasticsearch_save
            res = self.client.post(
                LLM_URL,
                {**LLM_PAYLOAD, "domain_id": str(self.domain.id)},
                format="json",
            )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        document = save.call_args.args[0]
        self.assertEqual(document.user_id, str(self.user.pk))
        self.assertEqual(document.link_status, "linked")

    def test_llm_with_foreign_domain_id_rejected(self):
        other = create_user(user_id="other", password="testpass12345")
        foreign = create_domain(user=other)
        res = self.client.post(
            LLM_URL, {**LLM_PAYLOAD, "domain_id": str(foreign.id)}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("domain_id", res.data)

    def test_llm_with_blank_domain_id_accepted(self):
        with patch.object(ChatGPTIndex, "save", autospec=True) as save:
            save.side_effect = self.fake_elasticsearch_save
            res = self.client.post(LLM_URL, LLM_PAYLOAD, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        document = save.call_args.args[0]
        self.assertEqual(document.user_id, str(self.user.pk))
        self.assertEqual(document.link_status, "")

    def test_llm_stamps_pending_linkage_from_authenticated_user(self):
        payload = {
            **LLM_PAYLOAD,
            "domain_session_id": "global-session-test-windowId-1-tabId-2-domain-example.com",
            "user_id": "forged-user-id",
            "link_status": "linked",
        }

        with patch.object(ChatGPTIndex, "save", autospec=True) as save:
            save.side_effect = self.fake_elasticsearch_save
            res = self.client.post(LLM_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        document = save.call_args.args[0]
        self.assertEqual(document.user_id, str(self.user.pk))
        self.assertEqual(document.link_status, "pending")
        self.assertEqual(document.domain_session_id, payload["domain_session_id"])

    def test_llm_with_garbage_domain_id_rejected(self):
        res = self.client.post(
            LLM_URL,
            {**LLM_PAYLOAD, "domain_id": "not-a-real-uuid-xyz"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_social_with_own_domain_id_accepted(self):
        with patch.object(TwitterIndex, "save", autospec=True) as save:
            save.side_effect = self.fake_elasticsearch_save
            res = self.client.post(
                SOCIAL_URL,
                {**SOCIAL_PAYLOAD, "domain_id": str(self.domain.id)},
                format="json",
            )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        document = save.call_args.args[0]
        self.assertEqual(document.user_id, str(self.user.pk))
        self.assertEqual(document.link_status, "linked")

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
        with patch.object(TwitterIndex, "save", autospec=True) as save:
            save.side_effect = self.fake_elasticsearch_save
            res = self.client.post(SOCIAL_URL, SOCIAL_PAYLOAD, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        document = save.call_args.args[0]
        self.assertEqual(document.user_id, str(self.user.pk))
        self.assertEqual(document.link_status, "")

    def test_social_stamps_pending_linkage_from_authenticated_user(self):
        payload = {
            **SOCIAL_PAYLOAD,
            "domain_session_id": "global-session-test-windowId-1-tabId-2-domain-example.com",
            "user_id": "forged-user-id",
            "link_status": "linked",
        }

        with patch.object(TwitterIndex, "save", autospec=True) as save:
            save.side_effect = self.fake_elasticsearch_save
            res = self.client.post(SOCIAL_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        document = save.call_args.args[0]
        self.assertEqual(document.user_id, str(self.user.pk))
        self.assertEqual(document.link_status, "pending")
        self.assertEqual(document.domain_session_id, payload["domain_session_id"])

    def test_all_wavelet_indexes_inherit_keyword_linkage_fields(self):
        index_classes = set(LLM_INDEX_MAPPING.values())
        index_classes.update(
            index_class
            for platform_indexes in SOCIAL_INDEX_MAPPING.values()
            for index_class in platform_indexes.values()
        )

        for index_class in index_classes:
            with self.subTest(index=index_class.__name__):
                mapping = index_class._doc_type.mapping.to_dict()["properties"]
                for field in ("domain_session_id", "user_id", "link_status"):
                    self.assertEqual(mapping[field], {"type": "keyword"})
                self.assertTrue(issubclass(index_class, BaseIndex))
