from http import HTTPStatus

from django.test import Client, TestCase


class URLTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls(self):
        """Проверка доступности статичных страниц по url"""
        urls = {
            '/about/author/',
            '/about/tech/'
        }
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.guest_client.get(url).status_code,
                                 HTTPStatus.OK)
