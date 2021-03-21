from django.contrib.auth import get_user_model
from django.core.mail import send_mail


def invite_handler(invite):
    if invite.is_accepted:
        invite.room.members.add(invite.invite_object)
        invite.delete()
    elif invite.is_accepted is False:
        invite.delete()


def get_emails(serializer_data):
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
    send_mail(
        'Приглашение в комнату',
        'Пользователь {} пригласил вас в комнату {}.'.format(username, room_title),
        'testovicht33@gmail.com',
        emails,
        fail_silently=False
    )
