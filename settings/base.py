import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv('DEBUG') == '1'

BASE_DIR = Path(__file__).resolve().parent.parent

if os.path.exists(os.path.join('envs', '.env.common')):
    load_dotenv(dotenv_path=f"envs/.env.common")
else:
    print("----- .env.common not found -----")

IS_CELERY_ENABLED = os.getenv("IS_CELERY_ENABLED", "True") == "True"
CELERY_BROKER_URL = os.getenv("REDIS_HOST", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# set allowed host from ALLOWED_HOSTS env var
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# import secret key from env var
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure$@")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "compressor",
    "crispy_forms",
    "django_filters",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "ui",
    "accounts",
    "rangefilter",
    "main",
    "import_export",
    "django_celery_beat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

CSRF_TRUSTED_ORIGINS = [
    'https://dev-ondc-ticketing-api.delhitransport.in',
    'https://pre-prod-ondc-ticketing-api-delhi.transportstack.in',
    'https://prod-ondc-ticketing-api-delhi.transportstack.in',
]
CSRF_COOKIE_SECURE = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
    # "chartr": {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": BASE_DIR / "updated_db.sqlite3",
    # },

}


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'ui', "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.is_mobile_context",
                "core.context_processors.sbadmin2_sidebar_data",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
AUTH_USER_MODEL = "accounts.MyUser"
CRISPY_TEMPLATE_PACK = "bootstrap4"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DATETIME_FORMAT": "iso-8601",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

SITE_ID = 1
SOCIALACCOUNT_LOGIN_ON_GET = True

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "https://cdn-001.chartr.in/ptx-api.chartr.in/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_REDIRECT_URL = "login_redirects"

# ELK CREDENTIALS
ELK_SECRET_TOKEN = str(os.getenv("ELK_SECRET_TOKEN"))
ELK_SERVER_URL = str(os.getenv("ELK_SERVER_URL"))
ELASTIC_APM_ENABLED = False
try:
    ELASTIC_APM_ENABLED = os.getenv("ELASTIC_APM_ENABLED")
    if ELASTIC_APM_ENABLED.lower() == "true":
        ELASTIC_APM_ENABLED = True
    else:
        ELASTIC_APM_ENABLED = False
except Exception:
    logging.info("ELASTIC_APM_ENABLED .env read error")
if ELASTIC_APM_ENABLED:
    INSTALLED_APPS.append("elasticapm.contrib.django")

ELASTIC_APM = {
    "SERVICE_NAME": "chartr-ondc-seller-api-service",
    "SERVER_URL": f"{ELK_SERVER_URL}",
    "SERVER_CERT": f"{BASE_DIR}/elk.chartr.in.crt",
    "SECRET_TOKEN": f"{ELK_SECRET_TOKEN}",
    "SERVER_TIMEOUT": "5s",
    "LOG_LEVEL": "critical",
    "CLOUD_PROVIDER": False,
    "DEBUG": DEBUG,
    "ELASTIC_APM_ENABLED": ELASTIC_APM_ENABLED,
}

PHONENUMBER_DEFAULT_REGION = "IN"
