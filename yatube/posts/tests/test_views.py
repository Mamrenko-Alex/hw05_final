import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

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
        ''' Страница на сайте использует правильный шаблон.'''
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
            ),
            'posts/follow.html': reverse('posts:follow_index')
        }
        for template_name, reverse_name in templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.request_user.get(reverse_name)
                self.assertTemplateUsed(response, template_name)

    def test_index_context(self):
        ''' Главная страница сайта.'''
        response = self.request_user.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author
        post_text = first_object.text
        post_image = first_object.image
        self.assertEqual(post_author, PagesTests.post.author)
        self.assertEqual(post_text, PagesTests.post.text)
        self.assertEqual(post_image, PagesTests.post.image)

    def test_follow_index_context(self):
        ''' Страница с постами авторов на которых подписан.'''
        client = User.objects.create_user(username='user')
        self.request_user = Client()
        self.request_user.force_login(client)
        Follow.objects.create(
            author=PagesTests.user,
            user=client
        )
        response = self.request_user.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author
        post_text = first_object.text
        post_image = first_object.image
        self.assertEqual(post_author, PagesTests.post.author)
        self.assertEqual(post_text, PagesTests.post.text)
        self.assertEqual(post_image, PagesTests.post.image)

    def test_group_context(self):
        ''' Страница записей группы.'''
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
        ''' Страница пользователя.'''
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
        ''' Детальная информация о посте.'''
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
        ''' Создание поста.'''
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
        ''' Редактирование поста.'''
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


class CaheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=cls.user,
            text='Тестовый пост длинной более 15 символов',
            group=cls.group
        )

    def setUp(self):
        self.request_user = Client()
        self.request_user.force_login(CaheTests.user)

    def test_cahe_index_context(self):
        ''' Кеширование главной страницы.'''
        response = self.request_user.get(reverse('posts:index'))
        first_content = response.content
        old_post = Post.objects.latest('pub_date')
        old_post.delete()
        second_content = response.content
        self.assertEqual(first_content, second_content)
        cache.clear()
        response_new = self.request_user.get(reverse('posts:index'))
        second_content = response_new.content
        self.assertNotEqual(first_content, second_content)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        post_object = Post(
            author=cls.author,
            text='Тестовый пост длинной более 15 символов',
            group=cls.group
        )
        Post.objects.bulk_create([post_object for num_post in range(13)])

    def setUp(self):
        self.post_per_page = 10
        self.request_user = Client()
        self.request_user.force_login(PaginatorViewsTests.user)
        Follow.objects.create(
            author=PaginatorViewsTests.author,
            user=PaginatorViewsTests.user
        )

    def test_index_ten_posts(self):
        ''' Паджинатор на главной странице.'''
        response = self.request_user.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), self.post_per_page)

    def test_group_ten_posts(self):
        ''' Паджинатор на странице группы.'''
        response = self.request_user.get(reverse(
            'posts:group_list',
            kwargs={'slug': PaginatorViewsTests.group.slug}
        ))
        self.assertEqual(len(response.context['page_obj']), self.post_per_page)

    def test_follow_index_posts(self):
        ''' Паджинатор на странице подписок.'''
        response = self.request_user.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), self.post_per_page)

    def test_profile_ten_posts(self):
        '''  Паджинатор на странице аккаунта пользователя.'''
        response = self.request_user.get(reverse(
            'posts:profile',
            kwargs={'username': PaginatorViewsTests.author}
        ))
        self.assertEqual(len(response.context['page_obj']), self.post_per_page)


class FollowFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост длинной более 15 символов'
        )

    def setUp(self):
        self.guest_user = Client()
        self.request_user = Client()
        self.request_user.force_login(FollowFormTests.user)

    def test_following_author_request_user(self):
        ''' Подписка на автора зарегистрированным пользователем.'''
        subscribers_count = Follow.objects.filter(
            author=FollowFormTests.author).count()
        self.request_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': FollowFormTests.author.username})
        )
        self.assertEqual(
            Follow.objects.filter(author=FollowFormTests.author).count(),
            subscribers_count + 1
        )

    def test_following_author_guest_user(self):
        ''' Подписка на автора анонимным пользователем.'''
        subscribers_count = Follow.objects.filter(
            author=FollowFormTests.author).count()
        following = self.guest_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': FollowFormTests.author.username})
        )
        login_url = reverse('users:login')
        profile_follow_url = reverse(
            'posts:profile_follow',
            kwargs={'username': FollowFormTests.author.username}
        )
        self.assertRedirects(
            following,
            f'{login_url}?next={profile_follow_url}'
        )
        response = self.guest_user.get(reverse('posts:follow_index'))
        posts = response.context
        self.assertIsNone(posts)
        self.assertEqual(
            Follow.objects.filter(author=FollowFormTests.author).count(),
            subscribers_count
        )

    def test_subscriber_not_author(self):
        ''' Пользователь не может подписаться сам на себя.'''
        subscribers_count = Follow.objects.filter(
            author=FollowFormTests.user).count()
        self.request_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': FollowFormTests.user.username})
        )
        self.assertEqual(
            Follow.objects.filter(author=FollowFormTests.user).count(),
            subscribers_count
        )

    def test_unfollowing_author(self):
        ''' Пользователь может отписаться от автора.'''
        Follow.objects.create(
            author=FollowFormTests.author,
            user=FollowFormTests.user
        )
        subscribers_count = Follow.objects.filter(
            author=FollowFormTests.author).count()
        self.request_user.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': FollowFormTests.author.username})
        )
        self.assertEqual(
            Follow.objects.filter(author=FollowFormTests.author).count(),
            subscribers_count - 1
        )
