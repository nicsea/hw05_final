from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_author = User.objects.create_user(username='test_author')
        not_author = User.objects.create_user(username='not_author')

        cls.authorised_users = {
            'test_author': test_author,
            'not_author': not_author
        }

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
            author=cls.authorised_users['test_author'],
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()

        self.test_author = Client()
        self.test_author.force_login(
            self.authorised_users['test_author'])

        self.not_author = Client()
        self.not_author.force_login(
            self.authorised_users['not_author'])

    def test_urls_wo_authorisation_available(self):
        """Страницы index, profile, post_detail, group_list доступны
        любому пользователю.
        """
        url_list = ['/',
                    '/group/test_slug/',
                    '/profile/test_author/',
                    '/posts/1/'
                    ]

        for address in url_list:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_anonymous(self):
        """Страницы create, post_edit редиректят анонимного пользователя."""
        url_list_redirect = ['/create/',
                             '/posts/1/edit/',
                             ]

        for address in url_list_redirect:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_edit_url_redirect_not_author(self):
        """Страница post_edit перенаправляет не автора."""
        response = self.not_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_url_available_if_authorised(self):
        """Страница create доступна авторизованному пользователю."""
        response = self.not_author.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_available_if_author(self):
        """Страница post_edit доступна автору."""
        response = self.test_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_no_page_url_returns_404(self):
        """Несуществующая страница возвращает 404 ошибку"""
        response = self.guest_client.get('/no_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/test_author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.test_author.get(address)
                self.assertTemplateUsed(response, template)
