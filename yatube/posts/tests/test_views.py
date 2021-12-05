import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
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
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий к тестовому посту'
        )

    def setUp(self):
        self.request_user = Client()
        self.request_user.force_login(PagesTests.user)

    def test_pages_uses_correct_template(self):
        templates_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': PagesTests.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': PagesTests.user.username}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': PagesTests.post.pk}
            ),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/update_post.html': reverse(
                'posts:post_edit',
                kwargs={'post_id': PagesTests.post.pk}
            )
        }
        for template_name, reverse_name in templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.request_user.get(reverse_name)
                self.assertTemplateUsed(response, template_name)

    def test_index_context(self):
        response = self.request_user.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author
        post_text = first_object.text
        post_image = first_object.image
        self.assertEqual(post_author, PagesTests.post.author)
        self.assertEqual(post_text, PagesTests.post.text)
        self.assertEqual(post_image, PagesTests.post.image)

    def test_group_context(self):
        response = self.request_user.get(reverse(
            'posts:group_list',
            kwargs={'slug': PagesTests.group.slug})
        )
        first_object = response.context['page_obj'][0]
        post_group = first_object.group
        group_slug = first_object.group.slug
        group_desc = first_object.group.description
        post_image = first_object.image
        self.assertEqual(post_group, PagesTests.post.group)
        self.assertEqual(group_slug, PagesTests.group.slug)
        self.assertEqual(group_desc, PagesTests.group.description)
        self.assertEqual(post_image, PagesTests.post.image)

    def test_profile_context(self):
        response = self.request_user.get(reverse(
            'posts:profile',
            kwargs={'username': PagesTests.user.username})
        )
        first_object = response.context['page_obj'][0]
        post_author = first_object.author
        post_image = first_object.image
        self.assertEqual(post_author, PagesTests.user)
        self.assertEqual(post_image, PagesTests.post.image)

    def test_detail_post_context(self):
        response = self.request_user.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PagesTests.post.pk})
        )
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, forms.fields.CharField)
        post_detail = response.context['post']
        post_comments = response.context['comments'][0]
        post_id = post_detail.pk
        post_image = post_detail.image
        self.assertEqual(post_id, PagesTests.post.pk)
        self.assertEqual(post_image, PagesTests.post.image)
        self.assertEqual(post_comments, PagesTests.comment)

    def test_create_post_context(self):
        response = self.request_user.get(reverse(
            'posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_update_post_context(self):
        response = self.request_user.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': PagesTests.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class CaheTests(BaseCommand):
    def handle(self, *args, **kwargs):
        cache.clear()
        self.stdout.write('Cleared cache\n')

    def test_cahe_index_context(self):
        response = self.request_user.get(reverse(
            'posts:index'
        ))
        first_content = response.content
        old_post = Post.objects.latest('pub_date')
        old_post.delete()
        second_content = response.content
        self.assertEqual(first_content, second_content)
        cache.clear()
        response_new = self.request_user.get(
            reverse('posts:index')
        )
        second_content = response.content
        self.assertNotEqual(first_content, second_content)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        post_object = Post(
            author=PagesTests.post.author,
            text='Тестовый пост длинной более 15 символов',
            group=cls.group
        )
        Post.objects.bulk_create([post_object for num_post in range(13)])

    def setUp(self):
        self.post_per_page = 10
        self.request_user = Client()
        self.request_user.force_login(PagesTests.user)

    def test_index_ten_posts(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), self.post_per_page)

    def test_group_ten_posts(self):
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PaginatorViewsTests.group.slug}
        ))
        self.assertEqual(len(response.context['page_obj']), self.post_per_page)

    def test_profile_ten_posts(self):
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': PaginatorViewsTests.user}
        ))
        self.assertEqual(len(response.context['page_obj']), self.post_per_page)