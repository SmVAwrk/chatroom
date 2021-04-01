import json

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from chat_app.models import Room, RoomInvite, Message
from chat_app.serializers import (
    RoomListSerializer, RoomDetailSerializer, InviteSerializer,
    InviteToMeSerializer, MessageSerializer
)


class RoomViewSetTestCase(APITestCase):

    def test_rooms_list_not_auth(self):
        url = reverse('room-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rooms_list_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room')
        room_2 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_3 = Room.objects.create(owner=user2, title='test-room', slug='test-slug-2')
        room_2.members.add(user1)

        # Обновление для сохранения автосген. слага
        room_1.refresh_from_db()

        url = reverse('room-list')

        serializer = RoomListSerializer([room_2, room_1], many=True)

        self.client.force_login(user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_rooms_list_search_title(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room 1', slug='room')
        room_2 = Room.objects.create(owner=user1, title='test-room 2', slug='test-slug')
        room_2.members.add(user1)

        url = reverse('room-list')

        rooms = Room.objects.filter(title__contains='1')
        serializer = RoomListSerializer(rooms, many=True)

        self.client.force_login(user1)
        response = self.client.get(url, data={'search': '1'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_rooms_list_search_slug(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test 1', slug='room')
        room_2 = Room.objects.create(owner=user1, title='test 2', slug='test-slug')
        room_2.members.add(user1)

        url = reverse('room-list')

        rooms = Room.objects.filter(slug__contains='room')
        serializer = RoomListSerializer(rooms, many=True)

        self.client.force_login(user1)
        response = self.client.get(url, data={'search': 'room'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_retrieve_not_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')

        url = reverse('room-detail', kwargs={'slug': room_1.slug})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_auth_not_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')

        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')

        url = reverse('room-detail', kwargs={'slug': room_1.slug})

        self.client.force_login(user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_auth_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_1.members.add(user1)
        url = reverse('room-detail', kwargs={'slug': room_1.slug})

        self.client.force_login(user1)
        response = self.client.get(url)

        serializer = RoomDetailSerializer(room_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_auth_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        url = reverse('room-detail', kwargs={'slug': room_1.slug})

        self.client.force_login(user1)
        response = self.client.get(url)

        serializer = RoomDetailSerializer(room_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_not_auth(self):
        url = reverse('room-list')

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('room-list')

        input_data = {
            'title': 'Test Title 1',
            'slug': 'test-slug'
        }

        self.client.force_login(user1)

        self.assertEqual(Room.objects.all().count(), 0)
        response = self.client.post(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Room.objects.all().count(), 1)

    def test_create_without_slug(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('room-list')
        input_data = {
            'title': 'Test Title 1',
        }

        self.client.force_login(user1)

        self.assertEqual(Room.objects.all().count(), 0)
        response = self.client.post(url, data=input_data)
        room_uuid = Room.objects.all().first().slug.split('-')[-1]
        expected_slug = f'test-title-1-id-{room_uuid}'

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], expected_slug)

    def test_update_not_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_1.members.add(user1)
        url = reverse('room-detail', kwargs={'slug': room_1.slug})
        input_data = {
            'title': 'New title',
            'slug': 'test-slug'
        }

        self.client.force_login(user1)
        response = self.client.put(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        url = reverse('room-detail', kwargs={'slug': room_1.slug})
        input_data = {
            'title': 'New title',
            'slug': 'test-slug'
        }
        self.client.force_login(user1)
        response = self.client.put(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New title')

    def test_update_not_owner_and_not_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        url = reverse('room-detail', kwargs={'slug': room_1.slug})
        input_data = {
            'title': 'New title',
            'slug': 'test-slug'
        }

        self.client.force_login(user1)
        response = self.client.put(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_not_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_1.members.add(user1)
        url = reverse('room-detail', kwargs={'slug': room_1.slug})
        input_data = {
            'title': 'New title'
        }

        self.client.force_login(user1)
        response = self.client.patch(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        url = reverse('room-detail', kwargs={'slug': room_1.slug})
        input_data = {
            'title': 'New title'
        }
        self.client.force_login(user1)
        response = self.client.patch(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New title')

    def test_partial_update_not_owner_and_not_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        url = reverse('room-detail', kwargs={'slug': room_1.slug})
        input_data = {
            'title': 'New title'
        }

        self.client.force_login(user1)
        response = self.client.patch(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_not_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_1.members.add(user1)
        url = reverse('room-detail', kwargs={'slug': room_1.slug})

        self.client.force_login(user1)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        url = reverse('room-detail', kwargs={'slug': room_1.slug})

        self.client.force_login(user1)
        self.assertEqual(Room.objects.all().count(), 1)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Room.objects.all().count(), 0)

    def test_delete_not_owner_and_not_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        url = reverse('room-detail', kwargs={'slug': room_1.slug})

        self.client.force_login(user1)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InviteViewTestCase(APITestCase):

    def test_invite_room_not_found(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')

        url = reverse('room-invite', kwargs={'room_slug': 1})

        self.client.force_login(user1)
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_not_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        url = reverse('room-invite', kwargs={'room_slug': room_1.slug})

        self.client.force_login(user1)
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invite_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        url = reverse('room-invite', kwargs={'room_slug': room_1.slug})
        input_data = [
            {
                'invite_object': user2.id
            },
            {
                'invite_object': user3.id
            }
        ]
        json_data = json.dumps(input_data)

        self.client.force_login(user1)
        self.assertEqual(RoomInvite.objects.all().count(), 0)
        response = self.client.post(url, data=json_data, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoomInvite.objects.all().count(), 2)


class InviteFromMeViewTestCase(APITestCase):

    def test_invite_from_me_list_not_auth(self):
        url = reverse('invite-from-me-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invite_from_me_list_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        room_2 = Room.objects.create(owner=user2, title='test-room', slug='test-slug-2')
        invite_1 = RoomInvite.objects.create(creator=user1, invite_object=user2, room=room_1)
        invite_2 = RoomInvite.objects.create(creator=user1, invite_object=user3, room=room_1)
        invite_3 = RoomInvite.objects.create(creator=user2, invite_object=user3, room=room_2)
        url = reverse('invite-from-me-list')
        serializer = InviteSerializer([invite_2, invite_1], many=True)

        self.client.force_login(user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_invite_from_me_delete(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        invite_1 = RoomInvite.objects.create(creator=user1, invite_object=user2, room=room_1)
        url = reverse('invite-from-me-detail', kwargs={'pk': invite_1.id})

        self.client.force_login(user1)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RoomInvite.objects.all().count(), 0)

    def test_invite_from_me_delete_not_creator(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_2 = Room.objects.create(owner=user2, title='test-room', slug='test-slug-2')
        invite_3 = RoomInvite.objects.create(creator=user2, invite_object=user3, room=room_2)
        url = reverse('invite-from-me-detail', kwargs={'pk': invite_3.id})

        self.client.force_login(user1)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InviteToMeViewTestCase(APITestCase):

    def test_invite_to_me_list_not_auth(self):
        url = reverse('invite-to-me-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invite_to_me_list_auth(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_2 = Room.objects.create(owner=user3, title='test-room', slug='test-slug-2')
        invite_1 = RoomInvite.objects.create(creator=user2, invite_object=user1, room=room_1)
        invite_2 = RoomInvite.objects.create(creator=user3, invite_object=user1, room=room_2)
        serializer = InviteToMeSerializer([invite_2, invite_1], many=True)
        url = reverse('invite-to-me-list')

        self.client.force_login(user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)

    def test_invite_to_me_update(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        invite_1 = RoomInvite.objects.create(creator=user2, invite_object=user1, room=room_1)
        url = reverse('invite-to-me-detail', kwargs={'pk': invite_1.id})
        input_data = {
            'is_accepted': True
        }

        self.client.force_login(user1)
        response = self.client.put(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RoomInvite.objects.all().count(), 0)

    def test_invite_to_me_partial_update(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        invite_1 = RoomInvite.objects.create(creator=user2, invite_object=user1, room=room_1)
        url = reverse('invite-to-me-detail', kwargs={'pk': invite_1.id})
        input_data = {
            'is_accepted': True
        }

        self.client.force_login(user1)
        response = self.client.patch(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RoomInvite.objects.all().count(), 0)

    def test_invite_to_me_not_invite_object(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        invite_1 = RoomInvite.objects.create(creator=user2, invite_object=user3, room=room_1)
        url = reverse('invite-to-me-detail', kwargs={'pk': invite_1.id})
        input_data = {
            'is_accepted': True
        }

        self.client.force_login(user1)
        response = self.client.patch(url, data=input_data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LazyLoadMessagesViewTestCase(APITestCase):

    def test_not_owner_and_not_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        message_1 = Message.objects.create(author=user2, room=room_1, text='test text')
        message_2 = Message.objects.create(author=user2, room=room_1, text='test text 2')
        message_3 = Message.objects.create(author=user2, room=room_1, text='test text 3')
        url = reverse('room-messages', kwargs={'room_slug': room_1.slug})

        self.client.force_login(user1)
        response = self.client.get(url, data={'limit': 2, 'offset': 0})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        message_1 = Message.objects.create(author=user2, room=room_1, text='test text')
        message_2 = Message.objects.create(author=user2, room=room_1, text='test text 2')
        message_3 = Message.objects.create(author=user2, room=room_1, text='test text 3')
        url = reverse('room-messages', kwargs={'room_slug': room_1.slug})

        serializer = MessageSerializer([message_3, message_2], many=True)

        self.client.force_login(user1)
        response = self.client.get(url, data={'limit': 2, 'offset': 0})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['messages'], serializer.data)
        self.assertFalse(response.data['no_more_data'])

    def test_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_1.members.add(user1)
        message_1 = Message.objects.create(author=user2, room=room_1, text='test text')
        message_2 = Message.objects.create(author=user2, room=room_1, text='test text 2')
        message_3 = Message.objects.create(author=user2, room=room_1, text='test text 3')
        url = reverse('room-messages', kwargs={'room_slug': room_1.slug})

        serializer = MessageSerializer([message_3, message_2, message_1], many=True)

        self.client.force_login(user1)
        response = self.client.get(url, data={'limit': 4, 'offset': 0})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['messages'], serializer.data)
        self.assertTrue(response.data['no_more_data'])

    def test_not_found(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        url = reverse('room-messages', kwargs={'room_slug': 'not-found'})

        self.client.force_login(user1)
        response = self.client.get(url, data={'limit': 3, 'offset': 0})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_params(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        url = reverse('room-messages', kwargs={'room_slug': room_1.slug})

        self.client.force_login(user1)
        response = self.client.get(url, data={'limit': 'sre'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
