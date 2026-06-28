import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import GrammarLesson, GrammarExample, GrammarQuestion, UserGrammarProgress, GrammarBookmark
from .serializers import (
    GrammarLessonSerializer,
    GrammarLessonDetailSerializer,
    UserGrammarProgressSerializer,
    GrammarBookmarkSerializer,
)

logger = logging.getLogger('grammar')


def _has_active_pro(user):
    sub = (
        user.subscriptions
        .filter(status='active')
        .select_related('plan')
        .order_by('-created_at')
        .first()
    )
    if not sub:
        return False
    return sub.is_active and sub.plan.full_catalog_access



class LessonListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = GrammarLesson.objects.filter(status='published').select_related('language', 'cefr_level')

        lang = request.query_params.get('language')
        if lang:
            qs = qs.filter(language__code=lang)

        level = request.query_params.get('level')
        if level:
            qs = qs.filter(cefr_level__level=level)

        tag = request.query_params.get('tag')
        if tag:
            qs = qs.filter(tags__icontains=tag)

       
        if not _has_active_pro(request.user):
            qs = qs.filter(is_premium=False)

        serializer = GrammarLessonSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class LessonDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            lesson = GrammarLesson.objects.prefetch_related('examples', 'questions').get(id=pk, status='published')
        except GrammarLesson.DoesNotExist:
            return Response({'detail': 'Урок не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if lesson.is_premium and not _has_active_pro(request.user):
            return Response(
                {'detail': 'Этот урок доступен только Pro пользователям.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        
        progress, created = UserGrammarProgress.objects.get_or_create(
            user=request.user, lesson=lesson
        )
        if progress.status == 'not_started':
            progress.status = 'in_progress'
            progress.save(update_fields=['status'])

        serializer = GrammarLessonDetailSerializer(lesson, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)



class LessonTestSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            lesson = GrammarLesson.objects.prefetch_related('questions').get(id=pk, status='published')
        except GrammarLesson.DoesNotExist:
            return Response({'detail': 'Урок не найден.'}, status=status.HTTP_404_NOT_FOUND)

        answers = request.data.get('answers', {})
        questions = lesson.questions.all()
        total_questions = questions.count()

        if total_questions == 0:
            return Response(
                {'detail': 'У этого урока нет вопросов для тестирования.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        correct_count = 0
        details = {}

        for q in questions:
            user_ans = answers.get(str(q.id))
         
            is_correct = False
            if user_ans is not None:
                if str(user_ans).strip().lower() == str(q.correct_answer).strip().lower():
                    is_correct = True
                    correct_count += 1
            details[str(q.id)] = {
                'is_correct': is_correct,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
            }

        score_percent = int((correct_count / total_questions) * 100)

        
        progress, _ = UserGrammarProgress.objects.get_or_create(
            user=request.user, lesson=lesson
        )
        progress.attempts += 1
        progress.max_score = max(progress.max_score, score_percent)

        if score_percent == 100:
            progress.status = 'completed'
            progress.completed_at = timezone.now()
        else:
            progress.status = 'in_progress'

        progress.score = score_percent
        progress.save()

        # TODO
        logger.info(f'Тест сдан: урок {lesson.title}, пользователь {request.user.email}, результат {score_percent}%')

        return Response(
            {
                'score': score_percent,
                'correct_count': correct_count,
                'total_questions': total_questions,
                'status': progress.status,
                'details': details,
            },
            status=status.HTTP_200_OK,
        )



class GrammarBookmarkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookmarks = GrammarBookmark.objects.filter(user=request.user).select_related('lesson')
        serializer = GrammarBookmarkSerializer(bookmarks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        lesson_id = request.data.get('lesson')
        if not lesson_id:
            return Response({'detail': 'ID урока обязателен.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lesson = GrammarLesson.objects.get(id=lesson_id)
        except GrammarLesson.DoesNotExist:
            return Response({'detail': 'Урок не найден.'}, status=status.HTTP_404_NOT_FOUND)

        bookmark, created = GrammarBookmark.objects.get_or_create(
            user=request.user, lesson=lesson
        )
        if not created:
            return Response({'detail': 'Этот урок уже в закладках.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = GrammarBookmarkSerializer(bookmark)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GrammarBookmarkDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            bookmark = GrammarBookmark.objects.get(id=pk, user=request.user)
        except GrammarBookmark.DoesNotExist:
            return Response({'detail': 'Закладка не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        bookmark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
