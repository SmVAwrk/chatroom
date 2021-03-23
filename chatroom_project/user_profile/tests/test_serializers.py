from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from user_profile.models import UserProfile, FriendshipRelation
from user_profile.serializers import ProfileListSerializer, ProfileDetailSerializer, FriendshipRelationSerializer, \
    FriendshipRelationListSerializer


class ProfileListSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user1.profile.avatar = 'some_path'
        expected_data = [
            {
                'user_id': user1.id,
                'avatar': '/media/some_path',
                'username': 'user1'
            },
            {
                'user_id': user2.id,
                'avatar': None,
                'username': 'user2'
            }
        ]

        serializer = ProfileListSerializer([user1.profile, user2.profile], many=True)
        self.assertEqual(serializer.data, expected_data)


class ProfileDetailSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user1.profile.friends.add(user2)
        expected_data = {
            "user": user1.id,
            "friends": [
                user2.id
            ],
            "username": "user1",
            "avatar": None,
            "description": "",
            "first_name": "",
            "last_name": "",
            "birth_date": None,
            "location": ""
        }

        serializer = ProfileDetailSerializer(user1.profile)
        self.assertEqual(serializer.data, expected_data)

    def test_read_only_fields(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user1.profile.friends.add(user2)
        input_data = {
            "user": user2.id,
            "friends": [],
            "location": "Test City"
        }
        expected_data = {
            "user": user1.id,
            "friends": [
                user2.id
            ],
            "username": "user1",
            "avatar": None,
            "description": "",
            "first_name": "",
            "last_name": "",
            "birth_date": None,
            "location": "Test City"
        }
        serializer = ProfileDetailSerializer(user1.profile, data=input_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(serializer.data, expected_data)


class FriendshipRelationSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request = FriendshipRelation.objects.create(creator=user1, friend_object=user2)
        expected_data = {
            'creator': user1.id,
            'friend_object': user2.id,
            'is_accepted': None
        }

        serializer = FriendshipRelationSerializer(friend_request)
        self.assertEqual(serializer.data, expected_data)

    def test_valid_data(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        input_data = {
            'creator': user1.id,
            'friend_object': user2.id
        }
        expected_data = {
            'creator': user1.id,
            'friend_object': user2.id,
            'is_accepted': None
        }

        serializer = FriendshipRelationSerializer(data=input_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(serializer.data, expected_data)

    def test_add_myself(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        input_data = {
            'creator': user1.id,
            'friend_object': user1.id
        }

        serializer = FriendshipRelationSerializer(data=input_data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_already_friend(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user1.profile.friends.add(user2)
        input_data = {
            'creator': user1.id,
            'friend_object': user2.id
        }

        serializer = FriendshipRelationSerializer(data=input_data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_request_already_exists(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        FriendshipRelation.objects.create(creator=user1, friend_object=user2)

        input_data_1 = {
            'creator': user1.id,
            'friend_object': user2.id
        }

        serializer_1 = FriendshipRelationSerializer(data=input_data_1)
        with self.assertRaises(ValidationError):
            serializer_1.is_valid(raise_exception=True)

        input_data_2 = {
            'creator': user2.id,
            'friend_object': user1.id
        }

        serializer_2 = FriendshipRelationSerializer(data=input_data_2)
        with self.assertRaises(ValidationError):
            serializer_2.is_valid(raise_exception=True)


class FriendshipRelationListSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request = FriendshipRelation.objects.create(creator=user1, friend_object=user2)

        expected_data = {
            'id': friend_request.id,
            'creator': user1.id,
            'friend_object': user2.id,
            'is_accepted': None
        }

        serializer = FriendshipRelationListSerializer(friend_request)
        self.assertEqual(serializer.data, expected_data)

    def test_read_only_fields(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request = FriendshipRelation.objects.create(creator=user1, friend_object=user2)

        expected_data = {
            'id': friend_request.id,
            'creator': user1.id,
            'friend_object': user2.id,
            'is_accepted': True
        }
        input_data = {
            'id': friend_request.id,
            'creator': user2.id,
            'friend_object': user1.id,
            'is_accepted': True
        }

        serializer = FriendshipRelationListSerializer(instance=friend_request, data=input_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(serializer.data, expected_data)
