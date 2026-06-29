import logging
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

from languages.models import Language, CEFRLevel
from ratings.models import PlayerRating, RatingHistory

User = get_user_model()
logger = logging.getLogger('ratings')


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-ratings',
    }
})
class RatingsAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            username='testuser2',
            password='testpass123'
        )
        self.client = APIClient()

        self.lang = Language.objects.create(
            code='en',
            name='English',
            native_name='English',
        )
        CEFRLevel.objects.create(
            language=self.lang,
            level='A1',
            title='Beginner',
            order=1,
            min_vocabulary=0,
            max_vocabulary=500,
        )

        self.rating = PlayerRating.objects.create(
            user=self.user,
            language=self.lang,
            score=1200,
            wins=10,
            losses=5,
            draws=2,
            total_duels=17,
            win_streak=3,
            best_streak=5,
        )
        self.rating2 = PlayerRating.objects.create(
            user=self.user2,
            language=self.lang,
            score=1100,
            wins=8,
            losses=7,
            draws=1,
            total_duels=16,
            win_streak=1,
            best_streak=3,
        )

        RatingHistory.objects.create(
            player_rating=self.rating,
            score_before=1150,
            score_after=1200,
            change=50,
            reason='duel_win'
        )

    def tearDown(self):
        cache.clear()

    def test_weekly_leaderboard(self):
        response = self.client.get('/api/ratings/en/weekly/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['score'], 1200)
        self.assertEqual(response.data[1]['score'], 1100)

    def test_weekly_leaderboard_cached(self):
        self.client.get('/api/ratings/en/weekly/')
        self.rating.score = 1500
        self.rating.save()
        response = self.client.get('/api/ratings/en/weekly/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['score'], 1200)

    def test_global_leaderboard_unauthenticated(self):
        response = self.client.get('/api/ratings/en/global/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_global_leaderboard_no_pro(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/ratings/en/global/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_rating(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/ratings/en/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 1200)
        self.assertEqual(response.data['language_code'], 'en')

    def test_my_rating_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/ratings/es/me/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rating_history(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/ratings/en/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['change'], 50)

    def test_rating_history_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/ratings/es/history/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_elo_calculation(self):
        from ratings.services import calculate_elo_change
        winner_delta, loser_delta = calculate_elo_change(1000, 1200, winner_is_first=True)
        self.assertEqual(winner_delta, 35)
        self.assertEqual(loser_delta, -20)

        winner_delta, loser_delta = calculate_elo_change(1200, 1000, winner_is_first=True)
        self.assertEqual(winner_delta, 25)
        self.assertEqual(loser_delta, -20)

        winner_delta, loser_delta = calculate_elo_change(1000, 1000, is_draw=True)
        self.assertEqual(winner_delta, 5)
        self.assertEqual(loser_delta, 5)
