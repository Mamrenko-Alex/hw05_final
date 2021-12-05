from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()


class PostModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длинной более 15 символов',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Комментарий к тестовому посту'
        )

    def test_str_models(self):
        models = {
            PostModelsTest.post: PostModelsTest.post.text[:15],
            PostModelsTest.group: PostModelsTest.group.title,
            PostModelsTest.comment: PostModelsTest.comment.text
        }
        for model, str_method in models.items():
            with self.subTest(str_method=str_method):
                self.assertEqual(str_method, str(model))

    def test_verbose_help_model_post(self):
        fields = {
            'text': 'текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, verbose in fields.items():
            with self.subTest(field=field):
                verbose_name = Post._meta.get_field(field).verbose_name
                self.assertEqual(verbose_name, verbose)

    def test_verbose_help_model_group(self):
        fields = {
            'title': 'Название группы',
            'slug': 'Уникальная ссылка на группу',
            'description': 'Описания сообщества',
        }
        for field, verbose in fields.items():
            with self.subTest(field=field):
                verbose_name = Group._meta.get_field(field).verbose_name
                self.assertEqual(verbose_name, verbose)

    def test_verbose_help_model_commet(self):
        fields = {
            'post': 'Коментируемый пост',
            'author': 'Автор комментария',
            'text': 'коментарий к посту',
            'created': 'Дата публикации'
        }
        for field, verbose in fields.items():
            with self.subTest(field=field):
                verbose_name = Comment._meta.get_field(field).verbose_name
                self.assertEqual(verbose_name, verbose)

    def test_help_text_model_post(self):
        fields = {
            'text': 'напишите то о чем думаете',
            'group': 'Группа к которой будет '
                     'относиться пост, необязательно',
        }
        for field, help_text in fields.items():
            with self.subTest(field=field):
                help_text_field = Post._meta.get_field(field).help_text
                self.assertEqual(help_text_field, help_text)

    def test_help_text_model_group(self):
        fields = {
            'title': 'Придумайте название для сообщества',
            'slug': 'Можно задать любой адресс, главное '
                    'что бы он не был занят другим пользователем',
            'description': 'Тут могут быть правила, описания группы и т.д.',
        }
        for field, help_text in fields.items():
            with self.subTest(field=field):
                help_text_field = Group._meta.get_field(field).help_text
                self.assertEqual(help_text_field, help_text)

    def test_help_text_model_comment(self):
        fields = {
            'text': 'выскажите своё мнение',
            'author': 'добавляется автоматически',
            'created': 'добавляется автоматически'
        }
        for field, help_text in fields.items():
            with self.subTest(field=field):
                help_text_field = Comment._meta.get_field(field).help_text
                self.assertEqual(help_text_field, help_text)
