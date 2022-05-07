from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView

from core.check_access import only_anon_view

from .forms import CreationForm


def only_user_page(request):
    return render(request, "users/check_anon.html")


def only_anon_page(request):
    return render(request, "users/check_authenticated.html")


@method_decorator(only_anon_view, name="dispatch")
class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy("posts:index")
    template_name = "users/signup.html"


@method_decorator(only_anon_view, name="dispatch")
class MyLoginView(auth_views.LoginView):
    template_name = "users/login.html"


class MyLogoutView(auth_views.LogoutView):
    template_name = "users/logged_out.html"


@method_decorator(only_anon_view, name="dispatch")
class MyPasswordResetView(auth_views.PasswordResetView):
    template_name = "users/password_reset_form.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("users:password_reset_done")


@method_decorator(only_anon_view, name="dispatch")
class MyPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")


@method_decorator(login_required, name="dispatch")
class MyPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "users/password_change_form.html"
    success_url = reverse_lazy("users:password_change_done")
