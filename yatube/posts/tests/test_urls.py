from http import HTTPStatus

from core.utils import clear_cache, get_login_redirect_url
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class URLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user1 = User.objects.create(username='user1')
        cls.user2 = User.objects.create(username='user2')

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Описание тестовой группы"
        )

        cls.post = Post.objects.create(
            id=1,
            text='123456789012345678901234567890',
            author=cls.user1
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client2 = Client()
        self.authorized_client1.force_login(URLTest.user1)
        self.authorized_client2.force_login(URLTest.user2)

    @clear_cache
    def test_guest_access(self):
        """Проверка доступности страниц любым пользователям"""
        urls = [
            '/',
            '/group/test_group/',
            '/profile/user2/',
            '/posts/1/',
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    HTTPStatus.OK
                )
                self.assertEqual(
                    self.authorized_client1.get(url).status_code,
                    HTTPStatus.OK
                )

    def test_all_redirect(self):
        """Проверка перенаправления любых пользователей"""
        urls = [
            '/profile/user2/follow/',
            '/profile/user2/unfollow/',
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    HTTPStatus.FOUND
                )

    def test_authorized_access(self):
        """Проверка доступности страниц авторизованным пользователям"""
        urls = [
            '/follow/',
            '/create/',
            '/posts/1/comment/'
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.authorized_client1.get(url).status_code,
                                 HTTPStatus.OK)
                self.assertRedirects(self.guest_client.get(url),
                                     get_login_redirect_url(url))

    def test_only_author_access(self):
        """Проверка доступности страниц только автору поста"""
        url = '/posts/1/edit/'

        author = self.authorized_client1
        authorized_user = self.authorized_client2
        guest = self.guest_client

        self.assertEqual(author.get(url).status_code, HTTPStatus.OK)
        self.assertRedirects(authorized_user.get(url), '/posts/1/')
        self.assertRedirects(guest.get(url), get_login_redirect_url(url))

    def test_nonexistent_page(self):
        """Проверка отсутствия доступа к несуществующей странице"""
        url = '/nonexistent_page/'

        self.assertEqual(self.guest_client.get(url).status_code,
                         HTTPStatus.NOT_FOUND)
        self.assertEqual(self.authorized_client1.get(url).status_code,
                         HTTPStatus.NOT_FOUND)

    @clear_cache
    def test_namespaced_urls(self):
        """Проверка вызова правильных шаблонов"""
        namespaced_urls = {
            '/': reverse('posts:index'),
            '/follow/': reverse('posts:follow_index'),
            '/profile/user1/': reverse('posts:profile',
                                       kwargs={'username': 'user1'}),
            '/profile/user1/follow/': reverse('posts:profile_follow',
                                              kwargs={'username': 'user1'}),
            '/profile/user1/unfollow/': reverse('posts:profile_unfollow',
                                                kwargs={'username': 'user1'}),
            '/group/test_group/': reverse('posts:group_list',
                                          kwargs={'slug': 'test_group'}),
            '/posts/1/': reverse('posts:post_detail', kwargs={'post_id': 1}),
            '/create/': reverse('posts:post_create'),
            '/posts/1/edit/': reverse('posts:post_edit',
                                      kwargs={'post_id': 1}),
            '/posts/1/comment/': reverse('posts:add_comment',
                                         kwargs={'post_id': 1}),
        }

        for url, namespaced_url in namespaced_urls.items():
            with self.subTest(url=url):
                self.assertEqual(url, namespaced_url)

    @clear_cache
    def test_templates(self):
        """Проверка вызова правильных шаблонов"""
        templates = {
            '/': 'posts/index.html',
            '/follow/': 'posts/follow.html',
            '/group/test_group/': 'posts/group_list.html',
            '/profile/user1/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/update_post.html',
            '/create/': 'posts/create_post.html',
            '/nonexistent_page/': 'core/404.html'
        }

        client = self.authorized_client1

        for url, template in templates.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(client.get(url), template)
