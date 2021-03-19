import json

import redis
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer, DenyConnection, AcceptConnection
from channels.generic.websocket import AsyncWebsocketConsumer

from chat_app.models import Message, Room
from chat_app.serializers import MessageSerializer


class AsyncAPIChatConsumer(AsyncWebsocketConsumer):
    session_storage = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    # session_storage.delete('user_room-title-1')

    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        try:
            self.room = await self.get_room()
        except Exception:
            await self.close()

        if not await self.is_room_member():
            raise StopConsumer()


        self.room_group_name = 'chat_{}'.format(self.room_slug)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print('Приняли соединение')

        await self.redis_add_user()
        print('Добавили пользователя в редис')

        print('Отправляем сообщения')
        try:
            await self.send(json.dumps(await self.get_messages()))
        except Exception as exc:
            print(exc)
        print('Отправили сообщение')

        print('Обновляем счётчик')
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_counter',
                    'online': len(await self.get_online_users()),
                    'users': await self.get_online_users()
                }
            )
        except Exception as exc:
            print(exc)
        print('Обновили счётчик')

    async def disconnect(self, close_code):
        print('Зашли в дисконнект')

        await self.redis_del_user()
        print('Удалили пользователя')

        try:
            print('Обновляем счётчик')
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_counter',
                    'online': len(await self.get_online_users()),
                    'users': await self.get_online_users()
                }
            )
            print('Обновили счётчик')
        except Exception as exc:
            print(exc)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        author = text_data_json.get('author', None)
        message = text_data_json['message']

        print(text_data_json)
        print(self.scope)
        print('Приняли сообщение')
        # try:
        #     await self.create_message(message)
        #     print('Создали сообщение')
        # except Exception as exc:
        #     print(exc)
        #     await self.send(json.dumps({'message': 'something wrong'}))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'author': author,
                'message': message
            }
        )

    async def chat_message(self, event):
        print('Зашли в сообщение')
        author = event['author']
        message = event['message']

        await self.send(text_data=json.dumps({
            'author': author,
            'text': message
        }))
        print('Вышли из сообщение')

    async def user_counter(self, event):
        print('Зашли в счётчика')
        online = event['online']
        users = event['users']

        await self.send(text_data=json.dumps({
            'currently_online': online,
            'User': users
        }))
        print('Вышли из счётчика')

    @database_sync_to_async
    def get_room(self):
        print('Зашли в получение комнаты')
        return Room.objects.get(slug=self.room_slug)

    @sync_to_async
    def is_room_member(self):
        print(self.scope['user'])
        print(self.room.owner)
        print(self.room.members.all())
        return bool(self.scope['user'] == self.room.owner or self.scope['user'] in self.room.members.all())

    @database_sync_to_async
    def create_message(self, message):
        Message.objects.create(author=self.scope["user"], room=self.room, text=message)

    @sync_to_async
    def get_username(self):
        print('Зашли в получение юзернейма')
        return self.scope["user"].profile.username

    @sync_to_async
    def redis_add_user(self):
        print('Зашли в добавление пользователя в редис')
        self.session_storage.sadd(f'users_{self.room_slug}', self.scope["user"].profile.id)
        print('Вышли из добавление пользователя в редис')

    @sync_to_async
    def redis_del_user(self):
        print('Зашли в удаление пользователя в редис')
        self.session_storage.srem(f'users_{self.room_slug}', self.scope["user"].profile.id)
        print('Вышли из удаление пользователя в редис')

    @sync_to_async
    def get_messages(self):
        print('Зашли в получение сообщений')
        messages = self.room.room_messages.order_by('-created_at')[:25]
        serializer = MessageSerializer(messages, many=True)
        print('Вышли из получение сообщений')
        return serializer.data

    @sync_to_async
    def get_online_users(self):
        print('Зашли в получение пользователей в редис')
        users = list(self.session_storage.smembers(f'users_{self.room_slug}'))
        print('Вышли из получение пользователей в редис')
        return users
