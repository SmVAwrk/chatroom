import json
import logging

import redis
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer

from chat_app.models import Message, Room
from chat_app.serializers import MessageSerializer
from chatroom_project.settings import REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)


class AsyncChatConsumer(AsyncWebsocketConsumer):
    """Async Consumer для обработки WS-соединения."""
    session_storage = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

    # session_storage.delete('users_test-slug')

    async def connect(self):
        """Функция-обработчик соединения."""
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        try:
            # Пытаемся получить комнату
            self.room = await self.get_room()
        except Exception as exc:
            # Закрываем соединение, если возникли ошибки
            logger.error(f'Exception: {exc}, ошибка при получении комнаты в WS.')
            await self.close()

        # Проверяем является ли пользователь участником комнаты
        if not await self.is_room_member():
            raise StopConsumer()

        # Добавляем пользователя к группе комнаты
        self.room_group_name = 'chat_{}'.format(self.room_slug)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Принимаем соединение
        await self.accept()

        # Добавляем пользователя в хранилище для отслеживания подключенных пользователей
        await self.redis_add_user()

        # Отправляем подключенному пользователю прошлые сообщения комнаты
        await self.send(json.dumps(await self.get_messages()))

        # Отправляем всем пользователям в группе новый онлайн
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_counter',
                'online': len(await self.get_online_users()),
                'users': await self.get_online_users()
            }
        )

    async def disconnect(self, close_code):
        """Функция-обработчик разрыва-соединения."""

        # Удаляем пользователя из временного хранилища
        await self.redis_del_user()

        # Отправляем всем пользователям в группе новый онлайн
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_counter',
                'online': len(await self.get_online_users()),
                'users': await self.get_online_users()
            }
        )

        # Удаляем пользователя из группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.debug(f"Все удалили {self.scope['user']}")

    async def receive(self, text_data):
        """Функция для обработки принятого сигнала."""

        # Обработка полученных данных
        text_data_json = json.loads(text_data)
        author = text_data_json.get('author', None)
        message = text_data_json['message']

        # Создание экземпляра сообщения в БД
        await self.create_message(message)

        # Отправка сообщения всем пользователям в группе
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'author': author,
                'message': message
            }
        )

    async def chat_message(self, event):
        """Функция отправки сообщения."""
        author = event['author']
        message = event['message']

        await self.send(text_data=json.dumps({
            'author': author,
            'text': message
        }))

    async def user_counter(self, event):
        """Функция отправки онлайн пользователей."""
        online = event['online']
        users = event['users']

        await self.send(text_data=json.dumps({
            'currently_online': online,
            'User': users
        }))

    # Синхронные вспомогательные функции:

    @database_sync_to_async
    def get_room(self):
        return Room.objects.get(slug=self.room_slug)

    @sync_to_async
    def is_room_member(self):
        return bool(self.scope['user'] == self.room.owner or self.scope['user'] in self.room.members.all())

    @database_sync_to_async
    def create_message(self, message):
        Message.objects.create(author=self.scope["user"], room=self.room, text=message)

    @sync_to_async
    def get_username(self):
        return self.scope["user"].profile.username

    @sync_to_async
    def redis_add_user(self):
        self.session_storage.sadd(f'users_{self.room_slug}', self.scope["user"].profile.id)

    @sync_to_async
    def redis_del_user(self):
        self.session_storage.srem(f'users_{self.room_slug}', self.scope["user"].profile.id)

    @sync_to_async
    def get_messages(self):
        messages = self.room.room_messages.order_by('-created_at')[:25]
        serializer = MessageSerializer(messages, many=True)
        return serializer.data

    @sync_to_async
    def get_online_users(self):
        users = list(self.session_storage.smembers(f'users_{self.room_slug}'))
        return users
