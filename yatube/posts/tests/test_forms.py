import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(username='first_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.group = Group.objects.create(
            title='Тестовая группа_1',
            slug='test_slug_1',
            description='Тестовое описание_1',
        )
        self.post = Post.objects.create(
            text='Тестовый пост_1',
            author=self.author,
            group=self.group
        )

        self.guest_client = Client()

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_form(self):
        """Валидная форма создает запись в Post"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост_2',
            'group': 1,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'first_author'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                id=2,
                text='Тестовый пост_2',
                image='posts/small.gif',
            ).exists()
        )
        post = Post.objects.get(id=2)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group, self.group)

    def test_create_post_form_not_authorised(self):
        """Валидная форма не дает добавить запись в Post без авторизации"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост_2',
            'group': 1
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_form(self):
        """Валидная форма меняет запись в Post"""
        form_data = {
            'text': 'Тестовый пост_1_изменённый',
            'group': 1
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': '1'}))
        self.assertTrue(
            Post.objects.filter(
                id=1,
                text='Тестовый пост_1_изменённый'
            ).exists()
        )

    def test_comment_post_form_not_authorised(self):
        """Валидная форма не дает добавить комментарий без авторизации"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_comment_form(self):
        """Валидная форма добавляет комментарий к посту"""
        comments_count = Comment.objects.filter(post_id=1).count()
        comment_text = 'Тестовый комментарий'
        form_data = {
            'text': comment_text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': '1'}))
        self.assertEqual(Comment.objects.filter(post_id=1).count(),
                         comments_count + 1)
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        self.assertEqual(response.context['comments'][0].text, comment_text)
