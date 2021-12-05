from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        verbose_name='текст поста',
        help_text='напишите то о чем думаете'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа к которой будет '
                  'относиться пост, необязательно'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        help_text='Добавьте изображиние',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Придумайте название для сообщества'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Уникальная ссылка на группу',
        help_text='Можно задать любой адресс, главное '
                  'что бы он не был занят другим пользователем'
    )
    description = models.TextField(
        verbose_name='Описания сообщества',
        help_text='Тут могут быть правила, описания группы и т.д.'
    )

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Коментируемый пост',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
        help_text='добавляется автоматически'
    )
    text = models.TextField(
        verbose_name='коментарий к посту',
        help_text='выскажите своё мнение'
    )
    created = models.DateTimeField(
        verbose_name='Дата публикации',
        help_text='добавляется автоматически',
        auto_now_add=True
    )

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='following'
    )
