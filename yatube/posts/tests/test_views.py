import shutil
import tempfile

from core.utils import clear_cache
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='user')
        cls.user_post_text = '123456789012345678901234567890'

        cls.another_user = User.objects.create(username='another')
        cls.another_user_post_text = '987654321098765432109876543210'

        cls.third_user = User.objects.create(username='third')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Описание тестовой группы'
        )
        cls.another_group = Group.objects.create(
            title='Ещё одна тестовая группа',
            slug='another_test_group',
            description='Описание ещё одной тестовой группы'
        )

        user_small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        another_user_small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3A'
        )
        user_uploaded = SimpleUploadedFile(
            name='user_small.gif',
            content=user_small_gif,
            content_type='image/gif'
        )
        another_user_uploaded = SimpleUploadedFile(
            name='another_user_small.gif',
            content=another_user_small_gif,
            content_type='image/gif'
        )

        # the first fifteen posts' author is user
        Post.objects.create(
            id=1,
            text=cls.user_post_text,
            author=cls.user,
            group=cls.group,
            image=user_uploaded,
        )
        Post.objects.bulk_create(
            Post(id=i,
                 text=cls.user_post_text,
                 author=cls.user,
                 group=cls.group
                 ) for i in range(2, 16)
        )

        # the last fourteen posts' author is another_user
        Post.objects.create(
            id=16,
            text=cls.another_user_post_text,
            author=cls.another_user,
            group=cls.another_group,
            image=another_user_uploaded
        )
        Post.objects.bulk_create(
            Post(id=i,
                 text=cls.another_user_post_text,
                 author=cls.another_user,
                 group=cls.another_group
                 ) for i in range(17, 30)
        )
        cls.user_post = Post.objects.get(id=1)
        cls.another_user_post = Post.objects.get(id=16)

        cls.user_post_comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.user_post
        )

        cls.user_followers = Follow.objects.create(
            user=cls.another_user,
            author=cls.user
        )

        cls.posts_count = Post.objects.count()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(ViewTest.user)

        self.authorized_another_client = Client()
        self.authorized_another_client.force_login(ViewTest.another_user)

        self.authorized_third_client = Client()
        self.authorized_third_client.force_login(ViewTest.third_user)

    @clear_cache
    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:index') + '?page=3')
        page_obj = response.context.get('page_obj')

        # 29 records in total
        self.assertEqual(page_obj.paginator.count, ViewTest.posts_count)

        # 9 records on the last page
        self.assertEqual(len(page_obj), 9)

        last_item = page_obj.object_list[len(page_obj) - 1]
        self.assertEqual(last_item, ViewTest.user_post)

    @clear_cache
    def test_index_cache(self):
        """Проверка работы кеширования главной страницы"""
        new_post = Post.objects.create(
            text='Временный пост',
            author=ViewTest.user
        )
        content = self.guest_client.get(reverse('posts:index')).content
        new_post.delete()
        cached_content = self.guest_client.get(reverse('posts:index')).content

        # because of caching, the deleted post still appears
        self.assertEqual(content, cached_content)

        # after clearing the cache, the index page is generated again
        cache.clear()
        new_content = self.guest_client.get(reverse('posts:index')).content
        self.assertNotEqual(content, new_content)

    def test_follow_index_correct_context(self):
        """Шаблон follow сформирован с правильным контекстом"""
        follower_response = self.authorized_another_client.get(
            reverse('posts:follow_index') + '?page=2'
        )
        third_user_response = self.authorized_third_client.get(
            reverse('posts:follow_index')
        )

        follower_page_obj = follower_response.context.get('page_obj')
        third_user_page_obj = third_user_response.context.get('page_obj')

        # 15 user's records in total on the follower's page
        self.assertEqual(follower_page_obj.paginator.count,
                         ViewTest.user.posts.count())
        # no records for the third user
        self.assertEqual(third_user_page_obj.paginator.count, 0)

        # 5 records on the follower's last page
        self.assertEqual(len(follower_page_obj), 5)

        last_item = follower_page_obj.object_list[len(follower_page_obj) - 1]
        self.assertEqual(last_item, ViewTest.user_post)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_another_client.get(
            reverse('posts:profile', kwargs={'username': 'user'})
            + '?page=2'
        )

        user = response.context.get('user_obj')
        self.assertEqual(user, ViewTest.user)

        # 15 records in total
        page_obj = response.context.get('page_obj')
        self.assertEqual(page_obj.paginator.count,
                         ViewTest.user.posts.count())

        # 5 records on the last page
        self.assertEqual(len(page_obj), 5)

        last_item = page_obj.object_list[len(page_obj) - 1]
        self.assertEqual(last_item, ViewTest.user_post)

        # check followings
        self.assertEqual(response.context.get('following'), True)

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'another_test_group'})
            + '?page=2'
        )

        group = response.context.get('group')
        self.assertEqual(group, ViewTest.another_group)

        # 14 records in total
        page_obj = response.context.get('page_obj')
        self.assertEqual(page_obj.paginator.count,
                         ViewTest.another_group.posts.count())

        # 4 records on the last page
        self.assertEqual(len(page_obj), 4)

        last_item = page_obj.object_list[len(page_obj) - 1]
        self.assertEqual(last_item, ViewTest.another_user_post)

    def check_form_fields(self, form, form_fields):
        """Вспомогательная функция проверки полей формы поста"""
        for field_name, field_type in form_fields.items():
            with self.subTest(field_name=field_name):
                self.assertIsInstance(form.fields.get(field_name), field_type)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )

        self.assertEqual(response.context.get('post'), ViewTest.user_post)

        # check comment form
        form_fields = {
            'text': forms.fields.CharField,
        }
        self.check_form_fields(response.context.get('comment_form'),
                               form_fields)

        # check post comments
        self.assertEqual(list(response.context.get('comments')),
                         list(ViewTest.user_post.comments.all()))

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.check_form_fields(response.context.get('form'), form_fields)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )

        form = response.context.get('form')
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        self.check_form_fields(form, form_fields)
        self.assertEqual(form.instance.id, 1)
