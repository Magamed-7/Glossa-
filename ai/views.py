import json
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .services import AIService
from .tasks import generate_story_async

logger = logging.getLogger('ai')


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


class ExplainWordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _has_active_pro(request.user):
            return Response(
                {'detail': 'Эта функция доступна только для Pro подписчиков.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        word = request.data.get('word')
        context = request.data.get('context', '')
        lang_code = request.data.get('language_code')

        if not word or not lang_code:
            return Response(
                {'detail': 'Поля word и language_code обязательны.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.core.cache import cache
        cache_key = f'ai_explain_{lang_code}_{word}_{hash(context)}'
        cached_response = cache.get(cache_key)
        if cached_response:
            AIService()._log_request(
                user=request.user,
                request_type='explain_word',
                prompt=f'Word: {word}, Context: {context}',
                response=cached_response,
                status='cached',
            )
            return Response({'explanation': cached_response, 'cached': True}, status=status.HTTP_200_OK)

        explanation = AIService().explain_word(request.user, word, context, lang_code)
        cache.set(cache_key, explanation, 24 * 60 * 60)

        return Response({'explanation': explanation, 'cached': False}, status=status.HTTP_200_OK)


class GenerateStoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _has_active_pro(request.user):
            return Response(
                {'detail': 'Генерация историй доступна только для Pro подписчиков.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        lang_code = request.data.get('language_code')
        level = request.data.get('level')
        topic = request.data.get('topic')

        if not lang_code or not level or not topic:
            return Response(
                {'detail': 'Поля language_code, level и topic обязательны.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        generate_story_async.delay(
            user_id=request.user.id,
            language_code=lang_code,
            cefr_level=level,
            topic=topic,
        )

        return Response(
            {
                'detail': 'Генерация истории запущена.',
                'status': 'pending',
                'language_code': lang_code,
                'level': level,
                'topic': topic,
            },
            status=status.HTTP_202_ACCEPTED,
        )
