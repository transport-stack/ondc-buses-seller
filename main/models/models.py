from django.db import models


class ActiveMixin(models.Model):
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class DateTimeMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
