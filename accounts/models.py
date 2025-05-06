import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from modules.helpers.mixins import TimeStampActiveMixin


class MyUser(AbstractUser, TimeStampActiveMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone = PhoneNumberField(null=True, blank=True, unique=True, db_index=True)
    language_preferred = models.CharField(
        max_length=7, choices=settings.LANGUAGES, default="en", blank=True, null=True
    )
    email = models.EmailField(
        _("email address"), blank=True, null=True, unique=True, db_index=True
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ("-is_active", "-created_at")

    @property
    def render_sbadmin2_ui(self):
        # TODO: TEMPLATE write this logic
        return True

    @property
    def name(self):
        string = self.first_name + " " + self.last_name
        return string.strip()
