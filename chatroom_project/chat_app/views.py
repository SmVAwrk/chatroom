from django.db.models import Q
from django.shortcuts import render
from rest_framework import mixins, status
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from chat_app.models import Room, RoomInvite
from chat_app.permissions import IsOwnerOrAdmin, IsOwnerOrMember
from chat_app.serializers import (
    RoomListSerializer, RoomDetailSerializer,
    InviteSerializer, InviteToMeSerializer,
    MessageSerializer
)
from chat_app.services import invite_handler, get_emails, message_filter
from chat_app.tasks import send_invite_notification_task


class RoomViewSet(ModelViewSet):
    """
    Набор представлений для просмотра списка своих чат-комнат,
    просмотра экземпляра чат-комнаты, создания, изменения или удаления.
    Возможен поиск профиля по полям 'title' и 'slug'.
    """
    lookup_field = 'slug'
    filter_backends = [SearchFilter, ]
    search_fields = ['title', 'slug']

    def get_serializer_class(self):
        if self.action == 'list':
            return RoomListSerializer
        return RoomDetailSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return (IsAuthenticated(),)
        return (IsOwnerOrAdmin(),)

    def get_queryset(self):
        return Room.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).order_by('-created_at').distinct().select_related('owner').prefetch_related('members')

    def perform_create(self, serializer):
        """Сохранение пользователя как как владельца комнаты."""
        serializer.save(owner=self.request.user)


class InviteView(APIView):
    """Представление-класс для создания приглашений в комнату."""

    permission_classes = (IsOwnerOrAdmin,)

    def post(self, request, room_slug):
        """Функция обработки POST-запроса."""
        room = get_object_or_404(Room, slug=room_slug)
        self.check_object_permissions(request, room)
        serializer = InviteSerializer(data=request.data, context={'room': room}, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(room=room, creator=request.user)

        # Отправка оповещений на почту
        emails = get_emails(serializer.data)
        # send_invite_notification_task.delay(emails, request.user.profile.username, room.title)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InviteFromMeView(mixins.ListModelMixin,
                       mixins.DestroyModelMixin,
                       GenericViewSet):
    """Набор представлений для просмотра исходящих приглашений."""
    permission_classes = (IsAuthenticated,)
    serializer_class = InviteSerializer

    def get_queryset(self):
        return RoomInvite.objects.filter(creator=self.request.user).order_by('-id').select_related('creator', 'room')


class InviteToMeView(mixins.ListModelMixin,
                     mixins.UpdateModelMixin,
                     GenericViewSet):
    """Набор представлений для просмотра входящих приглашений."""
    permission_classes = (IsAuthenticated,)
    serializer_class = InviteToMeSerializer

    def perform_update(self, serializer):
        """Обработка приглашения при его обновлении."""
        serializer.save()
        invite = self.get_object()
        invite_handler(invite)

    def get_queryset(self):
        return RoomInvite.objects.filter(
            invite_object=self.request.user
        ).order_by('-id').select_related('invite_object', 'room')


class LazyLoadMessagesView(APIView):
    """Представление для ленивой загрузки сообщений."""
    permission_classes = (IsOwnerOrMember,)

    def get(self, request, room_slug):
        """Функция обработки GET-запроса LazyLoad."""
        room = get_object_or_404(Room, slug=room_slug)
        self.check_object_permissions(request, room)

        messages, no_more_data = message_filter(request, room_slug)
        serializer = MessageSerializer(messages, many=True)
        return Response(
            {
                'messages': serializer.data,
                'no_more_data': no_more_data
            },
            status=status.HTTP_200_OK
        )

def chat_view(request, room_slug):
    """Представление-функция для отладки WS."""
    return render(request, 'chat_app/my_chat.html', context={
        'room_slug': room_slug
    })
