import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Group, Post

User = get_user_model()
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка создания поста"""

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )

        form_data = {
            "text": (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
                "Praesent ut scelerisque velit. Nam quis suscipit elit."
            ),
            "group": self.group.id,
            "image": uploaded,
        }

        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )

        self.assertRedirects(
            response, reverse(
                "posts:profile", kwargs={"username": self.user.username}
            )
        )

        post = Post.objects.first()
        self.assertTrue(bool(post.image))

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
            "group": self.group.id}

        response = guest_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        post = Post.objects.first()

        expected_url = (reverse("users:login") + "?next="
                        + reverse("posts:post_create"))
        self.assertRedirects(response, expected_url)
        self.assertIsNone(post)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CommentForm
        cls.user = User.objects.create_user(username="user")

        cls.post = Post.objects.create(
            author=cls.user,
            text="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Проверка создания комментария"""
        text = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
            "Praesent ut scelerisque velit. Nam quis suscipit elit."
        )

        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data={"text": text},
            follow=True,
        )

        self.assertRedirects(
            response, reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            )
        )

        comment = self.post.comment.first()

        self.assertEqual(comment.text, text)
        self.assertEqual(comment.author, self.user)

    def test_anon_user_cant_comments(self):
        """Проверка прав на создание комментария"""
        guest_client = Client()
        text = "Этот комментарий не должен быть создан"

        response = guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data={"text": text},
            follow=True,
        )

        comment = self.post.comment.first()
        expected_url = (
            reverse("users:login")
            + "?next="
            + reverse("posts:add_comment", kwargs={"post_id": self.post.id})
        )

        self.assertRedirects(response, expected_url)
        self.assertIsNone(comment)
