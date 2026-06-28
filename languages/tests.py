from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from languages.models import Language, CEFRLevel

User = get_user_model()

TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

User = get_user_model()


@override_settings(CACHES=TEST_CACHES)
class LanguageListTests(APITestCase):

    def setUp(self):
        self.url = reverse('languages:language-list')

        self.lang_en = Language.objects.create(
            name='English', native_name='English',
            code='en', flag_emoji='🇬🇧', is_active=True,
        )
        self.lang_de = Language.objects.create(
            name='German', native_name='Deutsch',
            code='de', flag_emoji='🇩🇪', is_active=True,
        )
        self.lang_hidden = Language.objects.create(
            name='Hidden', native_name='Hidden',
            code='xx', flag_emoji='', is_active=False,
        )

        CEFRLevel.objects.create(
            language=self.lang_en, level='A1', title='Beginner',
            min_vocabulary=0, max_vocabulary=500, order=1,
        )
        CEFRLevel.objects.create(
            language=self.lang_en, level='B2', title='Upper-Intermediate',
            min_vocabulary=3000, max_vocabulary=6000, order=4,
        )

    def test_only_active_languages_returned(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = [lang['code'] for lang in response.data]
        self.assertIn('en', codes)
        self.assertIn('de', codes)
        self.assertNotIn('xx', codes)  # неактивный не показывается

    def test_cefr_levels_nested_in_language(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        en_data = next(l for l in response.data if l['code'] == 'en')
        self.assertEqual(len(en_data['cefr_levels']), 2)


@override_settings(CACHES=TEST_CACHES)
class CEFRLevelListTests(APITestCase):

    def setUp(self):
        self.lang = Language.objects.create(
            name='French', native_name='Français',
            code='fr', flag_emoji='🇫🇷', is_active=True,
        )
        CEFRLevel.objects.create(
            language=self.lang, level='A1', title='Débutant',
            min_vocabulary=0, max_vocabulary=400, order=1,
        )
        CEFRLevel.objects.create(
            language=self.lang, level='C1', title='Avancé',
            min_vocabulary=8000, max_vocabulary=15000, order=5,
        )

    def test_get_cefr_levels_for_language(self):
        url = reverse('languages:cefr-levels', kwargs={'lang_code': 'fr'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_404_for_nonexistent_language(self):
        url = reverse('languages:cefr-levels', kwargs={'lang_code': 'zz'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_404_for_inactive_language(self):
        inactive = Language.objects.create(
            name='Inactive', native_name='Inactive',
            code='ia', flag_emoji='', is_active=False,
        )
        CEFRLevel.objects.create(
            language=inactive, level='A1', title='Test',
            min_vocabulary=0, max_vocabulary=100, order=1,
        )
        url = reverse('languages:cefr-levels', kwargs={'lang_code': 'ia'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(CACHES=TEST_CACHES)
class AdminLanguageToggleTests(APITestCase):

    def setUp(self):
        self.lang = Language.objects.create(
            name='Spanish', native_name='Español',
            code='es', flag_emoji='🇪🇸', is_active=True,
        )
        self.url = reverse('languages:language-toggle', kwargs={'lang_code': 'es'})

        self.moderator = User.objects.create_user(
            username='mod', email='mod@example.com',
            password='password123', is_verified=True,
            dashboard_role='moderator',
        )
        self.regular_user = User.objects.create_user(
            username='regular', email='regular@example.com',
            password='password123', is_verified=True,
        )

    def test_moderator_can_toggle_language(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lang.refresh_from_db()
        self.assertFalse(self.lang.is_active)  

    def test_regular_user_cannot_toggle(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_toggle(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
