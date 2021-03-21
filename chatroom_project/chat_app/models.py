from hashlib import md5

from django.db import models, IntegrityError
from slugify import slugify

from chatroom_project import settings


class Room(models.Model):
    title = models.CharField(max_length=128, verbose_name='Название')
    slug = models.SlugField(max_length=128, verbose_name='URL', unique=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Владелец',
                              on_delete=models.CASCADE, related_name='my_rooms')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='Участники',
                                     blank=True, related_name='rooms')
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Комната {self.owner} со слагом {self.slug}'

    def get_members_num(self):
        return self.members.all().count() + 1

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) + '-' + self.pk
            try:
                super().save(*args, **kwargs)
            except IntegrityError:
                self.slug = md5(bytes(str(self.created_at), encoding='utf8')).hexdigest()
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class Message(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='Автор', related_name='author_messages')
    room = models.ForeignKey(Room, on_delete=models.CASCADE,
                             verbose_name='Комната', related_name='room_messages')
    text = models.TextField(verbose_name='Контент')
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Сообщение {self.author} в комнате {self.room}'


class RoomInvite(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Приглашение от',
                                on_delete=models.CASCADE, related_name='invite_inits')
    invite_object = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Приглашение к',
                                      on_delete=models.CASCADE, related_name='invite_requests')
    room = models.ForeignKey(Room, on_delete=models.CASCADE,
                             verbose_name='Комната', related_name='invites')
    is_accepted = models.BooleanField(verbose_name='Принято', null=True)

    def __str__(self):
        return f'Приглашение {self.invite_object} от {self.creator} в комнату {self.room}'

    class Meta:
        unique_together = ('invite_object', 'room')
