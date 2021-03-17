from django.urls import re_path, path

from chat_app import consumers

websocket_urlpatterns = [
    path('ws/chat/room/<str:room_slug>/', consumers.APIChatConsumer.as_asgi()),
]
