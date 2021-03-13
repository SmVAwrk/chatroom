import re

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from chatroom_project import settings


def upload_to(instance, filename):
    return f'avatars/uid-{instance.user.id}/{filename}'


class UserProfile(models.Model):
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
def create_user_profile(sender, instance, created, **kwargs):
    username = re.search(r'^(\w+)@', instance.email)
    if created:
        UserProfile.objects.create(user=instance, username=username.group(1))


@receiver(signal=post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class FriendshipRelation(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Запрос от',
                                on_delete=models.CASCADE, related_name='friend_inits')
    friend_object = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Запрос к',
                                      on_delete=models.CASCADE, related_name='friend_requests')
    is_accepted = models.BooleanField(verbose_name='Принято', null=True)

    def __str__(self):
        return f'Запрос на дружбу от {self.creator} к {self.friend_object}'

    class Meta:
        unique_together = ('creator', 'friend_object')
