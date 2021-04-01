import json

import pytest
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.urls import path

from chat_app.models import Room, Message
from chat_app.ws.consumers import AsyncChatConsumer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_connect_async_chat_consumer(django_user_model):
    user = await database_sync_to_async(django_user_model.objects.create)(email='user1@test.com')
    room = await database_sync_to_async(Room.objects.create)(owner=user, title='test-room', slug='test-slug')
    application = AuthMiddlewareStack(URLRouter([
        path('ws/chat/room/<str:room_slug>/', AsyncChatConsumer.as_asgi()),
    ]))
    communicator = WebsocketCommunicator(application, f"/ws/chat/room/{room.slug}/")
    communicator.scope['user'] = user

    connected, subprotocol = await communicator.connect()
    assert connected

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_chat_consumer_get_room_messages(django_user_model):
    user = await database_sync_to_async(django_user_model.objects.create)(email='user1@test.com')
    room = await database_sync_to_async(Room.objects.create)(owner=user, title='test-room', slug='test-slug')
    await database_sync_to_async(Message.objects.create)(author=user, text='test text', room=room)
    application = AuthMiddlewareStack(URLRouter([
        path('ws/chat/room/<str:room_slug>/', AsyncChatConsumer.as_asgi()),
    ]))
    communicator = WebsocketCommunicator(application, f"/ws/chat/room/{room.slug}/")
    communicator.scope['user'] = user
    await communicator.connect()

    json_messages = await communicator.receive_from()
    messages = json.loads(json_messages)
    assert messages[0]["text"] == 'test text'

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_chat_consumer_get_room_online_users(django_user_model):
    user = await database_sync_to_async(django_user_model.objects.create)(email='user1@test.com')
    room = await database_sync_to_async(Room.objects.create)(owner=user, title='test-room', slug='test-slug')
    application = AuthMiddlewareStack(URLRouter([
        path('ws/chat/room/<str:room_slug>/', AsyncChatConsumer.as_asgi()),
    ]))
    communicator = WebsocketCommunicator(application, f"/ws/chat/room/{room.slug}/")
    communicator.scope['user'] = user
    await communicator.connect()

    # Получение сообщений комнаты
    await communicator.receive_from()

    json_online_users = await communicator.receive_from()
    online_users = json.loads(json_online_users)
    assert online_users['currently_online'] == 1
    assert online_users['User'][0] == str(user.id)

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_chat_consumer_receive(django_user_model):
    user = await database_sync_to_async(django_user_model.objects.create)(email='user1@test.com')
    room = await database_sync_to_async(Room.objects.create)(owner=user, title='test-room', slug='test-slug')
    application = AuthMiddlewareStack(URLRouter([
        path('ws/chat/room/<str:room_slug>/', AsyncChatConsumer.as_asgi()),
    ]))
    communicator = WebsocketCommunicator(application, f"/ws/chat/room/{room.slug}/")
    communicator.scope['user'] = user
    await communicator.connect()

    # Получение сообщений комнаты
    await communicator.receive_from()

    # Получение пользователей онлайн при подключении
    await communicator.receive_from()

    await communicator.send_json_to({'author': user.id, 'message': 'test message'})

    json_message = await communicator.receive_from()
    message = json.loads(json_message)
    assert message['author'] == user.id
    assert message['text'] == 'test message'

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_chat_consumer_get_room_online_users_with_another_connect(django_user_model):
    user = await database_sync_to_async(django_user_model.objects.create)(email='user1@test.com')
    user2 = await database_sync_to_async(django_user_model.objects.create)(email='user2@test.com')
    room = await database_sync_to_async(Room.objects.create)(owner=user, title='test-room', slug='test-slug')
    await database_sync_to_async(room.members.add)(user2)
    application = AuthMiddlewareStack(URLRouter([
        path('ws/chat/room/<str:room_slug>/', AsyncChatConsumer.as_asgi()),
    ]))
    communicator1 = WebsocketCommunicator(application, f"/ws/chat/room/{room.slug}/")
    communicator1.scope['user'] = user
    await communicator1.connect()

    # Получение сообщений комнаты
    await communicator1.receive_from()

    # Получение пользователей онлайн при подключении
    await communicator1.receive_from()

    communicator2 = WebsocketCommunicator(application, f"/ws/chat/room/{room.slug}/")
    communicator2.scope['user'] = user2
    await communicator2.connect()

    json_online_users = await communicator1.receive_from()
    online_users = json.loads(json_online_users)
    assert online_users['currently_online'] == 2
    assert all(user in online_users['User'] for user in [str(user2.id), str(user.id)])

    await communicator1.disconnect()
    await communicator2.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_chat_consumer_get_room_online_users_with_another_disconnect(django_user_model):
    user = await database_sync_to_async(django_user_model.objects.create)(email='user1@test.com')
    user2 = await database_sync_to_async(django_user_model.objects.create)(email='user2@test.com')
    room = await database_sync_to_async(Room.objects.create)(owner=user, title='test-room', slug='test-slug')
    await database_sync_to_async(room.members.add)(user2)
    application = AuthMiddlewareStack(URLRouter([
        path('ws/chat/room/<str:room_slug>/', AsyncChatConsumer.as_asgi()),
    ]))
    communicator1 = WebsocketCommunicator(application, f"/ws/chat/room/{room.slug}/")
    communicator1.scope['user'] = user
    await communicator1.connect()

    # Получение сообщений комнаты
    await communicator1.receive_from()

    # Получение пользователей онлайн при подключении
    await communicator1.receive_from()

    communicator2 = WebsocketCommunicator(application, f"/ws/chat/room/{room.slug}/")
    communicator2.scope['user'] = user2
    await communicator2.connect()

    # Получение пользователей онлайн при подключении нового пользователя
    await communicator1.receive_from()

    await communicator2.disconnect()

    json_online_users = await communicator1.receive_from()
    online_users = json.loads(json_online_users)
    assert online_users['currently_online'] == 1
    assert online_users['User'] == [str(user.id), ]

    await communicator1.disconnect()
