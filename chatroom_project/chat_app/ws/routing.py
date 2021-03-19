from django.urls import path

from chat_app.ws import consumers

websocket_urlpatterns = [
    path('ws/chat/room/<str:room_slug>/', consumers.AsyncAPIChatConsumer.as_asgi()),
]
