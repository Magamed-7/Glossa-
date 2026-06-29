import logging

from django.core.cache import cache

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from .models import Language, CEFRLevel
from .serializers import (
    LanguageSerializer,
    CEFRLevelSerializer,
    LanguageToggleRequestSerializer,
)
from users.permissions import IsModerator

logger = logging.getLogger('languages')


LANG_CODE_PARAMETER = OpenApiParameter(
    name='lang_code',
    type=str,
    location=OpenApiParameter.PATH,
    required=True,
    description='Код языка (например en, ru, de, tj).',
)


# Inline response schema for PATCH /toggle — bypasses drf-spectacular's serializer
# resolution (which discards empty components for PATCH responses under the default
# COMPONENT_SPLIT_REQUEST=False setting) by passing a raw schema dict.
LANGUAGE_TOGGLE_RESPONSE_SCHEMA = {
    'type': 'object',
    'properties': {
        'detail': {
            'type': 'string',
            'description': 'Человекочитаемое описание результата операции.',
        },
        'is_active': {
            'type': 'boolean',
            'description': 'Новое значение флага активности языка.',
        },
        'code': {'type': 'string', 'description': 'Код языка.'},
        'name': {'type': 'string', 'description': 'Название языка.'},
    },
    'required': ['detail', 'is_active', 'code', 'name'],
}


@extend_schema(
    responses={200: LanguageSerializer(many=True)},
    summary='Список активных языков с уровнями CEFR (кэш 1 час)',
    tags=['languages · Catalog'],
)
class LanguageListView(APIView):
    permission_classes = [AllowAny]
    CACHE_KEY = 'languages_list'
    CACHE_TTL = 60 * 60

    def get(self, request):
        cached = cache.get(self.CACHE_KEY)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        languages = Language.objects.filter(is_active=True).prefetch_related('cefr_levels')
        serializer = LanguageSerializer(languages, many=True)
        data = serializer.data

        cache.set(self.CACHE_KEY, data, self.CACHE_TTL)
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[LANG_CODE_PARAMETER],
    responses={
        200: CEFRLevelSerializer(many=True),
        404: OpenApiResponse(description='Язык не найден или деактивирован'),
    },
    summary='Список уровней CEFR (A1–C2) для указанного языка',
    tags=['languages · Catalog'],
)
class CEFRLevelListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, lang_code):
        try:
            language = Language.objects.get(code=lang_code, is_active=True)
        except Language.DoesNotExist:
            return Response(
                {'detail': 'Язык не найден или недоступен.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        levels = CEFRLevel.objects.filter(language=language).order_by('order')
        serializer = CEFRLevelSerializer(levels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[LANG_CODE_PARAMETER],
    request=LanguageToggleRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=LANGUAGE_TOGGLE_RESPONSE_SCHEMA,
            description='Язык успешно переключён',
        ),
        401: OpenApiResponse(description='Не авторизован'),
        403: OpenApiResponse(description='Недостаточно прав (нужна роль moderator/superadmin)'),
        404: OpenApiResponse(description='Язык не найден'),
    },
    summary='Активировать / деактивировать язык (только moderator/superadmin)',
    tags=['languages · Admin'],
)
class AdminLanguageToggleView(APIView):
    permission_classes = [IsAuthenticated, IsModerator]

    def patch(self, request, lang_code):
        try:
            language = Language.objects.get(code=lang_code)
        except Language.DoesNotExist:
            return Response({'detail': 'Язык не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if 'is_active' in request.data:
            language.is_active = bool(request.data['is_active'])
        else:
            language.is_active = not language.is_active

        language.save(update_fields=['is_active'])
        cache.delete(LanguageListView.CACHE_KEY)

        action = 'активирован' if language.is_active else 'деактивирован'
        logger.info(
            f'Язык {language.name} ({lang_code}) {action} пользователем {request.user.email}'
        )

        return Response(
            {
                'detail': f'Язык "{language.name}" успешно {action}.',
                'is_active': language.is_active,
                'code': language.code,
                'name': language.name,
            },
            status=status.HTTP_200_OK,
        )