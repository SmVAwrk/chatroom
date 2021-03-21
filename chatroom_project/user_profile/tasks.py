from chatroom_project.celery import app
from user_profile.services import send_friend_notification, send_accept_notification


@app.task
def send_friend_notification_task(email, username):
    send_friend_notification(email, username)


@app.task
def send_accept_notification_task(email, username):
    send_accept_notification(email, username)