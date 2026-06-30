import logging
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import UserPhrase, ReviewSession
from .serializers import UserPhraseSerializer, ReviewSubmitSerializer

logger = logging.getLogger('learning')

FREE_DAILY_WORD_LIMIT = 55


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



class DeckListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Моя колода слов',
        description='Список всех слов пользователя с фильтрацией по статусу, категории, языку.',
        responses={200: UserPhraseSerializer(many=True)},
    )
    def get(self, request):
        qs = UserPhrase.objects.filter(user=request.user).prefetch_related('review_sessions')

        status_param = request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        category_param = request.query_params.get('category')
        if category_param:
            qs = qs.filter(category__icontains=category_param)

        lang_param = request.query_params.get('language')
        if lang_param:
            qs = qs.filter(language__code=lang_param)

        serializer = UserPhraseSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddWordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Добавить слово в колоду',
        description='Добавление нового слова. Free-лимит: 55 слов/день. Pro — безлимит.',
        request=UserPhraseSerializer,
        responses={201: UserPhraseSerializer},
    )
    def post(self, request):
        is_pro = _has_active_pro(request.user)
        if not is_pro:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            words_today = UserPhrase.objects.filter(
                user=request.user,
                created_at__gte=today_start,
            ).count()

            if words_today >= FREE_DAILY_WORD_LIMIT:
                return Response(
                    {
                        'detail': (
                            f'Вы исчерпали лимит добавления слов ({FREE_DAILY_WORD_LIMIT} в день). '
                            'Оформите Pro подписку для безлимитного добавления слов.'
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = UserPhraseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        word = serializer.validated_data['word']
        language = serializer.validated_data['language']

  
        if UserPhrase.objects.filter(user=request.user, word=word, language=language).exists():
            return Response(
                {'detail': 'Это слово уже добавлено в вашу колоду.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        phrase = serializer.save(user=request.user, status='active')


        ReviewSession.objects.create(phrase=phrase)

        logger.info(f'Пользователь {request.user.email} добавил слово: "{word}"')
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class ReviewSessionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Слова для повторения',
        description='Слова, у которых наступил срок повторения (next_review_at <= now).',
        responses={200: UserPhraseSerializer(many=True)},
    )
    def get(self, request):
        now = timezone.now()
        qs = UserPhrase.objects.filter(
            user=request.user,
            status='active',
            review_sessions__next_review_at__lte=now,
        ).prefetch_related('review_sessions')

        lang_param = request.query_params.get('language')
        if lang_param:
            qs = qs.filter(language__code=lang_param)

        serializer = UserPhraseSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitReviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Отправить результат повторения',
        description='Результат: again/hard/good/easy. Алгоритм SM-2 обновляет интервал.',
        request=ReviewSubmitSerializer,
        responses={200: {'type': 'object'}},
    )
    def post(self, request, pk):
        try:
            phrase = UserPhrase.objects.get(id=pk, user=request.user)
        except UserPhrase.DoesNotExist:
            return Response({'detail': 'Слово не найдено.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result_choice = serializer.validated_data['result']
        quality = ReviewSubmitSerializer.RESULT_QUALITY_MAP[result_choice]

        
        session, _ = ReviewSession.objects.get_or_create(phrase=phrase)

       
        session.last_result = result_choice
        session.apply_sm2(quality)

       
        if session.consecutive_correct >= 5 and session.interval_days > 30:
            phrase.status = 'mastered'
            phrase.save(update_fields=['status'])
            logger.info(f'Слово "{phrase.word}" выучено пользователем {request.user.email}')

        return Response(
            {
                'detail': 'Результат сохранен.',
                'phrase_status': phrase.status,
                'next_review_at': session.next_review_at,
                'interval_days': session.interval_days,
            },
            status=status.HTTP_200_OK,
        )



class MasteredWordsListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Выученные слова',
        description='Список слов со статусом mastered.',
        responses={200: UserPhraseSerializer(many=True)},
    )
    def get(self, request):
        qs = UserPhrase.objects.filter(user=request.user, status='mastered')
        serializer = UserPhraseSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RestartWordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Вернуть выученное слово в колоду',
        description='Сброс прогресса выученного слова для повторения.',
        responses={200: {'type': 'object'}},
    )
    def post(self, request, pk):
        try:
            phrase = UserPhrase.objects.get(id=pk, user=request.user, status='mastered')
        except UserPhrase.DoesNotExist:
            return Response(
                {'detail': 'Выученное слово не найдено.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        
        phrase.status = 'active'
        phrase.save(update_fields=['status'])

        
        session, _ = ReviewSession.objects.get_or_create(phrase=phrase)
        session.easiness_factor = 2.5
        session.interval_days = 1
        session.repetitions = 0
        session.consecutive_correct = 0
        session.next_review_at = timezone.now()
        session.last_result = None
        session.save()

        logger.info(f'Слово "{phrase.word}" возвращено в колоду пользователем {request.user.email}')

        return Response(
            {'detail': 'Слово возвращено в активный цикл повторений.'},
            status=status.HTTP_200_OK,
        )
