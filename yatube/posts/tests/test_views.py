import math
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание"
        )

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
        cls.post_data = {
            "text": (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
                "Praesent ut scelerisque velit. Nam quis suscipit elit."
            ),
            "group": cls.group,
            "author": cls.author,
            "image": uploaded,
        }
        cls.post = Post.objects.create(
            author=cls.post_data["author"],
            text=cls.post_data["text"],
            group=cls.post_data["group"],
            image=cls.post_data["image"],
        )

        cls.pages_list_urls = [
            reverse("posts:index"),
            reverse("posts:profile", kwargs={"username": cls.author.username}),
            reverse("posts:group_list", kwargs={"slug": cls.group.slug}),
        ]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """Проверяем, что страница использует корректный шаблон"""
        templates_url_address = {
            reverse("posts:index"): "posts/index.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:group_list", kwargs={"slug": f"{self.group.slug}"}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": f"{self.author.username}"}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": f"{self.post.id}"}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": f"{self.post.id}"}
            ): "posts/create_post.html",
        }

        for reverse_name, template in templates_url_address.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_show_correct_context_in_list(self):
        """Проверка формирования шаблона с правильным контекстом
        на страницах со списком"""

        for url in self.pages_list_urls:
            response = self.authorized_client.get(url)
            context = response.context.get("page_obj").object_list[0]

            self.assertTrue(bool(context.image))

            context_detail = {
                context.text: self.post_data["text"],
                context.author.username: self.post_data["author"].username,
                context.group.title: self.post_data["group"].title,
            }

            for context, expected in context_detail.items():
                with self.subTest(url=url, context=context):
                    self.assertEqual(context, expected)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )

        context = response.context["post"]

        self.assertTrue(bool(context.image))
        context_detail = {
            context.text: self.post_data["text"],
            context.author.username: self.post_data["author"].username,
            context.group.title: self.post_data["group"].title,
        }

        for context, expected in context_detail.items():
            with self.subTest(context=context):
                self.assertEqual(context, expected)

    def test_comment_show_correct_context_on_post_page(self):
        """Правильно отображается на странице поста"""
        text = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
            "Praesent ut scelerisque velit. Nam quis suscipit elit."
        )
        Comment.objects.create(
            post=self.post,
            author=self.author,
            text=text,
        )

        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )

        context = response.context["comments"].first()
        context_detail = {
            context.post.id: self.post.id,
            context.text: text,
            context.author.username: self.author.username,
        }

        for context, expected in context_detail.items():
            with self.subTest(context=context):
                self.assertEqual(context, expected)

    def test_new_post_show_correct(self):
        """Проверка создания нового поста и отображения на страницах"""
        group2 = Group.objects.create(
            title="Тестовая группа2",
            slug="test-slug2",
            description="Тестовое описание"
        )

        post_text = "Тестовый пост 2"
        Post.objects.create(
            author=self.author, text=post_text, group=self.group
        )

        for url in self.pages_list_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                post = response.context.get("page_obj").object_list[0]
                self.assertEqual(post.text, post_text)

        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": group2.slug})
        )
        self.assertEqual(len(response.context.get("page_obj").object_list), 0)

    def test_post_create_show_correct_context(self):
        """Шаблон создания и редактирование поста
        сформирован с правильными полями"""
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        post_urls = {
            "post_create": reverse("posts:post_create"),
            "post_edit": reverse(
                "posts:post_edit", kwargs={"post_id": self.post.id}
            ),
        }

        for name, url in post_urls.items():
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(name=name, value=value):
                    form_field = response.context["form"].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_cache_index_page(self):
        """Тест работы кэша"""
        post2 = Post.objects.create(
            author=self.author,
            text="Тест кэша")

        url = reverse("posts:index")

        response = self.authorized_client.get(url)
        post2.delete()
        response_old = self.authorized_client.get(url)
        self.assertEqual(response.content, response_old.content)

        cache.clear()
        response_new = self.authorized_client.get(url)
        self.assertNotEqual(response_old.content, response_new.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username="author")

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание"
        )

        # Создадим записи в БД для проверки доступности постов
        cls.object_size = 13
        post_objs = []
        for i in range(cls.object_size):
            post_obj = Post(
                author=cls.author, text=f"Тестовая пост {i}", group=cls.group
            )
            post_objs.append(post_obj)
        Post.objects.bulk_create(post_objs)

        cls.page_urls = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": cls.group.slug}),
            reverse("posts:profile", kwargs={"username": cls.author.username}),
        ]

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_page_contains_amount_entries(self):
        """Проверка количество постов на странице"""
        max_pages = math.ceil(
            self.object_size / settings.PAGINATION_OBJECTS_NUM
        )

        for page_url in self.page_urls:
            posts_per_page = settings.PAGINATION_OBJECTS_NUM
            for page in range(1, max_pages + 1):
                with self.subTest(page_url=page_url, page=page):
                    response = self.authorized_client.get(
                        page_url + f"?page={page}"
                    )

                    residual_size = self.object_size - (page * posts_per_page)
                    if residual_size < 0:
                        posts_per_page += residual_size

                    self.assertEqual(
                        len(response.context["page_obj"]), posts_per_page
                    )

    def test_first_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        for page_url in self.page_urls:

            response = self.authorized_client.get(page_url)
            page_objects = response.context.get("page_obj").object_list
            object_size = self.object_size
            for obj in page_objects:
                with self.subTest(page_url=page_url, obj=obj.text):
                    object_size -= 1
                    context_detail = {
                        obj.text: f"Тестовая пост {object_size}",
                        obj.author.username: "author",
                        obj.group.title: "Тестовая группа",
                    }

                for context, expected in context_detail.items():
                    with self.subTest(context=context):
                        self.assertEqual(context, expected)
