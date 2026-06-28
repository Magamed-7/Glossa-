from unittest.mock import patch

from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.test import override_settings

from subscriptions.models import Plan, Subscription
from ai.models import AIRequestLog

User = get_user_model()

TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


class AITests(APITestCase):

    def setUp(self):
        self.free_user = User.objects.create_user(
            username='freeuser', email='free@example.com', password='password123', is_verified=True
        )
        self.pro_user = User.objects.create_user(
            username='prouser', email='pro@example.com', password='password123', is_verified=True
        )
        self.pro_plan = Plan.objects.create(
            name='Pro', period='monthly', price='9.99', is_active=True,
            full_catalog_access=True
        )
        now = timezone.now()
        Subscription.objects.create(
            user=self.pro_user, plan=self.pro_plan, status='active',
            started_at=now, expires_at=now + timedelta(days=30)
        )
        self.explain_url = reverse('ai:explain-word')
        self.generate_url = reverse('ai:generate-story')

    def test_free_user_cannot_access_explain_word(self):
        self.client.force_authenticate(user=self.free_user)
        response = self.client.post(self.explain_url, {'word': 'test', 'language_code': 'en'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_free_user_cannot_access_generate_story(self):
        self.client.force_authenticate(user=self.free_user)
        response = self.client.post(self.generate_url, {'language_code': 'en', 'level': 'A1', 'topic': 'nature'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_gets_401(self):
        response = self.client.post(self.explain_url, {'word': 'test', 'language_code': 'en'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(CACHES=TEST_CACHES)
    def test_explain_word_missing_required_fields(self):
        self.client.force_authenticate(user=self.pro_user)
        response = self.client.post(self.explain_url, {'word': 'test'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.explain_url, {'language_code': 'en'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(CACHES=TEST_CACHES)
    def test_generate_story_missing_required_fields(self):
        self.client.force_authenticate(user=self.pro_user)
        response = self.client.post(self.generate_url, {'language_code': 'en', 'level': 'A1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.generate_url, {'language_code': 'en', 'topic': 'nature'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(CACHES=TEST_CACHES)
    def test_pro_user_explain_word_returns_explanation(self):
        self.client.force_authenticate(user=self.pro_user)
        data = {'word': 'hola', 'language_code': 'es', 'context': 'Hola mundo'}

        response = self.client.post(self.explain_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('explanation', response.data)

    @override_settings(CACHES=TEST_CACHES)
    def test_pro_user_explain_word_gets_cached(self):
        self.client.force_authenticate(user=self.pro_user)
        data = {'word': 'hola', 'language_code': 'es', 'context': 'Hola mundo'}

        response1 = self.client.post(self.explain_url, data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(self.explain_url, data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertTrue(response2.data['cached'])

        logs = AIRequestLog.objects.filter(user=self.pro_user, request_type='explain_word')
        self.assertGreaterEqual(logs.count(), 1)

    @patch('ai.views.generate_story_async')
    def test_pro_user_generate_story_returns_202_accepted(self, mock_task):
        self.client.force_authenticate(user=self.pro_user)
        data = {'language_code': 'en', 'level': 'B2', 'topic': 'travel'}

        response = self.client.post(self.generate_url, data)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['language_code'], 'en')
        self.assertEqual(response.data['level'], 'B2')
        self.assertEqual(response.data['topic'], 'travel')
        mock_task.delay.assert_called_once_with(
            user_id=self.pro_user.id,
            language_code='en',
            cefr_level='B2',
            topic='travel',
        )

    @override_settings(CACHES=TEST_CACHES)
    def test_expired_subscription_user_gets_403(self):
        expired_user = User.objects.create_user(
            username='expireduser', email='expired@example.com', password='password123', is_verified=True
        )
        now = timezone.now()
        Subscription.objects.create(
            user=expired_user, plan=self.pro_plan, status='active',
            started_at=now - timedelta(days=60), expires_at=now - timedelta(days=1)
        )
        self.client.force_authenticate(user=expired_user)
        response = self.client.post(self.explain_url, {'word': 'test', 'language_code': 'en'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(CACHES=TEST_CACHES)
    def test_ai_request_log_created_for_explain_word(self):
        self.client.force_authenticate(user=self.pro_user)
        self.client.post(self.explain_url, {'word': 'hello', 'language_code': 'en'})

        log = AIRequestLog.objects.filter(
            user=self.pro_user, request_type='explain_word'
        ).first()
        self.assertIsNotNone(log)

    @override_settings(CACHES=TEST_CACHES)
    def test_different_contexts_bypass_cache(self):
        self.client.force_authenticate(user=self.pro_user)

        self.client.post(self.explain_url, {'word': 'bank', 'language_code': 'en', 'context': 'river bank'})
        self.client.post(self.explain_url, {'word': 'bank', 'language_code': 'en', 'context': 'financial bank'})

        logs = AIRequestLog.objects.filter(
            user=self.pro_user, request_type='explain_word'
        )
        self.assertEqual(logs.count(), 2)
