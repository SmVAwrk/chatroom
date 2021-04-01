from django.urls import path
from rest_framework.routers import SimpleRouter

from chat_app.views import RoomViewSet, InviteView, InviteFromMeView, InviteToMeView, LazyLoadMessagesView, chat_view

router = SimpleRouter()
router.register('room', RoomViewSet, basename='room')
router.register('invite-from-me', InviteFromMeView, basename='invite-from-me')
router.register('invite-to-me', InviteToMeView, basename='invite-to-me')


urlpatterns = [
    path('room/<str:room_slug>/invite/', InviteView.as_view(), name='room-invite'),
    path('room/<str:room_slug>/messages/', LazyLoadMessagesView.as_view(), name='room-messages'),

    # Роут для отладки WS
    path('room/<str:room_slug>/connect/', chat_view),
]

urlpatterns += router.urls

