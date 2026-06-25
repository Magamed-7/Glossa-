import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger('duels')


class DuelConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.duel_id = self.scope['url_route']['kwargs']['duel_id']
        self.room_group_name = f'duel_{self.duel_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info(f'WebSocket подключён: {self.user.email} | дуэль {self.duel_id}')

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            logger.info(f'WebSocket отключён: {self.user.email} | дуэль {self.duel_id} | код {close_code}')
        except Exception as e:
            logger.error(f'Ошибка при отключении WebSocket {self.user.email}: {e}', exc_info=True)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'submit_answer':
                await self.handle_answer(data)
            elif action == 'player_ready':
                await self.handle_ready(data)
            else:
                logger.error(f'Неизвестный action от {self.user.email}: {action}',exc_info=True)

        except json.JSONDecodeError as e:
            logger.error(f'Невалидный JSON от {self.user.email}: {e}', exc_info=True)
        except Exception as e:
            logger.error(f'Ошибка в receive от {self.user.email}: {e}', exc_info=True)

    async def handle_answer(self, data):
        try:
            round_id = data.get('round_id')
            answer = data.get('answer', '').strip()
            elapsed_time = data.get('elapsed_time')

            is_correct = await self.save_answer(round_id, answer, elapsed_time)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'duel_message',
                    'action': 'answer_received',
                    'player_id': str(self.user.id),
                    'round_id': round_id,
                    'is_correct': is_correct,
                }
            )
            logger.info(f'{self.user.email} ответил на раунд {round_id} | верно: {is_correct}')
        except Exception as e:
            logger.error(f'Ошибка handle_answer от {self.user.email}: {e}',exc_info=True)

    async def handle_ready(self, data):
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'duel_message',
                    'action': 'player_ready',
                    'player_id': str(self.user.id),
                }
            )
        except Exception as e:
            logger.error(f'Ошибка handle_ready от {self.user.email}: {e}', exc_info=True)

    async def duel_message(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.error(f'Ошибка отправки сообщения игроку {self.user.email}: {e}', exc_info=True)

    @database_sync_to_async
    def save_answer(self, round_id, answer, elapsed_time):
        try:
            from .models import DuelRound
            round_obj = DuelRound.objects.get(id=round_id, duel__id=self.duel_id)
            duel = round_obj.duel

            if duel.player_one == self.user:
                round_obj.answer_player_one = answer
                round_obj.time_player_one = elapsed_time
            elif duel.player_two == self.user:
                round_obj.answer_player_two = answer
                round_obj.time_player_two = elapsed_time

            is_correct = answer.lower() == round_obj.correct_answer.lower()

            both_answered = round_obj.answer_player_one and round_obj.answer_player_two
            if both_answered:
                round_obj.finished_at = timezone.now()

            round_obj.save()
            return is_correct
        except Exception as e:
            logger.error(f'Ошибка save_answer раунд {round_id}: {e}', exc_info=True)
            return False