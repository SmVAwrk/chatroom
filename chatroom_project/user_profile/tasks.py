import logging

from chatroom_project.celery import app
from user_profile.services import send_friend_notification, send_accept_notification

logger = logging.getLogger(__name__)


@app.task
def send_friend_notification_task(email, username):
    """Сelery-task для отправки на почту оповещения о добавлении в друзья."""
    logger.debug('Запущен task при добавлении в друзья')
    send_friend_notification(email, username)


@app.task
def send_accept_notification_task(email, username):
    """Сelery-task для отправки на почту оповещения о подтверждении заявки в друзья."""
    logger.debug('Запущен task при подтверждении добавления в друзья')
    send_accept_notification(email, username)
