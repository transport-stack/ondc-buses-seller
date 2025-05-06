from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models.tickets import Ticket, TicketType, TicketUpdate, Agency
from .models.fare_setup import FareBreakup
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import (
    DateRangeFilterBuilder,
)
from main.models import PaymentStatus, TicketStatus
from main.models.pass_setup import Pass, PassType
from django.contrib import messages


class TicketUpdateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    list_display = ("ticket", "created_at", "details")
    search_fields = ("ticket__pnr",)
    list_filter = (("created_at", DateRangeFilterBuilder()),)
    autocomplete_fields = ("ticket",)


class TicketAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "pnr",
        "active",
        "view_ticket_updates",
        "ticket_status",
        "transit_pnr",
        "ticket_type",
        "passenger_count",
        "amount",
        "payment_type",
        "payment_status",
        "created_at",
        "updated_at",
        "valid_till",
        "vehicle_number",
        "link_to_created_for",
        "start_stop_code",
        "end_stop_code",
        "route",
        "subscriber_id",
        "description",
    )
    search_fields = ("pnr", "transit_pnr")
    list_filter = (
        "ticket_status",
        "payment_status",
        "subscriber_id",
        ("created_at", DateRangeFilterBuilder())
    )
    readonly_fields = ("transit_pnr", "pnr", "fare", "created_at", "updated_at")
    autocomplete_fields = ["ticket_type"]

    actions = [
        'mark_payment_completed',
        'mark_payment_incomplete',
        'mark_status_confirmed',
        'mark_status_pending',
        'mark_status_cancelled',
        'mark_status_expired'
    ]

    def view_ticket_updates(self, obj):
        url = reverse("admin:main_ticketupdate_changelist")
        return format_html('<a href="{}?ticket__id__exact={}">View Updates</a>', url,
                           obj.pnr)

    view_ticket_updates.short_description = "Ticket Updates"

    def link_to_created_for(self, obj):
        if hasattr(obj, 'created_for'):
            link = reverse(
                "admin:%s_%s_change" % (
                obj.created_for._meta.app_label, obj.created_for._meta.model_name),
                args=[obj.created_for.id]
            )
            return format_html('<a href="{}">{}</a>', link, obj.created_for)
        return "-"

    link_to_created_for.short_description = "Created For"


class TicketTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in TicketType._meta.fields if
                    field.name != 'id']
    search_fields = ("id", "name")


class FareBreakupAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in FareBreakup._meta.fields]


class AgencyAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Agency._meta.fields]
    search_fields = ("name", "description")


def mark_status_confirmed(modeladmin, request, queryset):
    updated_count = queryset.update(status=TicketStatus.CONFIRMED)
    messages.success(request, f'{updated_count} pass(s) marked as Confirmed.')


mark_status_confirmed.short_description = "Mark selected passes as Confirmed"


def mark_status_pending(modeladmin, request, queryset):
    updated_count = queryset.update(status=TicketStatus.PENDING)
    messages.success(request, f'{updated_count} pass(s) marked as Pending.')


mark_status_pending.short_description = "Mark selected passes as Pending"


def mark_status_cancelled(modeladmin, request, queryset):
    updated_count = queryset.update(status=TicketStatus.CANCELLED)
    messages.success(request, f'{updated_count} pass(s) marked as Cancelled.')


mark_status_cancelled.short_description = "Mark selected passes as Cancelled"


def mark_status_expired(modeladmin, request, queryset):
    updated_count = queryset.update(status=TicketStatus.EXPIRED)
    messages.success(request, f'{updated_count} pass(s) marked as Expired.')


mark_status_expired.short_description = "Mark selected passes as Expired"


class PassAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    readonly_fields = (
        "created_at", "updated_at", "pnr", "pass_type"
    )
    search_fields = ("pnr", "transit_pnr")
    list_display = (
        "pnr",
        "created_at",
        "pass_status",
        "amount",
        "transit_pnr",
        "pass_type"
    )
    list_filter = (
        "pass_status",
        "pass_type",
        ("created_at", DateRangeFilterBuilder()),
    )  # Add this line
    actions = [mark_status_confirmed,
               mark_status_pending,
               mark_status_cancelled,
               mark_status_expired]


class PassTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in PassType._meta.fields]


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketUpdate, TicketUpdateAdmin)
admin.site.register(TicketType, TicketTypeAdmin)
admin.site.register(FareBreakup, FareBreakupAdmin)
admin.site.register(Agency, AgencyAdmin)
admin.site.register(Pass, PassAdmin)
admin.site.register(PassType, PassTypeAdmin)
