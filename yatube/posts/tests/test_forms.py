import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длинной более 15 символов',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.request_user = Client()
        self.request_user.force_login(PostFormTests.user)

    def test_create_post_request_user(self):
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
            'text': 'Новый тестовый пост длинной более 15 символов',
            'group': PostFormTests.group.pk,
            'image': uploaded,
        }
        response = self.request_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.latest('pub_date')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group, PostFormTests.group)
        self.assertEqual(new_post.author, PostFormTests.user)
        self.assertEqual(new_post.image, 'posts/small.gif')

    def test_create_post_guest_user(self):
        posts_count = Post.objects.count()
        url_login = reverse("users:login")
        url_create = reverse('posts:post_create')
        response = self.guest_user.get(
            url_create
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, f'{url_login}?next={url_create}')

    def test_update_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст старого поста',
            'group': PostFormTests.group.pk
        }
        response = self.request_user.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostFormTests.post.pk})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        new_post = Post.objects.latest('pub_date')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group, PostFormTests.group)
        self.assertEqual(new_post.author, PostFormTests.user)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длинной более 15 символов',
            group=cls.group
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_user = Client()
        self.request_user = Client()
        self.request_user.force_login(CommentFormTests.user)

    def test_add_comment_request_user(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий к тестовому посту'
        }
        response = self.request_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': CommentFormTests.post.pk})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        new_comment = Comment.objects.latest('created')
        self.assertEqual(new_comment.text, form_data['text'])
        self.assertEqual(new_comment.author, CommentFormTests.user)

    def test_add_comment_guest_user(self):
        comments_count = Comment.objects.count()
        url_login = reverse('users:login')
        url_add_comment = reverse(
            'posts:add_comment',
            kwargs={'post_id': CommentFormTests.post.pk}
        )
        response = self.guest_user.get(
            url_add_comment
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(response, f'{url_login}?next={url_add_comment}')
