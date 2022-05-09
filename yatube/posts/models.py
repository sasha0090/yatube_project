from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название",
        help_text="Введите название группы"
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="Адрес страницы группы",
        help_text="Введите адрес для страницы группы",
    )
    description = models.TextField(
        verbose_name="Описание", help_text="Введите описание группы"
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст",
        help_text="Введите текст поста"
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        related_name="posts",
        on_delete=models.CASCADE,
    )
    group = models.ForeignKey(
        Group,
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост",
        related_name="posts",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="posts/",
        blank=True)

    class Meta:
        ordering = ["-pub_date", "-id"]

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name="Пост",
        related_name="comment",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        related_name="comment",
        on_delete=models.CASCADE,
    )
    text = models.TextField(
        verbose_name="Текст",
        help_text="Напишите комментарий")
    created = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created", "-id"]

    def __str__(self):
        return self.text[:30]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        related_name="follower",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        related_name="following",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("user", "author")
