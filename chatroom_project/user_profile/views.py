from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter

from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from user_profile.models import UserProfile, FriendshipRelation
from user_profile.permissions import IsOwnerOrAdmin
from user_profile.serializers import (
    ProfileListSerializer, ProfileDetailSerializer,
    FriendshipRelationSerializer, FriendshipRelationListSerializer
)
from user_profile.services import (
    friend_request_validation, friend_request_handler,
    friend_delete_validation, friend_delete_handler
)
from user_profile.tasks import send_friend_notification_task


class ProfileUserViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.ListModelMixin,
                         GenericViewSet):
    queryset = UserProfile.objects.all().order_by('username').select_related('user')
    lookup_field = 'user'
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    filter_backends = [SearchFilter, ]
    search_fields = ['username', ]

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            return (IsOwnerOrAdmin(),)
        return (IsAuthenticated(),)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProfileListSerializer
        return ProfileDetailSerializer

    @action(
        detail=True,
        url_path='friend-add',
        methods=('post',),
    )
    def add_friend(self, request, user=None):
        not_valid, user_obj = friend_request_validation(request.user, user)
        if not_valid:
            return not_valid

        fs_obj = FriendshipRelation.objects.create(creator=request.user, friend_object=user_obj)
        serializer = FriendshipRelationSerializer(fs_obj)

        send_friend_notification_task.delay(user_obj.email, request.user.profile.username)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        url_path='friend-del',
        methods=('delete',),
    )
    def delete_friend(self, request, user=None):
        not_valid, user_obj = friend_delete_validation(request.user, user)
        if not_valid:
            return not_valid

        friend_delete_handler(request.user, user_obj)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FriendshipRelationFromMeViewSet(mixins.DestroyModelMixin,
                                      mixins.ListModelMixin,
                                      GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = FriendshipRelationListSerializer

    def get_queryset(self):
        return FriendshipRelation.objects.filter(
            creator=self.request.user
        ).order_by('-id').select_related('creator', 'friend_object')


class FriendshipRelationToMeViewSet(mixins.UpdateModelMixin,
                                    mixins.ListModelMixin,
                                    GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = FriendshipRelationListSerializer

    def get_queryset(self):
        return FriendshipRelation.objects.filter(
            friend_object=self.request.user
        ).order_by('-id').select_related('creator', 'friend_object')

    def perform_update(self, serializer):
        serializer.save()
        friend_request = self.get_object()
        friend_request_handler(friend_request)

