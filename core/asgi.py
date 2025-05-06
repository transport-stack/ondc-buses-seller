"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    print('set DJANGO_SETTINGS_MODULE first.')
    exit(1)

application = get_asgi_application()
