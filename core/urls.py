"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import logging

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from settings.base import DEBUG
from .views import (
    login_redirects,
    index,
    testing_sbadmin2,
)


def healthcheck_view(request):
    logging.info(f"Health check request headers: {request.headers}")

    return HttpResponse("OK", content_type="text/plain", status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login_redirects/", login_redirects, name="login_redirects"),
    path("", index, name="index"),
    # ----------------------------------------------------------------
    # ----------------------------APP URLS----------------------------
    # ----------------------------------------------------------------
    path("", include("main.urls")),
    path("accounts/", include("accounts.urls"), name="accounts"),
    path("healthcheck", healthcheck_view, name="healthcheck"),
]

urlpatterns += [
    path("testing_sbadmin2/", testing_sbadmin2, name="dashboard"),
    path("api/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
