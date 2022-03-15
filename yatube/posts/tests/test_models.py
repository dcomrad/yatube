from django.test import TestCase
from posts.models import Comment, Group, Post, User


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='admin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            text='123456789012345678901234567890',
            author=cls.user
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post
        )

    def test_group_str(self):
        """Проверка метода __str__ для модели Group"""
        expected = 'Тестовая группа'
        self.assertEqual(
            str(ModelTest.group),
            expected,
            'Метод __str__ должен возвращать название группы'
        )

    def test_post_str(self):
        """Проверка метода __str__ для модели Post"""
        expected = '123456789012345'
        self.assertEqual(
            str(ModelTest.post),
            expected,
            'Метод __str__ должен возвращать первые 15 символов поста'
        )

    def test_comment_str(self):
        """Проверка метода __str__ для модели Comment"""
        expected = 'Тестовый коммен'
        self.assertEqual(
            str(ModelTest.comment),
            expected,
            'Метод __str__ должен возвращать первые 15 символов комментария'
        )

    def test_verbose_names(self):
        """Проверка наличия человекочитаемых имён для полей модели Post"""
        post = ModelTest.post
        expected_verbose_names = {
            'text': 'Содержимое поста',
            'created': 'Дата создания',
            'author': 'Автор поста',
            'group': 'Группа'
        }
        for field_name, verbose_name in expected_verbose_names.items():
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    post._meta.get_field(field_name).verbose_name,
                    verbose_name
                )

    def test_help_texts(self):
        """Проверка наличия подсказок у полей модели Post"""
        post = ModelTest.post
        expected_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой принадлежит автор'
        }
        for field_name, help_text in expected_help_texts.items():
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    post._meta.get_field(field_name).help_text,
                    help_text
                )
