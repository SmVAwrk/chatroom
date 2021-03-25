import logging

from chat_app.services import send_invite_notification
from chatroom_project.celery import app

logger = logging.getLogger(__name__)


@app.task
def send_invite_notification_task(emails, username, room_name):
    """Сelery-task для отправки на почту оповещений о приглашении в комнату."""
    logger.debug('Запущен task при приглашении в комнату')
    send_invite_notification(emails, username, room_name)
