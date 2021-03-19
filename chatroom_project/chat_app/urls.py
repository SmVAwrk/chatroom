from django.urls import path
from rest_framework.routers import SimpleRouter

from chat_app.views import RoomViewSet, InviteView, InviteFromMe, InviteToMe, chat_view

router = SimpleRouter()
router.register('room', RoomViewSet, basename='room')
router.register('invite-from-me', InviteFromMe, basename='invite-from-me')
router.register('invite-to-me', InviteToMe, basename='invite-to-me')


urlpatterns = [
    path('room/<str:room_slug>/invite/', InviteView.as_view()),
    path('room/<str:room_slug>/connect/', chat_view),
]

urlpatterns += router.urls

