from django.test import Client, TestCase
from django.urls import reverse


class TemplateTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_templates(self):
        """Проверка шаблонов статичных страниц"""
        urls_to_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in urls_to_templates.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(self.guest_client.get(url), template)

    def test_namespaced_url_templates(self):
        """Проверка соответствия именованных URL шаблонам"""
        pages_to_templates = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for url, template in pages_to_templates.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(self.guest_client.get(url), template)
