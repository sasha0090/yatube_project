from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание"
        )
        cls.post = Post.objects.create(
            author=cls.author, text="Тестовый пост", group=cls.group
        )

    def setUp(self):
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
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

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )

        context = response.context["post"]
        context_detail = {
            context.text: "Тестовый пост",
            context.author.username: "author",
            context.group.title: "Тестовая группа",
        }

        for context, expected in context_detail.items():
            with self.subTest(context=context):
                self.assertEqual(context, expected)

    def test_create_page_show_correct_context(self):
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        response = self.authorized_client.get(reverse("posts:post_create"))

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_post_show_correct(self):
        group2 = Group.objects.create(
            title="Тестовая группа2",
            slug="test-slug2",
            description="Тестовое описание"
        )

        Post.objects.create(
            author=self.author, text="Тестовый пост 2", group=self.group
        )

        page_urls = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.author.username}),
        ]

        for url in page_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                post = response.context.get("page_obj").object_list[0]
                self.assertEqual(post.text, "Тестовый пост 2")

        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": group2.slug})
        )
        self.assertEqual(len(response.context.get("page_obj").object_list), 0)


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
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_two_page_contains_records(self):
        """Проверка:
        Количество постов на первой странице равно 10
        На второй странице должно быть три поста."""
        max_pages = 2

        for page_url in self.page_urls:
            posts_per_page = 10
            for page in range(1, max_pages + 1):
                with self.subTest(page_url=page_url, page=page):
                    response = self.authorized_client.get(
                        reverse("posts:index") + f"?page={page}"
                    )
                    if page == 2:
                        posts_per_page = 3
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
                object_size -= 1
                context_detail = {
                    obj.text: f"Тестовая пост {object_size}",
                    obj.author.username: "author",
                    obj.group.title: "Тестовая группа",
                }

                for context, expected in context_detail.items():
                    with self.subTest(page_url=page_url, obj=str(obj)):
                        self.assertEqual(context, expected)
