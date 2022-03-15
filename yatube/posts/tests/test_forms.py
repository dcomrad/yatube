import shutil
import tempfile

from core.utils import get_login_redirect_url
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='user')
        cls.another_user = User.objects.create(username='another_user')

        user_small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        user_uploaded = SimpleUploadedFile(
            name='user_small.gif',
            content=user_small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            id=1,
            title='Тестовая группа',
            slug='test_group',
            description='Описание тестовой группы'
        )

        cls.post = Post.objects.create(
            id=1,
            text='Тестовое содержимое поста',
            author=cls.user,
            group=cls.group,
            image=user_uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(FormTest.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(FormTest.another_user)

    @staticmethod
    def get_post_response(client, request_url, post_text='tmp', group_id='',
                          post_image=''):
        if not post_image:
            post_image = SimpleUploadedFile(
                name='temp.gif',
                content=(
                    b'\x47\x49\x46\x38\x39\x61\x01'
                    b'\x00\x01\x00\x80\x00\x00\x05'
                    b'\x04\x04\x00\x00\x00\x2c\x00'
                    b'\x00\x00\x00\x01\x00\x01\x00'
                    b'\x00\x02\x02\x44\x01\x00\x3b'
                ),
                content_type='image/gif'
            )
        form = {
            'text': post_text,
            'group': group_id,
            'image': post_image
        }
        return client.post(
            request_url,
            data=form,
        )

    def test_guest_create_post(self):
        """Попытка создания поста неавторизованным пользователем"""
        posts_count = Post.objects.count()

        request_url = reverse('posts:post_create')
        response = FormTest.get_post_response(self.guest_client, request_url)

        # check a redirection to the login page
        self.assertRedirects(response, get_login_redirect_url(request_url))

        # the number of posts in the DB should not have increased
        self.assertEqual(posts_count, Post.objects.count())

    def test_authorized_create_post(self):
        """Создание поста авторизованным пользователем"""
        posts_count = Post.objects.count()
        post_text = 'Этот пост создан при тестировании'
        post_group = FormTest.group.id
        post_image = SimpleUploadedFile(
            name='create_post_small.gif',
            content=(
                b'\x47\x49\x46\x38\x39\x61\x01'
                b'\x00\x01\x00\x80\x00\x00\x05'
                b'\x04\x04\x00\x00\x00\x2c\x00'
                b'\x00\x00\x00\x01\x00\x01\x00'
                b'\x00\x02\x02\x44\x01\x00\x3b'
            ),
            content_type='image/gif'
        )

        response = FormTest.get_post_response(
            self.authorized_client, reverse('posts:post_create'),
            post_text, post_group, post_image
        )

        # check a redirection to the profile page
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': FormTest.user.username})
        )

        # new post has added to the DB
        self.assertEqual(posts_count + 1, Post.objects.count())
        self.assertTrue(
            Post.objects.filter(
                text=post_text,
                group=post_group,
                image__endswith=post_image.name
            ).exists()
        )

    def test_guest_update_post(self):
        """Попытка изменения поста неавторизованным пользователем и
        авторизованным пользователем, который не является автором поста"""
        request_url = reverse('posts:post_edit',
                              kwargs={'post_id': FormTest.post.id})

        guest_response = FormTest.get_post_response(
            self.guest_client, request_url
        )
        another_user_response = FormTest.get_post_response(
            self.another_authorized_client, request_url
        )

        # check a redirection to the login page for guests
        self.assertRedirects(guest_response,
                             get_login_redirect_url(request_url))

        # check a redirection to the post detail page for non-author
        self.assertRedirects(
            another_user_response,
            reverse('posts:post_detail', kwargs={'post_id': FormTest.post.id})
        )

        # the post hasn't updated
        self.assertEqual(Post.objects.get(id=FormTest.post.id), FormTest.post)

    def test_author_update_post(self):
        """Изменение поста его автором"""
        posts_count = Post.objects.count()
        request_url = reverse('posts:post_edit',
                              kwargs={'post_id': FormTest.post.id})
        post_new_text = 'Этот пост отредактирован при тестировании'
        post_new_image = SimpleUploadedFile(
            name='update_post_small.gif',
            content=(
                b'\x47\x49\x46\x38\x39\x61\x01'
                b'\x00\x01\x00\x80\x00\x00\x05'
                b'\x04\x04\x00\x00\x00\x2c\x00'
                b'\x00\x00\x00\x01\x00\x01\x00'
                b'\x00\x02\x02\x44\x01\x00\x3b'
            ),
            content_type='image/gif'
        )

        response = FormTest.get_post_response(
            self.authorized_client, request_url, post_text=post_new_text,
            post_image=post_new_image
        )

        # check a redirection to the post_detail page
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': FormTest.post.id})
        )

        # no new posts
        self.assertEqual(posts_count, Post.objects.count())

        # the post has updated
        self.assertTrue(
            Post.objects.filter(
                id=FormTest.post.id,
                text=post_new_text,
                group__isnull=True,
                image__endswith=post_new_image.name
            ).exists()
        )

    def test_guest_add_comment(self):
        """Попытка добавления комментария неавторизованным пользователем"""
        comments_count = FormTest.post.comments.count()
        request_url = reverse('posts:add_comment',
                              kwargs={'post_id': FormTest.post.id})

        response = self.guest_client.post(request_url)

        # check a redirection to the login page for guests
        self.assertRedirects(response,
                             get_login_redirect_url(request_url))

        # no new comments
        self.assertEqual(comments_count, FormTest.post.comments.count())

    def test_authorized_add_comment(self):
        """Попытка добавления комментария авторизованным пользователем"""
        comments_count = FormTest.post.comments.count()
        comment_text = 'Это тестовый коммент'
        form = {
            'text': comment_text,
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': FormTest.post.id}),
            data=form,
        )

        # check a redirection to the post detail page
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': FormTest.post.id})
        )

        # new comment has added
        self.assertEqual(comments_count + 1, FormTest.post.comments.count())
        self.assertTrue(
            Comment.objects.filter(
                text=comment_text,
            ).exists()
        )

    def test_guest_subscription(self):
        """Попытка неавторизованного пользователя подписаться на автора или
        отписаться от него"""
        follow_url = reverse('posts:profile_follow',
                             kwargs={'username': self.another_user.username})
        unfollow_url = reverse('posts:profile_unfollow',
                               kwargs={'username': self.another_user.username})

        follow_response = self.guest_client.post(follow_url)
        unfollow_response = self.guest_client.post(unfollow_url)

        # check a redirection to the login page for guests
        self.assertRedirects(follow_response,
                             get_login_redirect_url(follow_url))
        self.assertRedirects(unfollow_response,
                             get_login_redirect_url(unfollow_url))

    def test_authorized_subscription(self):
        """Подписка авторизованного пользователя подписаться на автора и
        отписка от него"""
        following_count = self.user.follower.count()

        follow_url = reverse('posts:profile_follow',
                             kwargs={'username': self.another_user.username})
        unfollow_url = reverse('posts:profile_unfollow',
                               kwargs={'username': self.another_user.username})

        self.authorized_client.post(follow_url)
        self.assertEqual(following_count + 1, self.user.follower.count())

        self.authorized_client.post(unfollow_url)
        self.assertEqual(following_count, self.user.follower.count())
