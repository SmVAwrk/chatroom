import logging

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError, ParseError

from chat_app.models import Message, RoomInvite

logger = logging.getLogger(__name__)


def invite_handler(invite):
    """Функция для обработки приглашения в чат-комнату при его изменении."""
    assert isinstance(invite, RoomInvite)

    if invite.is_accepted:
        # Если приглашение принято, то invite_object добавляется к участникам комнаты,
        # и экземпляр приглашения удаляется
        invite.room.members.add(invite.invite_object)
        invite.delete()
    elif invite.is_accepted is False:
        # Если приглашение отклонено, экземпляр приглашения просто удаляется
        invite.delete()


def get_emails(serializer_data):
    """Функция для получения списка email'ов приглашенных пользователей для отправки оповещений."""
    user_model = get_user_model()
    emails = []
    users = []
    for invite in serializer_data:
        users.append(invite['invite_object'])
    users_query = user_model.objects.filter(id__in=users)
    for user in users_query:
        emails.append(user.email)
    return emails


def send_invite_notification(emails, username, room_title):
    """Функция для отправки на почту оповещений о приглашении в комнату."""
    send_mail(
        'Приглашение в комнату',
        'Пользователь {} пригласил вас в комнату {}.'.format(username, room_title),
        'testovicht33@gmail.com',
        emails,
        fail_silently=False
    )


def message_filter(request, room_slug):
    """Функция для фильтрации сообщений через переданные в запросе параметры."""
    try:
        limit = int(request.GET.get('limit'))
        offset = int(request.GET.get('offset'))
    except (ValueError, TypeError) as exc:
        logger.error(f'Ошибка: {exc}; запрос с некорректными параметрами.')
        raise ParseError('Запрос с некорректными параметрами')

    no_more_data = False
    if Message.objects.filter(room__slug=room_slug).count() <= offset + limit:
        no_more_data = True
    return Message.objects.filter(room__slug=room_slug).order_by('-created_at')[offset:offset + limit], no_more_data
