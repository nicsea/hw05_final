import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Group, Post, Follow
from django.core.cache import cache

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        first_author = User.objects.create_user(username='first_author')
        second_author = User.objects.create_user(username='second_author')
        third_author = User.objects.create_user(username='third_author')

        cls.authors = {
            'first_author': first_author,
            'second_author': second_author,
            'third_author': third_author
        }

        first_group = Group.objects.create(
            title='Тестовая группа_1',
            slug='test_slug_1',
            description='Тестовое описание_1',
        )

        second_group = Group.objects.create(
            title='Тестовая группа_2',
            slug='test_slug_2',
            description='Тестовое описание_2',
        )
        third_group = Group.objects.create(
            title='Тестовая группа_3',
            slug='test_slug_3',
            description='Тестовое описание_3',
        )

        cls.group = {
            'first_group': first_group,
            'second_group': second_group,
            'third_group': third_group
        }

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text='Тестовый пост_1',
            author=cls.authors['first_author'],
            group=cls.group['first_group'],
            image=cls.uploaded,
        )

        cls.test_values = {
            'text': 'Тестовый пост_2',
            'author': 'second_author',
            'slug': 'test_slug_2',
            'description': 'Тестовое описание_2',
            'group': 'Тестовая группа_2',
            'post_id': 2,
        }

        for i in range(0, 13):
            for author in [cls.authors['second_author'],
                           cls.authors['third_author']]:
                for group in [cls.group['third_group'],
                              cls.group['second_group']]:
                    Post.objects.create(
                        text=f'Пост {Post.objects.count() + 1}',
                        author=author,
                        group=group
                    )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # очищаем кэш для каждого теста и авторизуем second_author
        cache.clear()
        self.second_author = Client()
        self.second_author.force_login(self.authors['second_author'])

    # добавлено на время тестирования дебага
    # def tearDown(self):
    #     shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug_1'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'first_author'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 2}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 2}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.second_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context_and_paginator(self):
        """Шаблон index сформирован с правильным контекстом и
        paginator работает корректно.
        """
        response_first_page = self.second_author.get(reverse('posts:index'))

        response_last_page = self.second_author.get(
            reverse('posts:index') + '?page=6')

        page_context_first_page = response_first_page.context['page_obj']
        page_context_last_page = response_last_page.context['page_obj']

        post = page_context_first_page[0]
        self.assertIsInstance(post, Post)
        self.assertIsNotNone(post.group)

        self.assertEqual(len(page_context_first_page), 10)
        self.assertEqual(len(page_context_last_page), 3)

    def test_group_list_page_show_correct_context_and_paginator(self):
        """Шаблон group_list сформирован с правильным контекстом и
        paginator работает корректно."""
        response_first_page = self.second_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_2'}))

        response_last_page = self.second_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_2'})
            + '?page=3')

        page_context_first_page = response_first_page.context['page_obj']
        page_context_last_page = response_last_page.context['page_obj']

        post = page_context_first_page[0]

        self.assertIsInstance(post, Post)
        self.assertEqual(post.group.title, self.test_values['group'])
        self.assertEqual(post.group.slug, self.test_values['slug'])
        self.assertEqual(post.group.description,
                         self.test_values['description'])

        self.assertEqual(len(page_context_first_page), 10)
        self.assertEqual(len(page_context_last_page), 6)

    def test_post_exists_correct_group(self):
        response_in_check_group = self.second_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_1'}))
        response_not_in_check_group = self.second_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_2'}))

        page_in_check = response_in_check_group.context['page_obj']
        page_not_check = response_not_in_check_group.context['page_obj']

        self.assertIn(self.post, page_in_check.paginator.object_list)
        self.assertNotIn(self.post, page_not_check.paginator.object_list)

    def test_post_exists_at_index_profile_group_list(self):
        response_index = self.second_author.get(reverse('posts:index'))
        response_grouplist = self.second_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_1'}))
        response_profile = self.second_author.get(
            reverse('posts:profile', kwargs={'username': 'first_author'}))

        for response in [response_index, response_grouplist, response_profile]:
            with self.subTest(response=response):
                post_list = response.context['page_obj'].paginator.object_list
                self.assertIn(self.post, post_list)

    def test_profile_page_show_correct_context_and_paginator(self):
        """Шаблон profile сформирован с правильным контекстом и
        paginator работает корректно.
        """
        response_first_page = self.second_author.get(
            reverse('posts:profile', kwargs={'username': 'second_author'}))

        response_last_page = self.second_author.get(
            reverse('posts:profile', kwargs={'username': 'second_author'})
            + '?page=3')

        page_context_first_page = response_first_page.context['page_obj']
        page_context_last_page = response_last_page.context['page_obj']

        post = page_context_first_page[0]
        self.assertIsInstance(post, Post)
        self.assertIsNotNone(post.group)
        self.assertEqual(post.author.username, self.test_values['author'])

        self.assertEqual(len(page_context_first_page), 10)
        self.assertEqual(len(page_context_last_page), 6)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.second_author.get(
            reverse('posts:post_detail', kwargs={'post_id': '2'}))
        post = response.context['post']
        self.assertIsInstance(post, Post)
        self.assertEqual(post.id, self.test_values['post_id'])

    def test_post_create_edit_page_show_correct_context(self):
        """Шаблон create, post_edit сформирован с правильным контекстом."""
        response_edit = self.second_author.get(
            reverse('posts:post_edit', kwargs={'post_id': 2}))
        response_create = self.second_author.get(
            reverse('posts:post_create'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                for response in [response_edit, response_create]:
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_image_exists_in_post_context(self):
        """Для поста с картинкой изображение передаётся в context"""
        response_index = self.second_author.get(reverse('posts:index'))
        response_detail = self.second_author.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        response_group_list = self.second_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_1'}))
        response_profile = self.second_author.get(
            reverse('posts:profile', kwargs={'username': 'first_author'}))

        for response in [response_index,
                         response_detail,
                         response_group_list,
                         response_profile,
                         ]:
            with self.subTest(response=response):
                if response != response_detail:
                    paginator = response.context['page_obj'].paginator
                    post = paginator.object_list.get(id=1)
                else:
                    post = response.context['post']
                self.assertEqual(self.post.image, post.image)

    def test_cache_index(self):
        """Тест работы кэша"""
        self.second_author.get(reverse('posts:index'))
        post_name_cache = 'Тест кэша'
        Post.objects.create(
            text=post_name_cache,
            author=self.authors['second_author'],
        )
        # Проверяем что после первого запроса в контенте страницы
        # нет созданного поста
        response = self.second_author.get(reverse('posts:index'))
        content = response.content.decode()
        self.assertNotIn(post_name_cache, content)

        # Сбрасываем кэш и повторяем запрос, и проверяем,
        # что пост уже есть на странице index
        cache.clear()
        response = self.second_author.get(reverse('posts:index'))
        content = response.content.decode()
        self.assertIn(post_name_cache, content)
        Post.objects.filter(text=post_name_cache).delete()

    def test_follow_unfollow_authorised(self):
        # проверяем начально количество подписок пользователя
        follow_initial = Follow.objects.filter(
            user_id=self.authors['second_author'].id).count()
        # подписываемся на first_author
        self.second_author.get(reverse('posts:profile_follow',
                                       kwargs={'username': 'first_author'}))
        follow_added = Follow.objects.filter(
            user_id=self.authors['second_author'].id).count()
        self.assertEqual(follow_initial + 1, follow_added)
        # отписываемся от first_author
        self.second_author.get(reverse('posts:profile_unfollow',
                                       kwargs={'username': 'first_author'}))
        follow_deleted = Follow.objects.filter(
            user_id=self.authors['second_author'].id).count()
        self.assertEqual(follow_initial, follow_deleted)

    def test_post_appear_follower(self):
        # Два авторизованных пользователя - second_author, third_author.
        # second_author подписан, third_author не подписан. Проверяем, что у
        # second_author запись в follow_index появляется, а у third_author нет
        self.third_author = Client()
        self.third_author.force_login(self.authors['third_author'])
        self.second_author.get(reverse('posts:profile_follow',
                                       kwargs={'username': 'first_author'}))
        post_text = 'Тестовый пост для фолловеров'
        Post.objects.create(
            text=post_text,
            author=self.authors['first_author'],
        )
        response_follower = self.second_author.get(
            reverse('posts:follow_index'))
        content_follower = response_follower.content.decode()
        self.assertIn(post_text, content_follower)

        response_not_follower = self.third_author.get(
            reverse('posts:follow_index'))
        content_not_follower = response_not_follower.content.decode()
        self.assertNotIn(post_text, content_not_follower)
        Post.objects.filter(text=post_text).delete()
