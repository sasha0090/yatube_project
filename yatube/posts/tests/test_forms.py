from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание"
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        form_data = {"text": "Тестовый пост", "group": self.group.id}

        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )

        self.assertRedirects(
            response, reverse(
                "posts:profile", kwargs={"username": self.user.username})
        )
        self.assertTrue(
            Post.objects.filter(
                id=1, text="Тестовый пост", group=self.group.id
            ).exists()
        )

    def test_edit_post(self):
        post = Post.objects.create(
            author=self.user, text="Тестовый пост", group=self.group
        )
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": post.id}),
            data={"text": "Изменили текст", "group": self.group.id},
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": post.id})
        )
        self.assertTrue(
            Post.objects.filter(
                id=1,
                text="Изменили текст",
                group=self.group).exists()
        )
