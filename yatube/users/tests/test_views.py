from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="author")

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """Проверяем, что страница использует корректный шаблон"""
        templates_url_address = {
            reverse("users:only_user"): "users/check_anon.html",
            reverse("users:only_anon"): "users/check_authenticated.html",
            reverse("users:password_change"):
                "users/password_change_form.html",
            reverse("users:password_change_done"):
                "users/password_change_done.html",
            reverse("users:password_reset_done"):
                "users/password_reset_done.html",
            reverse(
                "users:password_reset_complete"
            ): "users/password_reset_complete.html",
            # Разлогинивает
            reverse("users:logout"): "users/logged_out.html",
            reverse("users:signup"): "users/signup.html",
            reverse("users:login"): "users/login.html",
            reverse("users:password_reset"): "users/password_reset_form.html",
        }

        for reverse_name, template in templates_url_address.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_signup_page_show_correct_context(self):
        """Шаблон регистрации сформирован с правильными полями"""
        form_fields = {
            "first_name": forms.fields.CharField,
            "last_name": forms.fields.CharField,
            "username": forms.fields.CharField,
            "email": forms.fields.EmailField,
        }

        response = self.guest_client.get(reverse("users:signup"))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_login_page_show_correct_context(self):
        """Шаблон входа сформирован с правильными полями"""
        form_fields = {
            "username": UsernameField,
            "password": forms.fields.CharField,
        }

        response = self.guest_client.get(reverse("users:login"))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                print(response.context["form"].fields[value])
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)
