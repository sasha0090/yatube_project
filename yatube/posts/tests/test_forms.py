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
        cls.user = User.objects.create_user(username="user")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание"
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка создания поста"""
        form_data = {"text": "Тестовый пост", "group": self.group.id}

        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )

        self.assertRedirects(
            response, reverse(
                "posts:profile", kwargs={"username": self.user.username})
        )

        post = Post.objects.first()

        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group_id, form_data["group"])
        self.assertEqual(post.author, self.user)

    def test_edit_post(self):
        """Проверка редактирования поста"""
        post = Post.objects.create(
            author=self.user, text="Тестовый пост", group=self.group
        )

        form_data = {"text": "Изменили текст", "group": self.group.id}
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": post.id}),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": post.id})
        )

        changed_post = Post.objects.first()
        self.assertEqual(changed_post.id, post.id)
        self.assertEqual(changed_post.text, form_data["text"])
        self.assertEqual(changed_post.group_id, form_data["group"])

    def test_anon_user_cant_posting(self):
        """Проверка прав на создание поста"""
        guest_client = Client()

        form_data = {
            "text": "Этот пост не должен быть создан",
            "group": self.group.id
        }

        response = guest_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        post = Post.objects.first()

        expected_url = (reverse("users:login") + "?next="
                        + reverse("posts:post_create"))
        self.assertRedirects(response, expected_url)
        self.assertIsNone(post)
