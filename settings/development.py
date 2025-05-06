from settings.base import *
import os
from datetime import timedelta

DEBUG = True
os.environ['DEBUG'] = str('1')


print("----- Running App in DEVELOPMENT Mode -----")

SECRET_KEY = "django-insecure-#=eo81$*nm53y&)i*64vbv(z2+y9_8%0_^2qgijv7*^s3&nl0^"
ALLOWED_HOSTS = ["*"]
EMAIL_HOST_USER = None
EMAIL_HOST_PASSWORD = None

# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=365),
}

if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
        "transit_db": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",  # or any other engine
            "NAME": os.getenv("TRANSIT_DB_NAME"),
            "USER": os.getenv("TRANSIT_DB_USER"),
            "PASSWORD": os.getenv("TRANSIT_DB_PASS"),
            "HOST": os.getenv("TRANSIT_DB_HOST"),
            "PORT": os.getenv("DB_PORT"),
            "CONN_MAX_AGE": 300,
            'OPTIONS': {
                        'options': '-c statement_timeout=30000',
                    },
            }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASS"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT"),
        },
        "transit_db": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",  # or any other engine
            "NAME": os.getenv("TRANSIT_DB_NAME"),
            "USER": os.getenv("TRANSIT_DB_USER"),
            "PASSWORD": os.getenv("TRANSIT_DB_PASS"),
            "HOST": os.getenv("TRANSIT_DB_HOST"),
            "PORT": os.getenv("DB_PORT"),
            "CONN_MAX_AGE": 300,
            'OPTIONS': {
                'options': '-c statement_timeout=30000',
            },
        }
    }

DATABASE_ROUTERS = [BASE_DIR / 'settings.routers.ReadOnlyRouter']

PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s %(message)s"
        },
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(PROJECT_BASE_DIR, "logs", "django",
                                     "django-dev.log"),
            "when": "D",
            "interval": 1,
            "backupCount": 10,  # updated to keep 10 backups
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": True,
        },
        # Consider adding a root logger to capture all logs
        "": {  # Root logger
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
    }
}

CELERY_BROKER_URL = 'redis://localhost:6379/0'
