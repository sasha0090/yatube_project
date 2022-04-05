from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст")
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
        related_name="posts",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text
