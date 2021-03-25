from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from user_profile.permissions import IsOwnerOrAdmin


class IsOwnerOrAdminPermissionTestCase(TestCase):

    def test_owner(self):
        user_model = get_user_model()
        user1 = user_model.objects.create(email='user1@test.com')
        request = Mock()
        request.user = user1
        view = Mock()
        obj = Mock()
        obj.user = user1

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
        obj.user = user1

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
        obj.user = user1

        permission = IsOwnerOrAdmin()
        has_permission = permission.has_object_permission(request, view, obj)
        self.assertFalse(has_permission)
