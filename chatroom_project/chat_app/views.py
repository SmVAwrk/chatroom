from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from rest_framework import mixins, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from chat_app.models import Room, RoomInvite
from chat_app.permissions import IsOwnerOrAdmin
from chat_app.serializers import RoomListSerializer, RoomDetailSerializer, InviteSerializer, InviteToMeSerializer
from chat_app.services import invite_handler


def chat_view(request, room_slug):
    return render(request, 'chat_app/my_chat_api.html', context={
        'room_slug': room_slug
    })


class RoomViewSet(ModelViewSet):
    lookup_field = 'slug'
    filter_backends = [SearchFilter, ]
    search_fields = ['title', 'slug']

    def get_serializer_class(self):
        if self.action == 'list':
            return RoomListSerializer
        return RoomDetailSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (IsAuthenticated(),)
        return (IsOwnerOrAdmin(),)

    def get_queryset(self):
        return Room.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).order_by('-created_at').distinct().select_related('owner').prefetch_related('members')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class InviteView(APIView):

    def post(self, request, room_slug):
        room = get_object_or_404(Room, slug=room_slug)
        serializer = InviteSerializer(data=request.data, context={'room': room}, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(room=room, creator=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InviteFromMe(mixins.ListModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = InviteSerializer

    def get_queryset(self):
        return RoomInvite.objects.filter(creator=self.request.user).order_by('-id').select_related('creator')


class InviteToMe(mixins.ListModelMixin,
                 mixins.UpdateModelMixin,
                 GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = InviteToMeSerializer

    def perform_update(self, serializer):
        serializer.save()
        invite = self.get_object()
        invite_handler(invite)

    def get_queryset(self):
        return RoomInvite.objects.filter(
            invite_object=self.request.user
        ).order_by('-id').select_related('invite_object')
