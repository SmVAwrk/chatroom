import logging
import re

from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField, SlugField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer, ListSerializer

from chat_app.models import Room, RoomInvite, Message


logger = logging.getLogger(__name__)

class RoomListSerializer(ModelSerializer):
    """Сериализатор для обработки списка чат-комнат"""
    members_num = ReadOnlyField(source='get_members_num')

    class Meta:
        model = Room
        fields = ('title', 'slug', 'owner', 'members_num', 'members')


class RoomDetailSerializer(ModelSerializer):
    """Сериализатор для обработки экземпляра чат-комнаты"""
    owner = PrimaryKeyRelatedField(read_only=True)
    members_num = ReadOnlyField(source='get_members_num')
    slug = SlugField(allow_blank=True, required=False)

    class Meta:
        model = Room
        fields = ('title', 'slug', 'owner', 'created_at', 'members_num', 'members')

    def validate_slug(self, value):
        """Валидация поля slug."""
        if re.search(r'[-|_][i|I][d|D]\d+$', value):
            logger.debug(f'Пользователь {self.instance.owner} попытался создать зарезервированный slug.')
            raise ValidationError('Такой тип окончания в поле slug зарезервирован.')
        return value

    def validate(self, data):
        """Валидация входных данных."""
        if data.get('members'):
            members_before = {user.id for user in self.instance.members.all()}
            members_after = {user.id for user in data['members']}
            if not members_after.issubset(members_before):
                raise ValidationError('Вы можете только удалять участников комнаты.')
        return data


class InviteListSerializer(ListSerializer):
    """Сериализатор для обработки списка приглашений."""

    def create(self, validated_data):
        invites = [RoomInvite(**item) for item in validated_data]
        return RoomInvite.objects.bulk_create(invites)


class InviteSerializer(ModelSerializer):
    """Сериализатор для обработки приглашений."""
    creator = ReadOnlyField(source='creator.id')
    room = ReadOnlyField(source='room.slug')

    class Meta:
        model = RoomInvite
        list_serializer_class = InviteListSerializer
        fields = '__all__'

    def validate(self, data):
        """Валидация входных данных."""
        room = self.context['room']
        if data['invite_object'] in room.members.all() or data['invite_object'] == room.owner:
            raise ValidationError(f'Пользователь {data["invite_object"]} уже числится в комнате {room.slug}.')
        if RoomInvite.objects.filter(invite_object=data['invite_object'], room=room):
            raise ValidationError(f'Пользователь {data["invite_object"]} уже приглашен в комнату {room.slug}.')
        return data


class InviteToMeSerializer(ModelSerializer):
    """Сериализатор для обработки входящих приглашений."""
    creator = ReadOnlyField(source='creator.id')
    room = ReadOnlyField(source='room.slug')
    invite_object = ReadOnlyField(source='invite_object.id')

    class Meta:
        model = RoomInvite
        fields = '__all__'


class MessageSerializer(ModelSerializer):
    """Сериализатор для обработки сообщений."""
    room = ReadOnlyField(source='room.slug')

    class Meta:
        model = Message
        exclude = ('id', )
