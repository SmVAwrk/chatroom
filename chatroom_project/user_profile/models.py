import logging
import re

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from chatroom_project import settings

logger = logging.getLogger(__name__)


def upload_to(instance, filename):
    """
    Функция для генерации пути до файла.
    :param instance: объект профиля
    :param filename: имя загружаемого файла
    :return: 'путь_до_файла': str
    """
    return f'avatars/uid-{instance.user.id}/{filename}'


class UserProfile(models.Model):
    """
    Модель профиля пользователя.
    Связь 1 к 1 с моделью пользователя.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name='Пользователь',
                                on_delete=models.CASCADE, related_name='profile')
    username = models.CharField(max_length=128, verbose_name='Никнейм')
    avatar = models.ImageField(upload_to=upload_to, verbose_name='Аватар',
                               blank=True, null=True)
    description = models.TextField(verbose_name='О себе', blank=True)
    first_name = models.CharField(max_length=128, verbose_name='Имя', blank=True)
    last_name = models.CharField(max_length=128, verbose_name='Фамилия', blank=True)
    birth_date = models.DateField(verbose_name='Дата рождения', blank=True, null=True)
    location = models.CharField(max_length=128, verbose_name='Местоположение', blank=True)
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='Друзья', blank=True)

    def __str__(self):
        return 'Профиль ' + self.username


@receiver(signal=post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Сигнал для создания связанного профиля при создании пользователя
    или обновления профиля при обновлении пользователя.
    """
    if created:
        username = re.search(r'^(\w+)@', instance.email)
        UserProfile.objects.create(user=instance, username=username.group(1))
        logger.debug(f'Создание профиля для пользователя {instance.email}')
    instance.profile.save()


class FriendshipRelation(models.Model):
    """Модель заявки на добавление в друзья."""
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Запрос от',
                                on_delete=models.CASCADE, related_name='friend_inits')
    friend_object = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Запрос к',
                                      on_delete=models.CASCADE, related_name='friend_requests')
    is_accepted = models.BooleanField(verbose_name='Принято', null=True)

    def __str__(self):
        return f'Запрос на дружбу от {self.creator} к {self.friend_object}'

    class Meta:
        unique_together = ('creator', 'friend_object')
