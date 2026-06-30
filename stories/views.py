import logging
from datetime import timedelta, date

from django.utils import timezone
from django.db.models import Q

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Story, StoryWord, UserStoryProgress
from .serializers import (
    StoryListSerializer,
    StoryDetailSerializer,
    StoryCreateSerializer,
    StoryAIAssistSerializer,
)

logger = logging.getLogger('stories')

FREE_DAILY_READ_LIMIT = 7      
FREE_WEEKLY_CREATE_LIMIT = 4  


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



class StoryListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Каталог историй',
        description='Список опубликованных историй с фильтрацией. Free-пользователи видят только бесплатные.',
        responses={200: StoryListSerializer(many=True)},
    )
    def get(self, request):
        is_pro = _has_active_pro(request.user)
        if not is_pro:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            reads_today = UserStoryProgress.objects.filter(
                user=request.user,
                last_read_at__gte=today_start,
            ).count()
            if reads_today >= FREE_DAILY_READ_LIMIT:
                return Response(
                    {
                        'detail': (
                            f'Вы достигли дневного лимита в {FREE_DAILY_READ_LIMIT} историй. '
                            'Оформите Pro подписку для безлимитного доступа.'
                        ),
                        'limit_reached': True,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )


        qs = Story.objects.filter(status='published').select_related(
            'language', 'cefr_level', 'created_by', 'created_by__profile'
        )

        lang = request.query_params.get('language')
        if lang:
            qs = qs.filter(language__code=lang)

        level = request.query_params.get('level')
        if level:
            qs = qs.filter(cefr_level__level=level)

        topic = request.query_params.get('topic')
        if topic:
            qs = qs.filter(topic__icontains=topic)

        featured = request.query_params.get('featured')
        if featured == 'true':
            qs = qs.filter(is_featured=True)

      
        if not is_pro:
            qs = qs.filter(is_premium=False)

        serializer = StoryListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Читать историю',
        description='Получение полного текста истории со словами. Увеличивает счётчик просмотров.',
        responses={200: StoryDetailSerializer},
    )
    def get(self, request, pk):
        try:
            story = Story.objects.select_related(
                'language', 'cefr_level', 'created_by', 'created_by__profile'
            ).prefetch_related('words').get(id=pk, status='published')
        except Story.DoesNotExist:
            return Response({'detail': 'История не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        
        if story.is_premium and not _has_active_pro(request.user):
            return Response(
                {'detail': 'Эта история доступна только для Pro подписчиков.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        
        progress, created = UserStoryProgress.objects.get_or_create(
            user=request.user, story=story
        )
        progress.read_count += 1
        progress.save(update_fields=['read_count', 'last_read_at'])

        
        Story.objects.filter(id=pk).update(views_count=story.views_count + 1)

        serializer = StoryDetailSerializer(story)
        return Response(serializer.data, status=status.HTTP_200_OK)



class StoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Создать историю',
        description='Создание новой истории (уровень B2+). Free-лимит: 4 в неделю. Статус: pending_review.',
        request=StoryCreateSerializer,
        responses={201: StoryListSerializer},
    )
    def post(self, request):
        serializer = StoryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        language = serializer.validated_data['language']
        is_pro = _has_active_pro(request.user)

        
        if not is_pro:
            week_start = timezone.now() - timedelta(days=7)
            created_this_week = Story.objects.filter(
                created_by=request.user,
                created_at__gte=week_start,
            ).count()
            if created_this_week >= FREE_WEEKLY_CREATE_LIMIT:
                return Response(
                    {
                        'detail': (
                            f'Вы достигли лимита в {FREE_WEEKLY_CREATE_LIMIT} истории в неделю. '
                            'Оформите Pro подписку для безлимитного создания.'
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        story = serializer.save(
            created_by=request.user,
            status='pending_review',
        )

        # TODO
        logger.info(f'Новая история на модерации: "{story.title}" от {request.user.email}')

        return Response(
            StoryListSerializer(story).data,
            status=status.HTTP_201_CREATED,
        )



class StoryAIAssistView(APIView):
    # TODO

    @extend_schema(
        summary='AI помощь с историей',
        description='Запрос AI для улучшения текста истории. Только для Pro.',
        request=StoryAIAssistSerializer,
        responses={200: {'type': 'object'}},
    )
    def post(self, request, pk):
        if not _has_active_pro(request.user):
            return Response(
                {'detail': 'AI помощь доступна только для Pro подписчиков.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            story = Story.objects.get(id=pk, created_by=request.user)
        except Story.DoesNotExist:
            return Response(
                {'detail': 'История не найдена или не принадлежит вам.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        text = request.data.get('text', story.content)
        language_code = story.language.code
        level = story.cefr_level.level

        # TODO
        logger.info(f'AI помощь запрошена: story={story.id}, user={request.user.email}')

      
        return Response(
            {
                'detail': 'AI помощь временно недоступна. Будет реализована в следующем обновлении.',
                'story_id': str(story.id),
                'language': language_code,
                'level': level,
            },
            status=status.HTTP_200_OK,
        )
