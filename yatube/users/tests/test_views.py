from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ViewTest.user)

    def test_pages_use_correct_template(self):
        """Проверка правильного соответствия страниц шаблонам"""
        pages_to_templates = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_change'):
                'users/password_change_form.html',
            reverse('users:password_change_done'):
                'users/password_change_done.html',
            reverse('users:password_reset'): 'users/password_reset_form.html',
            reverse('users:password_reset_done'):
                'users/password_reset_done.html',
            reverse('users:password_reset_confirm',
                    kwargs={'uidb64': '82', 'token': 'abcdefg'}):
                'users/password_reset_confirm.html',
            reverse('users:password_reset_done'):
                'users/password_reset_done.html',
            reverse('users:logout'): 'users/logged_out.html',
        }
        for url, template in pages_to_templates.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(self.authorized_client.get(url),
                                        template)

    def test_signup_correct_context(self):
        """Шаблон signup сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('users:signup'))

        form = response.context.get('form')
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }

        for field_name, field_type in form_fields.items():
            with self.subTest(field_name=field_name):
                self.assertIsInstance(form.fields.get(field_name), field_type)
