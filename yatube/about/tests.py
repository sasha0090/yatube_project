from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class StaticPageUrlsTests(TestCase):
    def setUp(self):
        # Создаем неавторизованного клиента
        self.guest_client = Client()

        self.author = User.objects.create_user(username="author")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.clients = {
            "guest_client": self.guest_client,
            "authorized_client": self.authorized_client,
        }

    def test_urls_available_to_any_client(self):
        """Проверка url доступных любому пользователю"""
        url_addresses = ["/about/author/", "/about/tech/"]

        """Проверка url доступных любому пользователю"""
        url_addresses = ["/about/author/", "/about/tech/"]
        for client in self.clients:
            for url_address in url_addresses:
                with self.subTest(client=client, address=url_address):
                    response = self.clients[client].get(url_address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_static_url_uses_correct_template(self):
        """Проверка urs использует соответствующий шаблон"""
        url_templates = {
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
        }

        for url_address, template in url_templates.items():
            with self.subTest(address=url_address):
                response = self.guest_client.get(url_address)
                self.assertTemplateUsed(response, template)
