from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("only_user/", views.only_user_page, name="only_user"),
    path("only_anon/", views.only_anon_page, name="only_anon"),
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("login/", views.MyLoginView.as_view(), name="login"),
    path("logout/", views.MyLogoutView.as_view(), name="logout"),
    path(
        "password_change/",
        views.MyPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "password_reset/",
        views.MyPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password_reset_confirm/<uidb64>/<token>/",
        views.MyPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password_reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
