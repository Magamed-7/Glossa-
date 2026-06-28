from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from languages.models import Language, CEFRLevel
from subscriptions.models import Plan, Subscription
from grammar.models import GrammarLesson, GrammarQuestion, GrammarBookmark, UserGrammarProgress

User = get_user_model()


class GrammarTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='student', email='student@example.com', password='password123', is_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.lang = Language.objects.create(name='English', native_name='English', code='en', is_active=True)
        self.level = CEFRLevel.objects.create(language=self.lang, level='A1', title='Beginner', order=1)

        self.lesson = GrammarLesson.objects.create(
            title='Present Simple', explanation='Usage of Present Simple.',
            language=self.lang, cefr_level=self.level, status='published', is_premium=False
        )

        self.q1 = GrammarQuestion.objects.create(
            lesson=self.lesson, question_type='multiple_choice',
            question_text='He ___ a book.', correct_answer='reads',
            options=['read', 'reads', 'reading'], order=1
        )
        self.q2 = GrammarQuestion.objects.create(
            lesson=self.lesson, question_type='true_false',
            question_text='Present Simple is for future.', correct_answer='false',
            options=['true', 'false'], order=2
        )

        self.list_url = reverse('grammar:lesson-list')
        self.detail_url = reverse('grammar:lesson-detail', kwargs={'pk': self.lesson.id})
        self.submit_url = reverse('grammar:lesson-submit', kwargs={'pk': self.lesson.id})
        self.bookmark_url = reverse('grammar:bookmark-list')

    def test_list_lessons(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_lesson_detail_initializes_progress(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        progress = UserGrammarProgress.objects.get(user=self.user, lesson=self.lesson)
        self.assertEqual(progress.status, 'in_progress')

    def test_submit_test_100_percent_completes_lesson(self):
        data = {
            'answers': {
                str(self.q1.id): 'reads',
                str(self.q2.id): 'false'
            }
        }
        response = self.client.post(self.submit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 100)
        self.assertEqual(response.data['status'], 'completed')

    def test_submit_test_partial_keeps_in_progress(self):
        data = {
            'answers': {
                str(self.q1.id): 'reads',
                str(self.q2.id): 'true'  
            }
        }
        response = self.client.post(self.submit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 50)
        self.assertEqual(response.data['status'], 'in_progress')

    def test_add_and_delete_bookmark(self):
        response = self.client.post(self.bookmark_url, {'lesson': str(self.lesson.id)})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(GrammarBookmark.objects.filter(user=self.user, lesson=self.lesson).exists())

        bookmark = GrammarBookmark.objects.get(user=self.user, lesson=self.lesson)
        delete_url = reverse('grammar:bookmark-delete', kwargs={'pk': bookmark.id})


        delete_response = self.client.delete(delete_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(GrammarBookmark.objects.filter(user=self.user, lesson=self.lesson).exists())
