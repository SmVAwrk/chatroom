from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from chat_app.models import Room, RoomInvite, Message
from chat_app.serializers import RoomListSerializer, RoomDetailSerializer, InviteSerializer, InviteToMeSerializer, \
    MessageSerializer


class RoomListSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room')
        room_2 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        room_2.members.add(user2)
        expected_data = [
            {
                'title': 'test-room',
                'slug': f'test-room-id{room_1.id}',
                'owner': user1.id,
                'members_num': 1,
                'members': []
            },
            {
                'title': 'test-room',
                'slug': f'test-slug',
                'owner': user1.id,
                'members_num': 2,
                'members': [
                    user2.id
                ]
            },
        ]

        serializer = RoomListSerializer([room_1, room_2], many=True)

        self.assertEqual(serializer.data, expected_data)


class RoomDetailSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        room_1.members.add(user2)
        expected_data = {
            'title': 'test-room',
            'slug': 'test-slug',
            'owner': user1.id,
            'created_at': str(room_1.created_at),
            'members_num': 2,
            'members': [
                user2.id
            ]
        }

        serializer_data = RoomDetailSerializer(room_1).data
        serializer_data['created_at'] = str(room_1.created_at)

        self.assertEqual(serializer_data, expected_data)

    def test_not_valid_slug(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')

        input_data = {
            'slug': 'test-slug-id1234'
        }

        serializer = RoomDetailSerializer(instance=room_1, data=input_data, partial=True)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_delete_slug(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')

        input_data = {
            'slug': ''
        }

        serializer = RoomDetailSerializer(instance=room_1, data=input_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(serializer.data['slug'], f'test-room-id{room_1.id}')

    def test_add_members(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')

        input_data = {
            'members': [
                user2.id
            ]
        }

        serializer = RoomDetailSerializer(instance=room_1, data=input_data, partial=True)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_delete_members(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        room_1.members.add(user2)
        input_data = {
            'members': []
        }

        serializer = RoomDetailSerializer(instance=room_1, data=input_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(serializer.data['members'], [])

    def test_read_only_fields(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        room_1.members.add(user2)
        input_data = {
            'owner': user2.id,
            'members_num': 100,
            'title': 'test-room-1'
        }

        serializer = RoomDetailSerializer(instance=room_1, data=input_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer_data = serializer.data
        serializer_data['created_at'] = str(room_1.created_at)

        expected_data = {
            'title': 'test-room-1',
            'slug': 'test-slug',
            'owner': user1.id,
            'created_at': str(room_1.created_at),
            'members_num': 2,
            'members': [
                user2.id
            ]
        }

        self.assertEqual(serializer_data, expected_data)


class InviteSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        invite_1 = RoomInvite.objects.create(creator=user1, room=room_1, invite_object=user2)
        invite_2 = RoomInvite.objects.create(creator=user1, room=room_1, invite_object=user3)

        expected_data = [
            {
                'id': invite_1.id,
                'creator': user1.id,
                'room': room_1.slug,
                'invite_object': user2.id,
                'is_accepted': None
            },
            {
                'id': invite_2.id,
                'creator': user1.id,
                'room': room_1.slug,
                'invite_object': user3.id,
                'is_accepted': None
            }
        ]

        serializer = InviteSerializer([invite_1, invite_2], many=True)

        self.assertEqual(serializer.data, expected_data)

    def test_valid_data(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')

        input_data = [
            {
                'invite_object': user2.id
            },
            {
                'invite_object': user3.id
            },
        ]

        serializer = InviteSerializer(data=input_data, context={'room': room_1}, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(creator=user1, room=room_1)

        expected_data = [
            {
                'id': serializer.data[0]['id'],
                'creator': user1.id,
                'room': room_1.slug,
                'invite_object': user2.id,
                'is_accepted': None
            },
            {
                'id': serializer.data[1]['id'],
                'creator': user1.id,
                'room': room_1.slug,
                'invite_object': user3.id,
                'is_accepted': None
            }
        ]

        self.assertEqual(serializer.data, expected_data)

    def test_add_already_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        room_1.members.add(user2)
        input_data = [
            {
                'invite_object': user2.id
            }
        ]

        serializer = InviteSerializer(data=input_data, context={'room': room_1}, many=True)

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_add_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        input_data = [
            {
                'invite_object': user1.id
            }
        ]

        serializer = InviteSerializer(data=input_data, context={'room': room_1}, many=True)

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_add_already_invited(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        invite = RoomInvite.objects.create(creator=user1, room=room_1, invite_object=user2)
        input_data = [
            {
                'invite_object': user2.id
            }
        ]

        serializer = InviteSerializer(data=input_data, context={'room': room_1}, many=True)

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class InviteToMeSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_2 = Room.objects.create(owner=user3, title='test-room', slug='test-slug-2')
        invite_1 = RoomInvite.objects.create(creator=user2, room=room_1, invite_object=user1)
        invite_2 = RoomInvite.objects.create(creator=user3, room=room_2, invite_object=user1)
        expected_data = [
            {
                'id': invite_1.id,
                'creator': user2.id,
                'room': room_1.slug,
                'invite_object': user1.id,
                'is_accepted': None
            },
            {
                'id': invite_2.id,
                'creator': user3.id,
                'room': room_2.slug,
                'invite_object': user1.id,
                'is_accepted': None
            }
        ]

        serializer = InviteToMeSerializer([invite_1, invite_2], many=True)

        self.assertEqual(serializer.data, expected_data)

    def test_read_only_fields(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user3 = user_model.objects.create(email='user3@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        room_2 = Room.objects.create(owner=user3, title='test-room', slug='test-slug-2')
        invite_1 = RoomInvite.objects.create(creator=user2, room=room_1, invite_object=user1)
        invite_2 = RoomInvite.objects.create(creator=user3, room=room_2, invite_object=user1)
        input_data = {
            'id': invite_2.id,
            'creator': user3.id,
            'room': room_2.slug,
            'is_accepted': True
        }

        expected_data = {
            'id': invite_1.id,
            'creator': user2.id,
            'room': room_1.slug,
            'invite_object': user1.id,
            'is_accepted': True
        }

        serializer = InviteToMeSerializer(instance=invite_1, data=input_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(serializer.data, expected_data)


class MessageSerializerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        message_1 = Message.objects.create(author=user1, room=room_1, text='test text')
        message_2 = Message.objects.create(author=user1, room=room_1, text='test text 2')

        expected_data = [
            {
                'author': user1.id,
                'room': room_1.slug,
                'text': 'test text',
                'created_at': str(message_1.created_at)
            },
            {
                'author': user1.id,
                'room': room_1.slug,
                'text': 'test text 2',
                'created_at': str(message_1.created_at)
            }
        ]
        serializer = MessageSerializer([message_1, message_2], many=True)
        serializer_data = serializer.data
        for msg in serializer_data:
            msg['created_at'] = str(message_1.created_at)

        self.assertEqual(serializer.data, expected_data)
