import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Notification, PushSubscription
from .serializers import NotificationSerializer, PushSubscriptionSerializer, MarkReadSerializer

logger = logging.getLogger('notifications')


@extend_schema(
    responses={200: NotificationSerializer(many=True)},
    summary='Список уведомлений текущего пользователя',
    tags=['notifications'],
)
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user)

        is_read_param = request.query_params.get('is_read')
        if is_read_param is not None:
            if is_read_param.lower() in ('true', '1'):
                qs = qs.filter(is_read=True)
            elif is_read_param.lower() in ('false', '0'):
                qs = qs.filter(is_read=False)

        serializer = NotificationSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=MarkReadSerializer,
    responses={
        200: OpenApiResponse(description='Уведомление отмечено как прочитанное'),
        400: OpenApiResponse(description='Ошибка валидации'),
        404: OpenApiResponse(description='Уведомление не найдено'),
    },
    summary='Отметить уведомление как прочитанное',
    tags=['notifications'],
)
class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id=None):
        nid = notification_id or request.data.get('notification_id')
        if not nid:
            return Response({'detail': 'notification_id обязателен.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            notification = Notification.objects.get(id=nid, user=request.user)
        except Notification.DoesNotExist:
            return Response({'detail': 'Уведомление не найдено.'}, status=status.HTTP_404_NOT_FOUND)

        if not notification.is_read:
            notification.is_read = True
            from django.utils import timezone
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
            logger.info(f'Уведомление {nid} прочитано: {request.user.email}')

        return Response({'detail': 'Уведомление отмечено как прочитанное.'}, status=status.HTTP_200_OK)

    def post(self, request, notification_id=None):
        return self.patch(request, notification_id)


@extend_schema(
    request=PushSubscriptionSerializer,
    responses={
        201: PushSubscriptionSerializer,
        200: PushSubscriptionSerializer,
        400: OpenApiResponse(description='Ошибка валидации'),
    },
    summary='Зарегистрировать push-подписку (Web Push / Firebase)',
    tags=['notifications'],
)
class RegisterPushTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get('endpoint')
        p256dh_key = request.data.get('p256dh_key', '')
        auth_key = request.data.get('auth_key', '')
        user_agent = request.data.get('user_agent', '')

        if not endpoint:
            return Response({'detail': 'endpoint обязателен.'}, status=status.HTTP_400_BAD_REQUEST)

        subscription, created = PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=endpoint,
            defaults={
                'p256dh_key': p256dh_key,
                'auth_key': auth_key,
                'is_active': True,
                'user_agent': user_agent,
            }
        )

        serializer = PushSubscriptionSerializer(subscription)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        logger.info(f'Push-подписка {"создана" if created else "обновлена"} для {request.user.email}')
        return Response(serializer.data, status=status_code)