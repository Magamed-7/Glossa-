import logging
from django.core.cache import cache

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Language, CEFRLevel
from .serializers import LanguageSerializer, LanguageShortSerializer, CEFRLevelSerializer
from users.permissions import IsModerator

logger = logging.getLogger('languages')



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



class AdminLanguageToggleView(APIView):
    permission_classes = [IsAuthenticated, IsModerator]

    def patch(self, request, lang_code):
        try:
            language = Language.objects.get(code=lang_code)
        except Language.DoesNotExist:
            return Response({'detail': 'Язык не найден.'}, status=status.HTTP_404_NOT_FOUND)

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
            },
            status=status.HTTP_200_OK,
        )
