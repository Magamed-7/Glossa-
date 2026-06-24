import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger('notifications')


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f'notifications_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f'Уведомления WS подключён: {self.user.email}')

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f'Уведомления WS отключён: {self.user.email} | код {close_code}')
        except Exception as e:
            logger.error(f'Ошибка отключения уведомлений WS {self.user.email}: {e}', exc_info=True)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'mark_read':
                await self.handle_mark_read(data)
            else:
                logger.error(f'Неизвестный action от {self.user.email}: {action}', exc_info=True)

        except json.JSONDecodeError as e:
            logger.error(f'Невалидный JSON от {self.user.email}: {e}', exc_info=True)
        except Exception as e:
            logger.error(f'Ошибка в receive уведомлений {self.user.email}: {e}', exc_info=True)

    async def handle_mark_read(self, data):
        try:
            notification_id = data.get('notification_id')
            await self.mark_notification_read(notification_id)
            await self.send(text_data=json.dumps({
                'action': 'marked_read',
                'notification_id': notification_id,
            }))
        except Exception as e:
            logger.error(f'Ошибка mark_read от {self.user.email}: {e}', exc_info=True)

    async def send_notification(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.error(f'Ошибка отправки уведомления {self.user.email}: {e}', exc_info=True)

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            from .models import Notification
            Notification.objects.filter(
                id=notification_id,
                user=self.user
            ).update(is_read=True, read_at=timezone.now())
        except Exception as e:
            logger.error(f'Ошибка mark_notification_read: {e}', exc_info=True)