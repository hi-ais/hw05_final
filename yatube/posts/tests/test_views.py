import shutil
import tempfile
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django import forms
from ..models import Group, Post, Follow
from django.core.cache import cache
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем запись в БД."""
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='text for test',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаем пользователей."""
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'auth'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Шаблон индекс сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['posts'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group
        post_pub_date_0 = first_object.pub_date
        post_img = first_object.image
        self.assertEqual(post_text_0, PostPagesTest.post.text)
        self.assertEqual(post_author_0, PostPagesTest.user.username)
        self.assertEqual(post_group_0, PostPagesTest.post.group)
        self.assertEqual(post_pub_date_0, PostPagesTest.post.pub_date)
        self.assertEqual(post_img, PostPagesTest.post.image)

    def test_group_list_context(self):
        """Шаблон group list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group
        post_pub_date_0 = first_object.pub_date
        post_img = first_object.image
        self.assertEqual(post_text_0, PostPagesTest.post.text)
        self.assertEqual(post_author_0, PostPagesTest.user.username)
        self.assertEqual(post_group_0, PostPagesTest.post.group)
        self.assertEqual(post_img, PostPagesTest.post.image)
        self.assertEqual(post_pub_date_0, PostPagesTest.post.pub_date)
        self.assertEqual(
            response.context.get('group').title, 'Тестовая группа'
        )
        self.assertEqual(
            response.context.get('group').description, 'Тестовое описание'
        )

    def test_profile_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        profile_img = first_object.image
        self.assertEqual(profile_img, PostPagesTest.post.image)
        self.assertEqual(post_text_0, PostPagesTest.post.text)
        post_count = Post.objects.order_by('author').count()
        self.assertEqual(response.context.get('post_count'), post_count)
        self.assertEqual(
            response.context.get('author').username,
            PostPagesTest.user.username
        )

    def test_post_detail_context(self):
        """Шаблон post detail с правильным контексом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTest.post.id}
            )
        )
        profile_post = response.context['post'].text
        profile_group = response.context['post'].group
        profile_date = response.context['post'].pub_date
        profile_post_count = response.context['author_posts_count']
        post_count = Post.objects.order_by('author').count()
        post_image = response.context['post'].image
        self.assertEqual(post_image, PostPagesTest.post.image)
        self.assertEqual(profile_post, PostPagesTest.post.text)
        self.assertEqual(profile_group, PostPagesTest.post.group)
        self.assertEqual(profile_date, PostPagesTest.post.pub_date)
        self.assertEqual(profile_post_count, post_count)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTest.post.id}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


class PostPaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем запись в БД."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(1, 14):
            cls.post = Post.objects.create(
                text='text %s' % i,
                author=cls.user,
                group=cls.group
            )
            cls.post.save()

    def setUp(self):
        """Создаем пользователей."""
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """paginator на 1ой странице."""
        FIRST_LIST = 10
        paginator_list = {
            reverse('posts:index'): FIRST_LIST,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): FIRST_LIST,
            reverse('posts:profile', kwargs={'username': 'auth'}): FIRST_LIST,
        }
        for page_real, page_exp in paginator_list.items():
            with self.subTest(page_real=page_real):
                response = self.authorized_client.get(page_real)
                first_p = len(response.context['page_obj'])
                self.assertEqual(first_p, page_exp)

    def test_second_page_contains_ten_records(self):
        """padinator на 2ой странице."""
        SECOND_LIST = 3
        paginator_list = {
            (reverse('posts:index') + '?page=2'): SECOND_LIST,
            (reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ) + '?page=2'
            ): SECOND_LIST,
            (reverse(
                'posts:profile',
                kwargs={'username': 'auth'}
            ) + '?page=2'
            ): SECOND_LIST,
        }
        for page_real, page_exp in paginator_list.items():
            with self.subTest(page_real=page_real):
                response = self.authorized_client.get(page_real)
                second_p = len(response.context['page_obj'])
                self.assertEqual(second_p, page_exp)


class FollowUserTest(TestCase):
    def setUp(self):
        """Создаем пользователей."""
        self.guest_client = Client()
        self.user_1 = User.objects.create_user(username='Ais')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)
        self.user_2 = User.objects.create_user(username='Kid Cudi')
        self.user_3 = User.objects.create_user(username='Unfollow')
        self.group = Group.objects.create(
            title='samurai way',
            slug='samurai-way',
            description='Жизнь человека коротка, но имя его вечно'
        )

    def test_auth_user_can_follow(self):
        """Авториз поль-ль может подписывать и отписываться."""
        response = self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_2},
            ),
            follow=True
        )
        is_follow = Follow.objects.filter(user=self.user_1,
                                          author=self.user_2).exists()
        self.assertEqual(is_follow, True)
        self.assertIn("Отписаться", response.content.decode())

    def test_auth_user_can_unfollow(self):
        response = self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_2},
            ),
            follow=True
        )
        is_follow = Follow.objects.filter(user=self.user_1,
                                          author=self.user_2).exists()
        self.assertEqual(is_follow, False)
        self.assertIn("Подписаться", response.content.decode())

    def test_new_post_in_follow_index(self):
        new_post_follow = Post.objects.create(
            text='New post for test following',
            author=self.user_2,
            group=self.group
        )
        post_unfollow = Post.objects.create(
            text='Not follow test',
            author=self.user_3
        )
        self.follow = Follow.objects.create(user=self.user_1,
                                            author=self.user_2)
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        check_context = response.context['follow_post'][0]
        check_content = response.content.decode()
        self.assertEqual(check_context.text, new_post_follow.text)
        self.assertNotEqual(check_content, post_unfollow.text)
        self.assertIn("New post for test following", response.content.decode())


class TestCacheIndex(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.user = User.objects.create_user(username='Hamilton')
        self.authorized_client.force_login(self.user)
        self.post_1 = Post.objects.create(
            text='lalala',
            author=self.user
        )

    def test_cache_is_ok(self):
        """Работает ли кэширование главной страницы."""
        self.post_2 = Post.objects.create(
            text='test text',
            author=self.user
        )
        response_1 = self.authorized_client.get(reverse('posts:index'))
        first_render = response_1.content
        Post.objects.filter(text='test text').delete()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEquals(first_render, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEquals(first_render, response_3.content)
