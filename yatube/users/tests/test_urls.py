from http import HTTPStatus

from core.utils import get_login_redirect_url
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class URLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='admin')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(URLTest.user)

    def test_open_access(self):
        """Проверка доступности страниц анонимным пользователям"""
        urls = [
            '/auth/signup/',
            '/auth/login/',
            '/auth/logout/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/85/15/',
            '/auth/reset/done/',
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    HTTPStatus.OK
                )
                self.assertEqual(
                    self.authorized_client.get(url).status_code,
                    HTTPStatus.OK
                )

    def test_authorized_access(self):
        """Проверка доступности страниц смены пароля"""
        urls = [
            '/auth/password_change/',
            '/auth/password_change/done/',
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.authorized_client.get(url).status_code,
                    HTTPStatus.OK
                )
                self.assertRedirects(
                    self.guest_client.get(url),
                    get_login_redirect_url(url)
                )

    def test_nonexistent_page(self):
        """Проверка отсутствия доступа к несуществующей странице"""
        url = '/nonexistent_page/'
        self.assertEqual(self.guest_client.get(url).status_code,
                         HTTPStatus.NOT_FOUND)
        self.assertEqual(self.authorized_client.get(url).status_code,
                         HTTPStatus.NOT_FOUND)

    def test_templates(self):
        """Проверка вызова правильных шаблонов"""
        templates = {
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/85/15/': 'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/logout/': 'users/logged_out.html',
        }

        for url, template in templates.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(self.authorized_client.get(url),
                                        template)
