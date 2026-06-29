import logging
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from notifications.models import Notification, PushSubscription

User = get_user_model()
logger = logging.getLogger('notifications')


class NotificationAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.notification = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Тестовое уведомление',
            body='Это тест',
            channel='websocket'
        )

    def test_list_notifications(self):
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.notification.id))

    def test_list_notifications_filter_by_read(self):
        Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Прочитанное',
            body='Тест',
            channel='websocket',
            is_read=True
        )
        response = self.client.get('/api/notifications/?is_read=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertFalse(response.data[0]['is_read'])

    def test_mark_read_patch(self):
        self.assertFalse(self.notification.is_read)
        response = self.client.patch(
            f'/api/notifications/{self.notification.id}/read/',
            {'notification_id': str(self.notification.id)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)

    def test_mark_read_post(self):
        response = self.client.post(
            f'/api/notifications/{self.notification.id}/read/',
            {'notification_id': str(self.notification.id)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_read_not_found(self):
        fake_id = '00000000-0000-0000-0000-000000000000'
        response = self.client.patch(
            f'/api/notifications/{fake_id}/read/',
            {'notification_id': fake_id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_register_push_token_create(self):
        with patch('notifications.views.logger') as mock_logger:
            response = self.client.post('/api/notifications/push-token/', {
                'endpoint': 'https://example.com/push/abc123',
                'p256dh_key': 'test_key',
                'auth_key': 'test_auth',
                'user_agent': 'test agent'
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(PushSubscription.objects.count(), 1)
            sub = PushSubscription.objects.first()
            self.assertEqual(sub.user, self.user)
            self.assertEqual(sub.endpoint, 'https://example.com/push/abc123')

    def test_register_push_token_update(self):
        PushSubscription.objects.create(
            user=self.user,
            endpoint='https://example.com/push/abc123',
            p256dh_key='old_key',
            auth_key='old_auth',
        )
        response = self.client.post('/api/notifications/push-token/', {
            'endpoint': 'https://example.com/push/abc123',
            'p256dh_key': 'new_key',
            'auth_key': 'new_auth',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PushSubscription.objects.count(), 1)
        sub = PushSubscription.objects.first()
        self.assertEqual(sub.p256dh_key, 'new_key')

    def test_register_push_token_missing_endpoint(self):
        response = self.client.post('/api/notifications/push-token/', {
            'p256dh_key': 'test_key',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)