from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from chat_app.permissions import IsOwnerOrAdmin, IsOwnerOrMember


class IsOwnerOrAdminPermissionTestCase(TestCase):

    def test_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        request = Mock()
        request.user = user1
        view = Mock()
        obj = Mock()
        obj.owner = user1

        permission = IsOwnerOrAdmin()
        has_permission = permission.has_object_permission(request, view, obj)
        self.assertTrue(has_permission)

    def test_admin(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com', is_staff=True)
        request = Mock()
        request.user = user2
        view = Mock()
        obj = Mock()
        obj.owner = user1

        permission = IsOwnerOrAdmin()
        has_permission = permission.has_object_permission(request, view, obj)
        self.assertTrue(has_permission)

    def test_not_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        request = Mock()
        request.user = user2
        view = Mock()
        obj = Mock()
        obj.owner = user1

        permission = IsOwnerOrAdmin()
        has_permission = permission.has_object_permission(request, view, obj)
        self.assertFalse(has_permission)


class IsOwnerOrMemberPermissionTestCase(TestCase):

    def test_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        request = Mock()
        request.user = user1
        view = Mock()
        obj = Mock()
        obj.owner = user1
        obj.members.all = Mock(return_value=[])

        permission = IsOwnerOrMember()
        has_permission = permission.has_object_permission(request, view, obj)
        self.assertTrue(has_permission)

    def test_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        request = Mock()
        request.user = user1
        view = Mock()
        obj = Mock()
        obj.owner = user2
        obj.members.all = Mock(return_value=[user1, ])

        permission = IsOwnerOrMember()
        has_permission = permission.has_object_permission(request, view, obj)
        self.assertTrue(has_permission)

    def test_not_member(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        user2 = user_model.objects.create(email='user2@test.com')
        request = Mock()
        request.user = user1
        view = Mock()
        obj = Mock()
        obj.owner = user2
        obj.members.all = Mock(return_value=[])

        permission = IsOwnerOrAdmin()
        has_permission = permission.has_object_permission(request, view, obj)
        self.assertFalse(has_permission)
