import json
import os
import shutil
from io import BytesIO

from PIL import Image
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from chatroom_project.settings import BASE_DIR
from user_profile.models import UserProfile, FriendshipRelation
from user_profile.serializers import (
    ProfileListSerializer, ProfileDetailSerializer,
    FriendshipRelationSerializer, FriendshipRelationListSerializer
)


class ProfileUserViewSetTestCase(APITestCase):

    def test_profiles_list_not_auth(self):
        url = reverse('profile-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profiles_list_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        serializer = ProfileListSerializer([user1.profile, user2.profile], many=True)
        self.client.force_login(user1)
        url = reverse('profile-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_profiles_list_search(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        profiles = UserProfile.objects.filter(username__contains='user1')
        serializer = ProfileListSerializer(profiles, many=True)
        self.client.force_login(user1)
        url = reverse('profile-list')
        response = self.client.get(url, data={'search': 'user1'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_retrieve_not_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('profile-detail', kwargs={'user': user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        serializer = ProfileDetailSerializer(user1.profile)
        url = reverse('profile-detail', kwargs={'user': user1.id})
        self.client.force_login(user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_not_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        url = reverse('profile-detail', kwargs={'user': user2.id})
        self.client.force_login(user1)
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_not_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        url = reverse('profile-detail', kwargs={'user': user2.id})
        self.client.force_login(user1)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('profile-detail', kwargs={'user': user1.id})
        self.client.force_login(user1)

        input_data = {
            "user": user1.id,
            "friends": [],
            "username": "TestUser1",
            "avatar": None,
            "description": "",
            "first_name": "",
            "last_name": "",
            "birth_date": None,
            "location": ""
        }
        json_data = json.dumps(input_data)

        response = self.client.put(url, content_type='application/json', data=json_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], "TestUser1")

    def test_partial_update_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('profile-detail', kwargs={'user': user1.id})
        self.client.force_login(user1)

        input_data = {
            "username": "TestUser1"
        }
        json_data = json.dumps(input_data)

        response = self.client.patch(url, content_type='application/json', data=json_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], "TestUser1")

    def test_load_image(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='test@image.jpeg')

        # Данный email обязателен для создания специальной тестовой папки в media
        assert user1.email == 'test@image.jpeg'

        url = reverse('profile-detail', kwargs={'user': user1.id})
        self.client.force_login(user1)

        avatar = BytesIO()
        image = Image.new('RGB', size=(100, 100))
        image.save(avatar, 'jpeg')
        avatar.name = 'test_image.jpeg'
        avatar.seek(0)

        data = {
            'first_name': 'Test',
            'avatar': avatar
        }
        expected_avatar_path = f'http://testserver/media/avatars/test/uid-{user1.id}/{avatar.name}'

        response = self.client.patch(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['avatar'], expected_avatar_path)

        # Удаление сохраненного тестового аватара
        path = os.path.join(BASE_DIR, 'media/avatars/test')
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_friend_add_not_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('profile-add-friend', kwargs={'user': user1.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_friend_add_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        url = reverse('profile-add-friend', kwargs={'user': user2.id})
        self.client.force_login(user1)

        input_data = {'creator': user1.id, 'friend_object': user2.id}
        serializer = FriendshipRelationSerializer(data=input_data)
        serializer.is_valid()

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)

    def test_friend_add_not_found(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('profile-add-friend', kwargs={'user': 0})
        self.client.force_login(user1)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_friend_del_not_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('profile-delete-friend', kwargs={'user': user1.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_friend_del_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user1.profile.friends.add(user2)
        url = reverse('profile-delete-friend', kwargs={'user': user2.id})
        self.client.force_login(user1)

        self.assertEqual(user1.profile.friends.all().count(), 1)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(user1.profile.friends.all().count(), 0)

    def test_friend_del_not_found(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('profile-delete-friend', kwargs={'user': 0})
        self.client.force_login(user1)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FriendshipRelationFromMeViewSetTestCase(APITestCase):

    def test_request_from_me_list_not_auth(self):
        url = reverse('friend-requests-from-me-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_request_from_me_list_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        url = reverse('friend-requests-from-me-list')
        friend_request_1 = FriendshipRelation.objects.create(creator=user1, friend_object=user2)
        friend_request_2 = FriendshipRelation.objects.create(creator=user1, friend_object=user3)
        friend_request_3 = FriendshipRelation.objects.create(creator=user2, friend_object=user3)
        serializer = FriendshipRelationListSerializer([friend_request_2, friend_request_1], many=True)

        self.client.force_login(user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_request_from_me_delete(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request_1 = FriendshipRelation.objects.create(creator=user1, friend_object=user2)
        url = reverse('friend-requests-from-me-detail', kwargs={'pk': friend_request_1.id})

        self.client.force_login(user1)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FriendshipRelation.objects.all().count(), 0)

    def test_request_from_me_delete_not_creator(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        friend_request_2 = FriendshipRelation.objects.create(creator=user2, friend_object=user3)
        url = reverse('friend-requests-from-me-detail', kwargs={'pk': friend_request_2.id})

        self.client.force_login(user1)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FriendshipRelationToMeViewSetTestCase(APITestCase):

    def test_request_to_me_list_not_auth(self):
        url = reverse('friend-requests-to-me-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_request_to_me_list_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        url = reverse('friend-requests-to-me-list')
        friend_request_2 = FriendshipRelation.objects.create(creator=user2, friend_object=user1)
        friend_request_3 = FriendshipRelation.objects.create(creator=user3, friend_object=user1)
        serializer = FriendshipRelationListSerializer([friend_request_3, friend_request_2], many=True)

        self.client.force_login(user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_request_to_me_update(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request_1 = FriendshipRelation.objects.create(creator=user2, friend_object=user1)
        url = reverse('friend-requests-to-me-detail', kwargs={'pk': friend_request_1.id})
        input_data = {
            'is_accepted': True
        }

        self.client.force_login(user1)
        response = self.client.put(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FriendshipRelation.objects.all().count(), 0)

    def test_request_to_me_partial_update(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request_1 = FriendshipRelation.objects.create(creator=user2, friend_object=user1)
        url = reverse('friend-requests-to-me-detail', kwargs={'pk': friend_request_1.id})
        input_data = {
            'is_accepted': True
        }

        self.client.force_login(user1)
        response = self.client.patch(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FriendshipRelation.objects.all().count(), 0)

    def test_request_to_me_delete_not_friend_object(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        friend_request_2 = FriendshipRelation.objects.create(creator=user2, friend_object=user3)
        url = reverse('friend-requests-to-me-detail', kwargs={'pk': friend_request_2.id})
        input_data = {
            'is_accepted': True
        }

        self.client.force_login(user1)
        response = self.client.patch(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

# Отладка SQL запросов
# with CaptureQueriesContext(connection) as queries:
#     response = self.client.get(url)
#     pprint([q for q in queries])
#     print('queries', len(queries))
