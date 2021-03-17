from django.urls import path
from rest_framework.routers import SimpleRouter

from chat_app.views import index, room, RoomViewSet, InviteView, InviteFromMe, InviteToMe, my_chat_api

router = SimpleRouter()
router.register('room', RoomViewSet, basename='room')
router.register('invite-from-me', InviteFromMe, basename='invite-from-me')
router.register('invite-to-me', InviteToMe, basename='invite-to-me')


urlpatterns = [
    path('room/<str:room_slug>/invite/', InviteView.as_view()),
    path('room/<str:room_slug>/connect/', my_chat_api),
]

urlpatterns += router.urls

