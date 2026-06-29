import logging
from django.core.cache import cache
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .models import PlayerRating, RatingHistory
from .serializers import (
    PlayerRatingSerializer,
    RatingHistorySerializer,
    WeeklyLeaderboardSerializer,
    GlobalLeaderboardSerializer,
)

logger = logging.getLogger('ratings')


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


@extend_schema(
    responses={200: WeeklyLeaderboardSerializer(many=True)},
    parameters=[
        OpenApiParameter('lang_code', OpenApiTypes.STR, OpenApiParameter.PATH, description='Код языка (например, en, es, de)'),
    ],
    summary='Недельный топ-100 по языку (кэш 5 мин)',
    tags=['ratings'],
)
class WeeklyLeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, lang_code):
        cache_key = f'weekly_leaderboard_{lang_code}'
        data = cache.get(cache_key)

        if data is None:
            qs = PlayerRating.objects.filter(language__code=lang_code).select_related('user', 'language')
            qs = qs.order_by('-score')[:100]
            serializer = WeeklyLeaderboardSerializer(qs, many=True)
            data = serializer.data
            cache.set(cache_key, data, 300)

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: GlobalLeaderboardSerializer(many=True)},
    parameters=[
        OpenApiParameter('lang_code', OpenApiTypes.STR, OpenApiParameter.PATH, description='Код языка'),
    ],
    summary='Глобальный топ-100 по языку (только Pro, кэш 5 мин)',
    tags=['ratings'],
)
class GlobalLeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lang_code):
        if not _has_active_pro(request.user):
            return Response(
                {'detail': 'Требуется активная Pro-подписка.'},
                status=status.HTTP_403_FORBIDDEN
            )

        cache_key = f'global_leaderboard_{lang_code}'
        data = cache.get(cache_key)

        if data is None:
            qs = PlayerRating.objects.filter(language__code=lang_code).select_related('user', 'language')
            qs = qs.order_by('-score')[:100]
            serializer = GlobalLeaderboardSerializer(qs, many=True)
            data = serializer.data
            cache.set(cache_key, data, 300)

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: PlayerRatingSerializer},
    parameters=[
        OpenApiParameter('lang_code', OpenApiTypes.STR, OpenApiParameter.PATH, description='Код языка'),
    ],
    summary='Мой рейтинг по конкретному языку',
    tags=['ratings'],
)
class PlayerRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lang_code):
        try:
            rating = PlayerRating.objects.select_related('language').get(user=request.user, language__code=lang_code)
        except PlayerRating.DoesNotExist:
            return Response(
                {'detail': 'Рейтинг не найден. Начните играть в дуэли!'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PlayerRatingSerializer(rating)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: RatingHistorySerializer(many=True)},
    parameters=[
        OpenApiParameter('lang_code', OpenApiTypes.STR, OpenApiParameter.PATH, description='Код языка'),
    ],
    summary='История изменений рейтинга по языку',
    tags=['ratings'],
)
class RatingHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lang_code):
        try:
            rating = PlayerRating.objects.get(user=request.user, language__code=lang_code)
        except PlayerRating.DoesNotExist:
            return Response(
                {'detail': 'Рейтинг не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        history = RatingHistory.objects.filter(player_rating=rating).order_by('-created_at')
        serializer = RatingHistorySerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)