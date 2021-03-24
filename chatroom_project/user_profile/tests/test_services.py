from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase

from user_profile.models import FriendshipRelation
from user_profile.services import friend_request_handler, friend_delete_validation, friend_delete_handler


class FriendRequestHandlerTestCase(TestCase):

    def test_friend_request_accepted(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request = FriendshipRelation.objects.create(creator=user1, friend_object=user2, is_accepted=True)
        self.assertEqual(FriendshipRelation.objects.all().count(), 1)
        friend_request_handler(friend_request)
        self.assertEqual(user1.profile.friends.all().count(), 1)
        self.assertEqual(user2.profile.friends.all().count(), 1)

    def test_friend_request_declined(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request = FriendshipRelation.objects.create(creator=user1, friend_object=user2, is_accepted=False)
        self.assertEqual(FriendshipRelation.objects.all().count(), 1)
        friend_request_handler(friend_request)
        self.assertEqual(user1.profile.friends.all().count(), 0)
        self.assertEqual(user2.profile.friends.all().count(), 0)

    def test_friend_request_not_updated(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        friend_request = FriendshipRelation.objects.create(creator=user1, friend_object=user2, is_accepted=None)
        self.assertEqual(FriendshipRelation.objects.all().count(), 1)
        friend_request_handler(friend_request)
        self.assertEqual(FriendshipRelation.objects.all().count(), 1)

    def test_not_valid_arg(self):
        with self.assertRaises(AssertionError):
            friend_request_handler(123)


class FriendDeleteValidationTestCase(TestCase):

    def test_valid_data(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user1.profile.friends.add(user2)
        not_valid, user_obj = friend_delete_validation(user1, user2.id)
        self.assertIsNone(not_valid)
        self.assertEqual(user_obj, user2)

    def test_delete_not_friend(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        not_valid, user_obj = friend_delete_validation(user1, user2.id)
        self.assertIsNone(user_obj)
        self.assertIsNotNone(not_valid)

    def test_delete_not_found(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        with self.assertRaises(Http404):
            friend_delete_validation(user1, 5)


class FriendDeleteHandlerTestCase(TestCase):

    def test_ok(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        user1.profile.friends.add(user2)
        user2.profile.friends.add(user1)
        self.assertEqual(user1.profile.friends.all().count(), 1)
        self.assertEqual(user2.profile.friends.all().count(), 1)
        friend_delete_handler(user1, user2)
        self.assertEqual(user1.profile.friends.all().count(), 0)
        self.assertEqual(user2.profile.friends.all().count(), 0)
