from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UserUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="author")

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.clients = {
            "guest_client": self.guest_client,
            "authorized_client": self.authorized_client,
        }

    def test_urls_available_to_client(self):
        """Проверка url доступных для анонимов"""
        anon_client_status_codes = {
            "/auth/signup/": HTTPStatus.OK,
            "/auth/login/": HTTPStatus.OK,
            "/auth/password_reset/": HTTPStatus.OK,
            "/auth/password_reset/done/": HTTPStatus.OK,
            "/auth/password_reset/complete/": HTTPStatus.OK,
            "/auth/logout/": HTTPStatus.OK,
            "/auth/password_change/": HTTPStatus.FOUND,
            "/auth/password_change/done/": HTTPStatus.FOUND,
        }
        auth_client_status_codes = {
            "/auth/signup/": HTTPStatus.FOUND,
            "/auth/login/": HTTPStatus.FOUND,
            "/auth/password_reset/": HTTPStatus.FOUND,
            "/auth/password_reset/done/": HTTPStatus.OK,
            "/auth/password_reset/complete/": HTTPStatus.OK,
            "/auth/password_change/": HTTPStatus.OK,
            "/auth/password_change/done/": HTTPStatus.OK,
            "/auth/logout/": HTTPStatus.OK,
        }

        clients_status_codes = {
            "guest_client": anon_client_status_codes,
            "authorized_client": auth_client_status_codes,
        }

        for client, status_codes in clients_status_codes.items():
            for url, status_code in status_codes.items():
                with self.subTest(client=client, url=url):
                    response = self.clients[client].get(url)
                    self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """Проверка url использует соответствующий шаблон"""
        templates_url_address = {
            "/auth/only_user/": "users/check_anon.html",
            "/auth/only_anon/": "users/check_authenticated.html",
            "/auth/password_change/": "users/password_change_form.html",
            "/auth/password_change/done/": "users/password_change_done.html",
            "/auth/password_reset/done/": "users/password_reset_done.html",
            "/auth/password_reset/complete/":
                "users/password_reset_complete.html",
            # Разлогинивает
            "/auth/logout/": "users/logged_out.html",
            "/auth/signup/": "users/signup.html",
            "/auth/login/": "users/login.html",
            "/auth/password_reset/": "users/password_reset_form.html",
        }

        for address, template in templates_url_address.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_non_exist_url(self):
        """Проверка не существующего url"""
        non_existent_address = "/auth/non_exist_address/"
        with self.subTest(non_existent_address=non_existent_address):
            response = self.authorized_client.get(non_existent_address)
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
