from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="author")

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text="Тестовая пост",
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.clients = {
            "guest_client": self.guest_client,
            "authorized_client": self.authorized_client,
        }

    def test_urls_available_to_any_client(self):
        """Проверка url доступных любому пользователю"""
        url_address = [
            "/",
            f"/group/{self.group.slug}/",
            f"/profile/{self.author.username}/",
            f"/posts/{self.post.id}/",
        ]

        for client in self.clients:
            for address in url_address:
                with self.subTest(client=client, address=address):
                    response = self.clients[client].get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_available_to_auth_client(self):
        """Проверка url доступных только авторизованному пользователю"""
        urls = ["/create/", f"/posts/{self.post.id}/edit/"]
        clients_status_codes = {
            "guest_client": HTTPStatus.FOUND,
            "authorized_client": HTTPStatus.OK,
        }

        for url in urls:
            for client, status_code in clients_status_codes.items():
                with self.subTest(client=client, url=url):
                    response = self.clients[client].get(url)
                    self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """Проверка url использует соответствующий шаблон"""
        templates_url_address = {
            "/": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.author.username}/": "posts/profile.html",
            "/create/": "posts/create_post.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            f"/posts/{self.post.id}/edit/": "posts/create_post.html",
        }

        for address, template in templates_url_address.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_non_exist_url(self):
        """Проверка не существующего url"""
        non_existent_address = "/non_exist_address/"
        with self.subTest(non_existent_address=non_existent_address):
            response = self.authorized_client.get(non_existent_address)
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_not_author_edit_post(self):
        """Проверка url редактирования чужого поста"""
        not_author = User.objects.create_user(username="not_author")

        second_authorized_client = Client()
        second_authorized_client.force_login(not_author)

        address = f"/posts/{self.post.id}/edit/"
        redirect_address = f"/posts/{self.post.id}/"
        with self.subTest(address=address):
            response = second_authorized_client.get(address)
            self.assertRedirects(response, redirect_address)
