from rest_framework.fields import ReadOnlyField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from user_profile.models import UserProfile, FriendshipRelation


class ProfileListSerializer(ModelSerializer):
    user_id = ReadOnlyField(source='user.id')

    class Meta:
        model = UserProfile
        fields = ('user_id', 'avatar', 'username',)


class ProfileDetailSerializer(ModelSerializer):
    user = ReadOnlyField(source='user.id')
    friends = PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = UserProfile
        exclude = ('id',)


class FriendshipRelationSerializer(ModelSerializer):

    class Meta:
        model = FriendshipRelation
        exclude = ('id',)


class FriendshipRelationListSerializer(ModelSerializer):
    creator = ReadOnlyField(source='creator.id')
    friend_object = ReadOnlyField(source='friend_object.id')

    class Meta:
        model = FriendshipRelation
        fields = '__all__'
