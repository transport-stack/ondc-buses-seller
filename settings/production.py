from .base import *
import os
from datetime import timedelta

DEBUG = False
os.environ['DEBUG'] = str('0')

print("----- Running App in PRODUCTION Mode -----")

SECRET_KEY = os.getenv("SECRET_KEY")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(" ")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASS"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        'CONN_MAX_AGE': 300,
        'OPTIONS': {
            'options': '-c statement_timeout=30000',
        },
    },
    "transit_db": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",  # or any other engine
        "NAME": os.getenv("TRANSIT_DB_NAME"),
        "USER": os.getenv("TRANSIT_DB_USER"),
        "PASSWORD": os.getenv("TRANSIT_DB_PASS"),
        "HOST": os.getenv("TRANSIT_DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        'CONN_MAX_AGE': 300,
        'OPTIONS': {
                    'options': '-c statement_timeout=40000',
                },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': CELERY_BROKER_URL,
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django", "django.log"),
            "when": "D",  # this specifies the interval
            "interval": 1,  # defaults to 1, only necessary for other values
            "backupCount": 5,  # how many backup files to keep
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
