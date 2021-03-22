from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase

from custom_user.pipeline.user import create_user


class CustomModelTestCase(TestCase):

    def test_create_old_user_model(self):
        with self.assertRaises(AttributeError):
            User.objects.create_user(username='testuser')

    def test_create_custom_user_valid(self):
        user_model = get_user_model()
        user_model.objects.create_user(email='test@email.com')
        self.assertEqual(user_model.objects.all().count(), 1)
        self.assertEqual(user_model.objects.all()[0].get_username(), 'test@email.com')

    def test_create_custom_user_not_valid(self):
        user_model = get_user_model()
        with self.assertRaises(TypeError):
            user_model.objects.create_user(username='testuser')


class TestCustomPipeline(TestCase):

    def test_custom_create_user_pipeline(self):
        strategy = Mock()
        strategy.create_user = Mock()
        details = {
            'username': 'Test_Username',
            'email': ''
        }
        backend = Mock()
        backend.setting = Mock(return_value=['username', 'email'])
        backend.name = 'provider'

        create_user(strategy, details, backend)

        strategy.create_user.assert_called_with(username='Test_Username', email='test_username@provider.oauth')
