from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
            author=cls.user,
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post

        expected_str_group = 'Тестовая группа'
        expected_str_post = 'абвгдеёжзийклмн'

        self.assertEqual(group.__str__(), expected_str_group)
        self.assertEqual(post.__str__(), expected_str_post)

    def test_help_text(self):
        """Проверяем, что у модели Post корректно работает
        verbose_name и help_text
        """
        post = PostModelTest.post

        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }

        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_verbose_name(self):
        """Проверяем, что у модели Post корректно работает
        verbose_names и help_text
        """
        post = PostModelTest.post

        field_verbose_names = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }

        for field, expected_value in field_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)
