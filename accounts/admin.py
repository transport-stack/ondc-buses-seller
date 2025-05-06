from django.contrib import admin
from import_export.admin import ExportActionMixin

from accounts.models import MyUser


@admin.register(MyUser)
class MyUserAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "uuid",
        "pk",
        "username",
        "name",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
        "created_at",
        "updated_at",
        "last_login",
    )
    search_fields = ("uuid", "pk", "username", "name", "email")
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )
    fieldsets = (
        (
            "Data",
            {
                "fields": (
                    "uuid",
                    "pk",
                    "username",
                    "name",
                    "email",
                    "is_active",
                )
            },
        ),
        (
            "Staff Permissions",
            {
                "fields": (
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important Dates",
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )
    readonly_fields = (
        "last_login",
        "date_joined",
        "created_at",
        "updated_at",
        "pk",
        "uuid",
    )

    class Meta:
        model = MyUser


admin.site.disable_action("delete_selected")
