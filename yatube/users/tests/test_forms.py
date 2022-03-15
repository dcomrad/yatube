from django.test import Client, TestCase
from django.urls import reverse
from posts.models import User


class FormTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_create_user(self):
        users_count = User.objects.count()
        username = 'user'
        password = 'rfhfufylf'
        form_data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'username': username,
            'email': 'test@example.com',
            'password1': password,
            'password2': password
        }

        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
        )

        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(users_count + 1, User.objects.count())
        self.assertTrue(
            User.objects.filter(
                username=username,
            ).exists()
        )
