from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Group, Post
from http import HTTPStatus


User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем запись в БД."""
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_1,
            text='Тестовая группа',
        )

    def setUp(self):
        """Создаеем пользователей."""
        self.guest_client = Client()
        self.user = PostURLTest.user_1
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_urls_is_availiable(self):
        url_dict = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for url, status in url_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_urls_only_login(self):
        url_dict = {
            '/create/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.OK,
        }
        for url, status in url_dict.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_redirect_anonymous_on_admin_login(self):
        """Страницы /create/ и /posts/1/edit/ перенаправят анонимного пользователя
        на страницу логина.
        """
        url_dict = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/edit/': '/auth/login/?next=/posts/1/edit/',
        }
        for url, redirect_url in url_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_urls_uses_correct_template_for_all(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_login(self):
        templates_url_names = {
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_urls(self):
        url_dict = {
            '/': HTTPStatus.OK,
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for url, status in url_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)
