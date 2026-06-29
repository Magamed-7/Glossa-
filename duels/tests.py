from unittest.mock import patch, MagicMock

from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from languages.models import Language, CEFRLevel
from subscriptions.models import Plan, Subscription
from duels.models import Duel, DuelRound, DuelResult

User = get_user_model()

MOCK_DUEL_QUESTION = {
    'question_type': 'translate_word',
    'question': 'How do you say "hello"?',
    'options': ['hello', 'goodbye', 'thank you', 'please'],
    'correct_answer': 'hello',
}

MOCK_AI_ANSWER = 'goodbye'


def _mock_ai_service():
    svc = MagicMock()
    svc.generate_duel_question.return_value = MOCK_DUEL_QUESTION
    svc.ai_duel_answer.return_value = MOCK_AI_ANSWER
    svc.explain_word.return_value = '{}'
    svc.generate_story.return_value = 'text'
    svc.assist_story_creation.return_value = '{}'
    return svc


class DuelTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='player1', email='player1@test.com', password='pass123', is_verified=True
        )
        self.user2 = User.objects.create_user(
            username='player2', email='player2@test.com', password='pass123', is_verified=True
        )
        self.pro_plan = Plan.objects.create(
            name='Pro', period='monthly', price='9.99', is_active=True,
            full_catalog_access=True, rated_duels_access=True,
        )
        now = timezone.now()
        Subscription.objects.create(
            user=self.user2, plan=self.pro_plan, status='active',
            started_at=now, expires_at=now + timedelta(days=30),
        )

        self.language = Language.objects.create(
            name='English', native_name='English', code='en', is_active=True,
        )
        self.level = CEFRLevel.objects.create(
            language=self.language, level='B2', title='B2', order=4,
        )

    def _auth(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    @patch('duels.views.AIService', return_value=_mock_ai_service())
    def test_create_duel_creates_waiting_session(self, mock_ai_cls):
        self._auth()
        response = self.client.post('/api/duels/create/', {
            'language_code': 'en', 'cefr_level': 'B2', 'mode': 'casual',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'waiting')
        self.assertEqual(response.data['mode'], 'casual')
        self.assertEqual(response.data['player_one_username'], 'player1')

    @patch('duels.views.AIService', return_value=_mock_ai_service())
    def test_free_user_cannot_create_rated_duel(self, mock_ai_cls):
        self._auth()
        response = self.client.post('/api/duels/create/', {
            'language_code': 'en', 'cefr_level': 'B2', 'mode': 'rated',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('duels.views.AIService', return_value=_mock_ai_service())
    def test_pro_user_can_create_rated_duel(self, mock_ai_cls):
        self._auth(self.user2)
        response = self.client.post('/api/duels/create/', {
            'language_code': 'en', 'cefr_level': 'B2', 'mode': 'rated',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['mode'], 'rated')

    def test_create_duel_invalid_language(self):
        self._auth()
        response = self.client.post('/api/duels/create/', {
            'language_code': 'xx', 'cefr_level': 'B2', 'mode': 'casual',
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('duels.views.AIService', return_value=_mock_ai_service())
    def test_duel_detail_returns_403_for_non_participant(self, mock_ai_cls):
        self._auth(self.user2)
        resp = self.client.post('/api/duels/create/', {
            'language_code': 'en', 'cefr_level': 'B2', 'mode': 'casual',
        })
        duel_id = resp.data['id']

        self._auth(self.user)
        response = self.client.get(f'/api/duels/{duel_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('duels.views.AIService', return_value=_mock_ai_service())
    def test_join_existing_waiting_duel(self, mock_ai_cls):
        self._auth()
        resp1 = self.client.post('/api/duels/create/', {
            'language_code': 'en', 'cefr_level': 'B2', 'mode': 'casual',
        })
        duel_id = resp1.data['id']
        self.assertEqual(resp1.data['status'], 'waiting')

        self._auth(self.user2)
        resp2 = self.client.post('/api/duels/create/', {
            'language_code': 'en', 'cefr_level': 'B2', 'mode': 'casual',
        })
        self.assertEqual(resp2.data['status'], 'in_progress')
        self.assertEqual(resp2.data['player_two_username'], 'player2')
        self.assertEqual(len(resp2.data['rounds']), 5)

    @patch('duels.views.AIService', return_value=_mock_ai_service())
    def test_duel_with_ai_completes_successfully(self, mock_ai_cls):
        self._auth()
        response = self.client.post('/api/duels/ai/', {
            'language_code': 'en', 'cefr_level': 'B2', 'mode': 'casual',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('duel', response.data)
        self.assertIn('result', response.data)

    def test_duel_history_empty(self):
        self._auth()
        response = self.client.get('/api/duels/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @patch('duels.views.AIService', return_value=_mock_ai_service())
    def test_duel_result_view_returns_data(self, mock_ai_cls):
        self._auth()
        resp = self.client.post('/api/duels/ai/', {
            'language_code': 'en', 'cefr_level': 'B2', 'mode': 'casual',
        })
        duel_id = resp.data['duel']['id']

        result_resp = self.client.get(f'/api/duels/{duel_id}/result/')
        self.assertEqual(result_resp.status_code, status.HTTP_200_OK)
        self.assertIn('recommended_words', result_resp.data)
        self.assertIsInstance(result_resp.data['recommended_words'], list)
