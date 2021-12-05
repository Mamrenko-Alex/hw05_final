from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):
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
        )

    def setUp(self):
        self.guest_client = Client()
        self.request_user = Client()
        self.request_user.force_login(URLTests.user)
        self.index = '/'
        self.group = f'/group/{URLTests.group.slug}/'
        self.profile = f'/profile/{URLTests.user}/'
        self.post_detail = f'/posts/{URLTests.post.id}/'
        self.post_create = '/create/'
        self.post_update = f'/posts/{URLTests.post.id}/edit/'

    def test_urls_uses_correct_template(self):
        templatres_urls_names = {
            'posts/index.html': self.index,
            'posts/group_list.html': self.group,
            'posts/profile.html': self.profile,
            'posts/post_detail.html': self.post_detail,
            'posts/create_post.html': self.post_create,
            'posts/update_post.html': self.post_update,
        }
        for template, adress in templatres_urls_names.items():
            with self.subTest(adress=adress):
                response = self.request_user.get(adress)
                self.assertTemplateUsed(response, template)

    def test_pages_status_code_guest_user(self):
        url_and_status = {
            self.index: HTTPStatus.OK,
            self.group: HTTPStatus.OK,
            self.profile: HTTPStatus.OK,
            self.post_detail: HTTPStatus.OK,
            self.post_create: HTTPStatus.FOUND,
            self.post_update: HTTPStatus.FOUND,
        }
        for adress, status in url_and_status.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_pages_status_code_request_user(self):
        url_and_status = {
            self.index: HTTPStatus.OK,
            self.group: HTTPStatus.OK,
            self.profile: HTTPStatus.OK,
            self.post_detail: HTTPStatus.OK,
            self.post_create: HTTPStatus.OK,
            self.post_update: HTTPStatus.OK,
        }
        for adress, status in url_and_status.items():
            with self.subTest(adress=adress):
                response = self.request_user.get(adress)
                self.assertEqual(response.status_code, status)

    def test_unexisting_page(self):
        response = self.guest_client.get(
            '/unexisting_page/'
        )
        template = 'core/404.html'
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, template)
