from chat_app.services import send_invite_notification
from chatroom_project.celery import app


@app.task
def send_invite_notification_task(emails, username, room_name):
    send_invite_notification(emails, username, room_name)
