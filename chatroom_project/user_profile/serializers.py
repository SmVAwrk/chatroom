from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from user_profile.models import UserProfile, FriendshipRelation


class ProfileListSerializer(ModelSerializer):
    """Сериализатор для обработки списка профилей."""
    user_id = ReadOnlyField(source='user.id')

    class Meta:
        model = UserProfile
        fields = ('user_id', 'avatar', 'username',)


class ProfileDetailSerializer(ModelSerializer):
    """Сериализатор для обработки экземпляра профиля."""
    user = ReadOnlyField(source='user.id')
    friends = PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = UserProfile
        exclude = ('id',)


class FriendshipRelationSerializer(ModelSerializer):
    """Сериализатор для обработки экземпляра заявки в друзья."""

    class Meta:
        model = FriendshipRelation
        exclude = ('id',)

    def validate(self, data):
        """Кастомная валидация данных."""

        if data['creator'] == data['friend_object']:
            raise ValidationError('Невозможно отправить запрос самому себе.')
        if data['creator'].profile.friends.filter(id=data['friend_object'].id).select_related('profile'):
            raise ValidationError('Пользователь уже у вас в друзьях.')
        if FriendshipRelation.objects.filter(
                creator__in=[data['creator'], data['friend_object']],
                friend_object__in=[data['creator'], data['friend_object']]
        ).select_related('creator', 'friend_object'):
            raise ValidationError('Отношение уже существует.')
        return data


class FriendshipRelationListSerializer(ModelSerializer):
    """Сериализатор для обработки списка заявок в друзья."""
    creator = ReadOnlyField(source='creator.id')
    friend_object = ReadOnlyField(source='friend_object.id')

    class Meta:
        model = FriendshipRelation
        fields = '__all__'
