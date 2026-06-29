import logging
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from reminders.models import ReminderSchedule, Reminder

User = get_user_model()
logger = logging.getLogger('reminders')


class ReminderAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.schedule, _ = ReminderSchedule.objects.get_or_create(user=self.user)

    def test_get_schedule(self):
        response = self.client.get('/api/reminders/schedule/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_enabled'])
        self.assertEqual(response.data['frequency'], 'daily')

    def test_get_schedule_creates_if_not_exists(self):
        self.schedule.delete()
        response = self.client.get('/api/reminders/schedule/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ReminderSchedule.objects.filter(user=self.user).exists())

    def test_patch_schedule(self):
        response = self.client.patch('/api/reminders/schedule/', {
            'is_enabled': False,
            'frequency': 'weekly',
            'preferred_time': '10:00:00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_enabled'])
        self.assertEqual(response.data['frequency'], 'weekly')

    def test_patch_schedule_partial(self):
        response = self.client.patch('/api/reminders/schedule/', {
            'frequency': 'every_2_days',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['frequency'], 'every_2_days')
        self.assertTrue(response.data['is_enabled'])

    def test_unauthenticated(self):
        self.client.logout()
        response = self.client.get('/api/reminders/schedule/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_task_send_daily_review_reminders(self):
        from reminders.tasks import send_daily_review_reminders
        send_daily_review_reminders()

    def test_task_send_inactivity_reminders(self):
        from reminders.tasks import send_inactivity_reminders
        send_inactivity_reminders()

    def test_task_send_subscription_expiring_reminders(self):
        from reminders.tasks import send_subscription_expiring_reminders
        send_subscription_expiring_reminders()