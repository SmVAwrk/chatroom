from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from user_profile.models import FriendshipRelation


def friend_request_validation(request_user, user):
    _ = None
    if request_user.id == int(user):
        return Response({'message': 'невозможно отправить запрос самому себе'}, status=status.HTTP_400_BAD_REQUEST), _
    user_model = get_user_model()
    user_obj = get_object_or_404(user_model, id=user)
    if request_user.profile.friends.filter(id=int(user)).select_related('profile'):
        return Response({'message': 'пользователь уже у вас в друзьях'}, status=status.HTTP_400_BAD_REQUEST), _
    if FriendshipRelation.objects.filter(
            creator__in=[request_user, user_obj],
            friend_object__in=[request_user, user_obj]
    ).select_related('creator', 'friend_object'):
        return Response({'message': 'отношение уже существует'}, status=status.HTTP_400_BAD_REQUEST), _
    return _, user_obj


def friend_request_handler(friend_request):
    if friend_request.is_accepted:
        friend_request.friend_object.profile.friends.add(friend_request.creator)
        friend_request.creator.profile.friends.add(friend_request.friend_object)
        friend_request.delete()
    elif friend_request.is_accepted is False:
        friend_request.delete()


def friend_delete_validation(request_user, user):
    _ = None
    user_model = get_user_model()
    user_obj = get_object_or_404(user_model, id=user)
    if not request_user.profile.friends.filter(id=int(user)).select_related('profile'):
        return Response({'message': 'пользователя нет у вас в друзьях'}, status=status.HTTP_400_BAD_REQUEST), _

    return _, user_obj


def friend_delete_handler(request_user, user_obj):
    request_user.profile.friends.remove(user_obj)
    user_obj.profile.friends.remove(request_user)



