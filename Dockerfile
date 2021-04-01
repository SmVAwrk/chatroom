FROM python:3.8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . /app
EXPOSE 8080

WORKDIR /app

RUN chmod +x entrypoint.sh
RUN pip install -r requirements.txt

WORKDIR /app/chatroom_project