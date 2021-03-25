from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from user_profile.models import FriendshipRelation


def send_friend_notification(email, username):
    """Функция для отправки сообщения пользователю при добавлении его в друзья."""
    send_mail(
        'Заявка в друзья',
        'Пользователь {} хочет добавить вас в друзья'.format(username),
        'testovicht33@gmail.com',
        [email, ],
        fail_silently=False
    )


def send_accept_notification(email, username):
    """Функция для отправки сообщения пользователю при подтверждении заявки."""
    send_mail(
        'Подтверждение добавления в друзья',
        'Пользователь {} принял ваш запрос дружбы'.format(username),
        'testovicht33@gmail.com',
        [email, ],
        fail_silently=False
    )


def friend_request_handler(friend_request):
    """Функция для обработки запроса в друзья при его изменении."""
    from user_profile.tasks import send_accept_notification_task

    assert isinstance(friend_request, FriendshipRelation)

    if friend_request.is_accepted:
        # Если запрос принят, то пользователи добавляются друг другу в друзья,
        # и экземпляр запроса удаляется
        friend_request.friend_object.profile.friends.add(friend_request.creator)
        friend_request.creator.profile.friends.add(friend_request.friend_object)

        # Отправка оповещения на почту
        # send_accept_notification_task.delay(friend_request.creator.email, friend_request.friend_object.profile.username)
        friend_request.delete()
    elif friend_request.is_accepted is False:
        # Если запрос отклонен, экземпляр запроса просто удаляется
        friend_request.delete()


def friend_delete_validation(request_user, user):
    """
    Функция для валидации данных при удалении друга.
    :param request_user: объект пользователя, сделавшего запрос
    :param user: id: int удаляемого друга
    :return: При невалидных данных возвращает кортеж: (объект Response c кодом 400 , None),
    в противном случае - кортеж: (None, объект удаляемого из друзей пользователя).
    """
    _ = None
    user_model = get_user_model()
    user_obj = get_object_or_404(user_model, id=user)
    if not request_user.profile.friends.filter(id=user).select_related('profile'):
        return Response({'message': 'пользователя нет у вас в друзьях'}, status=status.HTTP_400_BAD_REQUEST), _

    return _, user_obj


def friend_delete_handler(request_user, user_obj):
    """Функция для обработки запроса на удаление друга."""
    request_user.profile.friends.remove(user_obj)
    user_obj.profile.friends.remove(request_user)


