import logging
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from achievements.models import Achievement, UserAchievement
from achievements.services import check_achievements, _has, _award

User = get_user_model()
logger = logging.getLogger('achievements')


class AchievementAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.achievement = Achievement.objects.create(
            code='first_step',
            title='First Step',
            description='Первые шаги в изучении языка',
            icon='🎉',
            category='levels',
            condition={'type': 'levels'}
        )
        self.achievement2 = Achievement.objects.create(
            code='collector',
            title='Collector',
            description='Добавил 100 слов',
            icon='📚',
            category='vocabulary',
            condition={'type': 'vocabulary', 'target': 100}
        )

    def test_list_achievements(self):
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_my_achievements_empty(self):
        response = self.client.get('/api/achievements/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_my_achievements_with_award(self):
        UserAchievement.objects.create(user=self.user, achievement=self.achievement)
        response = self.client.get('/api/achievements/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['achievement']['code'], 'first_step')

    def test_award_creates_user_achievement(self):
        result = _award(self.user, 'first_step')
        self.assertTrue(result)
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement__code='first_step').exists())

    def test_award_no_double_award(self):
        _award(self.user, 'first_step')
        result = _award(self.user, 'first_step')
        self.assertFalse(result)

    def test_award_nonexistent_code(self):
        result = _award(self.user, 'nonexistent')
        self.assertFalse(result)

    def test_has_true(self):
        UserAchievement.objects.create(user=self.user, achievement=self.achievement)
        self.assertTrue(_has(self.user, 'first_step'))

    def test_has_false(self):
        self.assertFalse(_has(self.user, 'first_step'))

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_check_achievements_runs_without_error(self):
        check_achievements(self.user)