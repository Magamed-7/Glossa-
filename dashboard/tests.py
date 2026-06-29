import logging
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()
logger = logging.getLogger('dashboard')


class DashboardAPITests(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='testpass123',
            dashboard_role='superadmin',
            is_staff=True,
        )
        self.moderator = User.objects.create_user(
            email='mod@example.com',
            username='moderator',
            password='testpass123',
            dashboard_role='moderator',
        )
        self.analyst = User.objects.create_user(
            email='analyst@example.com',
            username='analyst',
            password='testpass123',
            dashboard_role='analyst',
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='testpass123',
        )
        self.client = APIClient()

    def test_overview_superadmin(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('active_users', response.data)
        self.assertIn('pro_users', response.data)

    def test_overview_moderator(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get('/api/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_overview_analyst(self):
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get('/api/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_overview_regular_user_denied(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_management_list(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_user_management_search(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard/users/?search=admin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_management_filter_role(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard/users/?role=moderator')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_ban(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.patch(
            f'/api/dashboard/users/{self.regular_user.id}/ban/',
            {'is_active': False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

    def test_user_unban(self):
        self.regular_user.is_active = False
        self.regular_user.save()
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.patch(
            f'/api/dashboard/users/{self.regular_user.id}/ban/',
            {'is_active': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)

    def test_user_ban_not_found(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.patch(
            '/api/dashboard/users/00000000-0000-0000-0000-000000000000/ban/',
            {'is_active': False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_analytics(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard/analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('free_vs_pro', response.data)

    def test_ai_logs(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard/ai/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_requests', response.data)

    def test_moderator_cannot_access_analytics(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get('/api/dashboard/analytics/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_denied(self):
        response = self.client.get('/api/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)