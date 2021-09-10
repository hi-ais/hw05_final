import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import PostForm
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, Comment
from django.contrib.auth import get_user_model


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Запись в базу данных."""
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
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,

        )
        cls.form = PostForm()
        cls.post_for_edit = Post.objects.create(
            text='Текст до изменения',
            author=cls.user,
            group=cls.group,
        )
        cls.group2 = Group.objects.create(
            title='Измененная группа',
            slug='changed-group',
            description='Описание новой группы',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='новый коммент',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_post_create_by_guest(self):
        """Незарегистрованный пользователь не может создать пост."""
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_post_edit_by_guest(self):
        """Незарегистрированный пользователь не может редактировать пост."""
        response = self.guest_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/edit/'))

    def test_post_create_form_is_valid(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        new_post = {
            'text': f'{PostCreateFormTests.post.text} new',
            'group': PostCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=new_post,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=new_post['text'],
                group=new_post['group'],
            ).exists()
        )

    def test_post_edit_is_valid_and_change_post(self):
        """При редактировании пост изменяется и сохраняется."""
        post_count = Post.objects.count()
        post_for_edit_edited = {
            'text': f'{PostCreateFormTests.post_for_edit.text} отредактирован',
            'group': PostCreateFormTests.group2.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post_for_edit.id}
            ),
            data=post_for_edit_edited,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post_for_edit.id})
        )
        self.assertEqual(Post.objects.count(), post_count)
        post_edited = Post.objects.filter(
            text=post_for_edit_edited['text'],
            author=self.user,
            group=post_for_edit_edited['group']
        )
        self.assertTrue(post_edited.exists())
        self.assertEqual(post_edited.get().group, PostCreateFormTests.group2)

    def test_postform_with_image_exist(self):
        """при отправке поста с картинкой через форму PostForm создаётся
        запись в базе данных."""
        post_count = Post.objects.count()
        # Подготавливаем данные для передачи в форму
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded_1 = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': f'{PostCreateFormTests.post.text} new',
            'group': PostCreateFormTests.group.id,
            'image': uploaded_1
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Запись в базу данных."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='Myname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug_1',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='новый коммент',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user_1 = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)   

    def test_comment_create_by_guest(self):
        """Незарег поль-ль не может написать коммент."""
        redirect_page = '/auth/login/?next=/posts/1/comment'
        response = self.guest_client.get(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertRedirects(response, redirect_page)

    def test_comment_form(self):
        """При добавлении комента он появл на странице поста."""
        comment = {
            'post': CommentFormTest.post,
            'author': CommentFormTest.user,
            'text': 'Новый комментарий!!!!'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=comment,
            follow=True
        )
        comment_1 = response.context['comments'][0]
        comment_text = comment_1.text
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': CommentFormTest.post.id}
        )
        )
        self.assertEqual(comment_text, CommentFormTest.comment.text)
