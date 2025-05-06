from django.contrib.auth.views import LoginView
from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from accounts.views import MyUserViewSet, LogoutView, forgot_password

app_name = "accounts"

router = routers.DefaultRouter()

router.register("user", MyUserViewSet, "user")

urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path(
        "login/",
        LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", LogoutView, name="logout"),
    path("forgot_password/", forgot_password, name="forgot_password"),
]
