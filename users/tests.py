from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import Profile, EmailVerification, Friendship, UserLanguage

User = get_user_model()


class UsersAuthTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('users:register')
        self.verify_url = reverse('users:verify-email')
        self.login_url = reverse('users:login')
        self.resend_url = reverse('users:resend-verification')
        self.change_password_url = reverse('users:change-password')

        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'phone': '+1234567890'
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
        self.assertTrue(EmailVerification.objects.filter(user__email=self.user_data['email']).exists())

    def test_email_verification_success(self):
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data['email'])
        verification = EmailVerification.objects.get(user=user)

        verify_data = {
            'email': user.email,
            'code': verification.code
        }
        response = self.client.post(self.verify_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_email_verification_expired_code(self):
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data['email'])
        verification = EmailVerification.objects.get(user=user)
        
        verification.expires_at = timezone.now() - timedelta(minutes=1)
        verification.save()

        verify_data = {
            'email': user.email,
            'code': verification.code
        }
        response = self.client.post(self.verify_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unverified_fails(self):
        self.client.post(self.register_url, self.user_data)
        
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_verified_success(self):
        user = User.objects.create_user(
            username='verifieduser',
            email='verified@example.com',
            password='password123',
            is_verified=True
        )

        login_data = {
            'email': 'verified@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class UserProfileAndLanguagesTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='password123',
            is_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.me_url = reverse('users:me')
        self.update_profile_url = reverse('users:update-profile')
        self.update_account_url = reverse('users:update-account')
        self.languages_url = reverse('users:user-languages')

    def test_get_me(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_update_profile(self):
        update_data = {
            'full_name': 'New Name',
            'bio': 'New bio text',
            'ui_language': 'en'
        }
        response = self.client.patch(self.update_profile_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.full_name, 'New Name')
        self.assertEqual(self.user.profile.ui_language, 'en')

    def test_add_and_delete_user_language(self):
        lang_data = {
            'language_code': 'en',
            'level': 'B2',
            'show_level': True
        }
        response = self.client.post(self.languages_url, lang_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserLanguage.objects.filter(user=self.user, language_code='en').exists())

        user_lang = UserLanguage.objects.get(user=self.user, language_code='en')

        detail_url = reverse('users:user-language-detail', kwargs={'pk': user_lang.id})
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserLanguage.objects.filter(user=self.user, language_code='en').exists())


class FriendshipTests(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='password123', is_verified=True
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='password123', is_verified=True
        )

        self.friends_url = reverse('users:friends')
        self.incoming_url = reverse('users:friends-incoming')

    def test_send_and_accept_friend_request(self):
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(self.friends_url, {'to_user': self.user2.username})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Friendship.objects.filter(from_user=self.user1, to_user=self.user2, status='pending').exists())

        friendship = Friendship.objects.get(from_user=self.user1, to_user=self.user2)

        self.client.force_authenticate(user=self.user2)

        incoming_response = self.client.get(self.incoming_url)
        self.assertEqual(len(incoming_response.data), 1)

        action_url = reverse('users:friend-action', kwargs={'pk': friendship.id})
        action_response = self.client.patch(action_url, {'action': 'accept'})
        self.assertEqual(action_response.status_code, status.HTTP_200_OK)

        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')
