#!/bin/bash

python manage.py collectstatic
python manage.py makemigrations custom_user user_profile chat_app
python manage.py migrate
python manage.py createsuperuser --noinput
daphne -b 0.0.0.0 -p 8080 chatroom_project.asgi:application