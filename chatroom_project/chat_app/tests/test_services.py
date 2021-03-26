from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ParseError

from chat_app.models import Room, RoomInvite, Message
from chat_app.services import invite_handler, get_emails, message_filter


class InviteHandlerTestCase(TestCase):

    def test_accepted(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        invite_1 = RoomInvite.objects.create(creator=user2, room=room_1, invite_object=user1, is_accepted=True)

        self.assertEqual(RoomInvite.objects.all().count(), 1)
        invite_handler(invite_1)
        self.assertEqual(room_1.members.all().count(), 1)
        self.assertEqual(RoomInvite.objects.all().count(), 0)

    def test_declined(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        invite_1 = RoomInvite.objects.create(creator=user2, room=room_1, invite_object=user1, is_accepted=False)

        self.assertEqual(RoomInvite.objects.all().count(), 1)
        invite_handler(invite_1)
        self.assertEqual(room_1.members.all().count(), 0)
        self.assertEqual(RoomInvite.objects.all().count(), 0)

    def test_not_updated(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        room_1 = Room.objects.create(owner=user2, title='test-room', slug='test-slug')
        invite_1 = RoomInvite.objects.create(creator=user2, room=room_1, invite_object=user1)

        self.assertEqual(RoomInvite.objects.all().count(), 1)
        invite_handler(invite_1)
        self.assertEqual(room_1.members.all().count(), 0)
        self.assertEqual(RoomInvite.objects.all().count(), 1)


class GetEmailsTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')

        data = [
            {
                'invite_object': user1.id
            },
            {
                'invite_object': user2.id
            }
        ]
        expected_data = ['user1@test.com', 'user2@test.com']

        emails = get_emails(data)
        self.assertEqual(emails, expected_data)


class MessageFilterTestCase(TestCase):

    def test_ok_with_remaining_data(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        message_1 = Message.objects.create(author=user1, room=room_1, text='test text')
        message_2 = Message.objects.create(author=user1, room=room_1, text='test text 2')
        message_3 = Message.objects.create(author=user1, room=room_1, text='test text 3')
        request = Mock()
        request.GET = {
            'limit': 2,
            'offset': 0,
        }

        messages, no_more_data = message_filter(request, room_1.slug)
        messages_list = [msg for msg in messages]
        expected_messages_list = [message_3, message_2]

        self.assertEqual(messages_list, expected_messages_list)
        self.assertFalse(no_more_data)

    def test_ok_with_all_data(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        message_1 = Message.objects.create(author=user1, room=room_1, text='test text')
        message_2 = Message.objects.create(author=user1, room=room_1, text='test text 2')
        message_3 = Message.objects.create(author=user1, room=room_1, text='test text 3')
        request = Mock()
        request.GET = {
            'limit': 3,
            'offset': 0,
        }

        messages, no_more_data = message_filter(request, room_1.slug)
        messages_list = [msg for msg in messages]
        expected_messages_list = [message_3, message_2, message_1]

        self.assertEqual(messages_list, expected_messages_list)
        self.assertTrue(no_more_data)

    def test_without_params(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        request = Mock()
        request.GET = {
            'offset': 0
        }

        with self.assertRaises(ParseError):
            message_filter(request, room_1.slug)

    def test_with_not_valid_params(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        room_1 = Room.objects.create(owner=user1, title='test-room', slug='test-slug')
        request = Mock()
        request.GET = {
            'limit': 3,
            'offset': 'a'
        }

        with self.assertRaises(ParseError):
            message_filter(request, room_1.slug)
