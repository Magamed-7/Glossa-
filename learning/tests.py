from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from languages.models import Language
from subscriptions.models import Plan, Subscription
from learning.models import UserPhrase, ReviewSession

User = get_user_model()


class LearningTests(APITestCase):

    def setUp(self):
        self.free_user = User.objects.create_user(
            username='freeuser', email='free@example.com', password='password123', is_verified=True
        )
        self.pro_user = User.objects.create_user(
            username='prouser', email='pro@example.com', password='password123', is_verified=True
        )

        self.free_plan = Plan.objects.create(name='Free', period='free', price='0.00', is_active=True)
        self.pro_plan = Plan.objects.create(
            name='Pro', period='monthly', price='9.99', is_active=True,
            full_catalog_access=True
        )

       
        Subscription.objects.create(
            user=self.pro_user, plan=self.pro_plan, status='active',
            started_at=timezone.now(), expires_at=timezone.now() + timedelta(days=30)
        )

        self.lang = Language.objects.create(name='Spanish', native_name='Español', code='es', is_active=True)

        self.deck_url = reverse('learning:deck-list')
        self.add_url = reverse('learning:deck-add')
        self.review_url = reverse('learning:review-session')

    def test_add_phrase_creates_review_session(self):
        self.client.force_authenticate(user=self.free_user)
        data = {
            'language': str(self.lang.id),
            'word': 'hola',
            'translation': 'привет',
            'context_sentence': 'Hola, ¿cómo estás?',
            'source': 'manual'
        }
        response = self.client.post(self.add_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        phrase = UserPhrase.objects.get(user=self.free_user, word='hola')
        self.assertEqual(phrase.status, 'active')
        self.assertTrue(ReviewSession.objects.filter(phrase=phrase).exists())

    def test_free_user_limit_55_words_per_day(self):
        self.client.force_authenticate(user=self.free_user)
        for i in range(55):
            UserPhrase.objects.create(
                user=self.free_user, language=self.lang,
                word=f'word{i}', translation=f'trans{i}'
            )

        
        data = {
            'language': str(self.lang.id),
            'word': 'extra',
            'translation': 'extra_trans',
        }
        response = self.client.post(self.add_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pro_user_has_no_word_limit(self):
        self.client.force_authenticate(user=self.pro_user)
        for i in range(55):
            UserPhrase.objects.create(
                user=self.pro_user, language=self.lang,
                word=f'word{i}', translation=f'trans{i}'
            )

        data = {
            'language': str(self.lang.id),
            'word': 'extra',
            'translation': 'extra_trans',
        }
        response = self.client.post(self.add_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_review_session_only_returns_due_phrases(self):
        self.client.force_authenticate(user=self.free_user)

        phrase_due = UserPhrase.objects.create(
            user=self.free_user, language=self.lang, word='due', translation='due'
        )
        ReviewSession.objects.create(phrase=phrase_due, next_review_at=timezone.now() - timedelta(minutes=1))


        phrase_future = UserPhrase.objects.create(
            user=self.free_user, language=self.lang, word='future', translation='future'
        )
        ReviewSession.objects.create(phrase=phrase_future, next_review_at=timezone.now() + timedelta(days=1))

        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        words = [p['word'] for p in response.data]
        self.assertIn('due', words)
        self.assertNotIn('future', words)

    def test_submit_review_sm2_updates_session_and_consecutive_correct(self):
        self.client.force_authenticate(user=self.free_user)
        phrase = UserPhrase.objects.create(
            user=self.free_user, language=self.lang, word='test', translation='test'
        )
        session = ReviewSession.objects.create(phrase=phrase)

        url = reverse('learning:review-submit', kwargs={'pk': phrase.id})

        
        response = self.client.post(url, {'result': 'good'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        session.refresh_from_db()
        self.assertEqual(session.consecutive_correct, 1)
        self.assertEqual(session.last_result, 'good')

    def test_mastered_word_restart(self):
        self.client.force_authenticate(user=self.free_user)
        phrase = UserPhrase.objects.create(
            user=self.free_user, language=self.lang, word='mastered', translation='mastered',
            status='mastered'
        )
        session = ReviewSession.objects.create(
            phrase=phrase, consecutive_correct=6, interval_days=40
        )

        url = reverse('learning:mastered-restart', kwargs={'pk': phrase.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        phrase.refresh_from_db()
        session.refresh_from_db()

        self.assertEqual(phrase.status, 'active')
        self.assertEqual(session.consecutive_correct, 0)
        self.assertEqual(session.interval_days, 1)
