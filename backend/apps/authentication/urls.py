"""Authentication routes, mounted at ``/api/auth/``."""

from django.urls import path

from apps.authentication.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    RefreshView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
