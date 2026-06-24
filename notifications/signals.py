import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification

logger = logging.getLogger('notifications')


@receiver(post_save, sender=Notification)
def push_notification_to_websocket(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{instance.user.id}',
            {
                'type': 'send_notification',
                'id': str(instance.id),
                'notification_type': instance.notification_type,
                'title': instance.title,
                'body': instance.body,
                'created_at': instance.created_at.isoformat(),
            }
        )
        logger.info(f'Уведомление отправлено: {instance.user.email} — {instance.notification_type}')
    except Exception as e:
        logger.error(f'Ошибка push уведомления для {instance.user.email}: {e}', exc_info=True)