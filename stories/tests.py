from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from languages.models import Language, CEFRLevel
from subscriptions.models import Plan, Subscription
from stories.models import Story, StoryWord, UserStoryProgress

User = get_user_model()


class StoryTests(APITestCase):

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
            full_catalog_access=True, ai_story_assist=True
        )

        
        Subscription.objects.create(
            user=self.pro_user, plan=self.pro_plan, status='active',
            started_at=timezone.now(), expires_at=timezone.now() + timedelta(days=30)
        )

        
        self.lang = Language.objects.create(name='English', native_name='English', code='en', is_active=True)
        self.level_a1 = CEFRLevel.objects.create(language=self.lang, level='A1', title='Beginner', order=1)
        self.level_b2 = CEFRLevel.objects.create(language=self.lang, level='B2', title='Upper-Intermediate', order=4)

        
        self.free_story = Story.objects.create(
            title='Free Story', content='Hello English world.',
            language=self.lang, cefr_level=self.level_a1,
            status='published', is_premium=False, created_by=self.pro_user
        )

    
        self.premium_story = Story.objects.create(
            title='Premium Story', content='Hello Advanced English world.',
            language=self.lang, cefr_level=self.level_b2,
            status='published', is_premium=True, created_by=self.pro_user
        )

      
        self.draft_story = Story.objects.create(
            title='Draft Story', content='Draft content.',
            language=self.lang, cefr_level=self.level_b2,
            status='draft', created_by=self.pro_user
        )

        self.list_url = reverse('stories:story-list')
        self.create_url = reverse('stories:story-create')

    def test_list_stories_free_user_sees_only_free_published(self):
        self.client.force_authenticate(user=self.free_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s['id'] for s in response.data]
        self.assertIn(str(self.free_story.id), ids)
        self.assertNotIn(str(self.premium_story.id), ids)
        self.assertNotIn(str(self.draft_story.id), ids)

    def test_list_stories_pro_user_sees_all_published(self):
        self.client.force_authenticate(user=self.pro_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s['id'] for s in response.data]
        self.assertIn(str(self.free_story.id), ids)
        self.assertIn(str(self.premium_story.id), ids)
        self.assertNotIn(str(self.draft_story.id), ids)

    def test_read_story_detail_increases_views(self):
        self.client.force_authenticate(user=self.free_user)
        url = reverse('stories:story-detail', kwargs={'pk': self.free_story.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.free_story.refresh_from_db()
        self.assertEqual(self.free_story.views_count, 1)

    def test_free_user_cannot_read_premium_story(self):
        self.client.force_authenticate(user=self.free_user)
        url = reverse('stories:story-detail', kwargs={'pk': self.premium_story.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pro_user_can_read_premium_story(self):
        self.client.force_authenticate(user=self.pro_user)
        url = reverse('stories:story-detail', kwargs={'pk': self.premium_story.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_free_user_read_limit_7_per_day(self):
        self.client.force_authenticate(user=self.free_user)
        
        for i in range(7):
            s = Story.objects.create(
                title=f'Story {i}', content='Content', language=self.lang,
                cefr_level=self.level_a1, status='published', is_premium=False
            )
            UserStoryProgress.objects.create(user=self.free_user, story=s)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['limit_reached'])

    def test_create_story_restricted_to_b2_or_above(self):
        self.client.force_authenticate(user=self.pro_user)
       
        data = {
            'title': 'My New A1 Story',
            'content': 'Hello A1.',
            'language': str(self.lang.id),
            'cefr_level': str(self.level_a1.id),
            'read_time_minutes': 2
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_story_success_status_pending(self):
        self.client.force_authenticate(user=self.pro_user)
        data = {
            'title': 'My New B2 Story',
            'content': 'Hello B2.',
            'language': str(self.lang.id),
            'cefr_level': str(self.level_b2.id),
            'read_time_minutes': 5
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending_review')

    def test_ai_assist_premium_only(self):
        self.client.force_authenticate(user=self.free_user)
        
        story = Story.objects.create(
            title='Free User Story', content='content', language=self.lang,
            cefr_level=self.level_b2, status='draft', created_by=self.free_user
        )
        url = reverse('stories:story-ai-assist', kwargs={'pk': story.id})
        response = self.client.post(url, {'text': 'new content'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
