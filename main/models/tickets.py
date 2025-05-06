import datetime
import logging

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from main.constants import GENERAL_TICKET_TYPE_ID
from .models import ActiveMixin, DateTimeMixin
from .fare_setup import FareBreakup


# Enumeration for Ticket Status
class TicketStatus(models.IntegerChoices):
    CONFIRMED = 1, _("Confirmed")
    PENDING = 3, _("Pending")
    CANCELLED = 5, _("Cancelled")
    EXPIRED = 7, _("Expired")


# Model for Ticket Types
class TicketType(models.Model):
    objects = None
    DoesNotExist = None
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40,
                            unique=True)
    discount_percentage = models.FloatField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_description_required = models.BooleanField(default=False)
    is_active = models.BooleanField(
        default=True)
    description = models.CharField(max_length=256, null=True, blank=True)

    @classmethod
    def get_default_pk(cls):
        return GENERAL_TICKET_TYPE_ID

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ticket Type"
        verbose_name_plural = "Ticket Types"


# Enumeration for Payment Type
class PaymentType(models.IntegerChoices):
    PREPAID = 1, _("Prepaid")
    POSTPAID = 3, _("Postpaid")
    FREE = 5, _("Free")


# Enumeration for Payment Status
class PaymentStatus(models.IntegerChoices):
    NOT_COMPLETED = 1, _("Not Completed")
    COMPLETED = 3, _("Completed")


class ClaimStatus(models.TextChoices):
    CLAIMED = 1, _("Claimed")
    UNCLAIMED = 3, _("Unclaimed")


class Agency(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'agency'
        verbose_name_plural = "Agencies"


# Ticket Model incorporating Enumerations
class Ticket(DateTimeMixin, ActiveMixin):
    list_display = (
            'pnr', 'ticket_status', 'transit_pnr', 'ticket_type', 'passenger_count',
            'amount', 'payment_type', 'payment_status', 'valid_till', 'vehicle_number',
            'fare', 'start_stop_code', 'end_stop_code', 'route', 'subscriber_id')
    objects = None
    pnr = models.CharField(max_length=64,
                           primary_key=True)  # Primary keys are indexed by default
    ticket_status = models.IntegerField(choices=TicketStatus.choices,
                                        default=TicketStatus.PENDING)
    transit_pnr = models.CharField(max_length=128, null=True, blank=True)
    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.PROTECT,
        default=TicketType.get_default_pk,
    )
    passenger_count = models.IntegerField(default=1)
    amount = models.FloatField(default=0.0)
    payment_type = models.IntegerField(choices=PaymentType.choices,
                                       default=PaymentType.PREPAID)
    payment_status = models.IntegerField(choices=PaymentStatus.choices,
                                         default=PaymentStatus.NOT_COMPLETED)
    fare = models.OneToOneField(
        FareBreakup, null=True, blank=True, on_delete=models.PROTECT
    )
    valid_till = models.DateTimeField(null=True, blank=True)
    vehicle_number = models.CharField(max_length=32, null=True, blank=True)
    agency = models.ForeignKey(Agency, on_delete=models.PROTECT, null=True, blank=True)
    start_stop_name = models.CharField(max_length=80, null=True, blank=True)
    start_stop_code = models.CharField(max_length=80, null=True, blank=True)
    end_stop_name = models.CharField(max_length=80, null=True, blank=True)
    end_stop_code = models.CharField(max_length=80, null=True, blank=True)
    route = models.CharField(max_length=50, null=True, blank=True)
    subscriber_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    description = models.CharField(max_length=32, null=True, blank=True)
    is_ac = models.BooleanField(null=True, blank=True, default=False)
    claim_status = models.IntegerField(choices=ClaimStatus.choices, default=ClaimStatus.CLAIMED)

    def __str__(self):
        return self.pnr

    @staticmethod
    def mark_tickets_as_expired(start_datetime=None, end_datetime=None):
        """
        Update status of tickets to EXPIRED based on the created_at timestamp range.

        :param start_datetime: Expire tickets created after this datetime (datetime object).
        :param end_datetime: Expire tickets created before this datetime (datetime object).
        """
        if not start_datetime and not end_datetime:
            raise ValueError("At least one of start_datetime or end_datetime must be provided")

        filters = {'ticket_status': TicketStatus.CONFIRMED}

        if start_datetime:
            filters['created_at__gt'] = start_datetime
        if end_datetime:
            filters['created_at__lt'] = end_datetime

        affected_rows = Ticket.objects.filter(**filters).update(ticket_status=TicketStatus.EXPIRED)
        logging.info(f"Expired {affected_rows} ticket(s) with criteria: {filters}")


class TicketUpdate(DateTimeMixin, ActiveMixin):
    trigger_signal = models.BooleanField(default=True)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="ticket_updates",
        null=False,
        blank=False,
    )
    details = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Ticket Update"
        verbose_name_plural = "Ticket Updates"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.ticket.pnr} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @staticmethod
    def custom_create(details, ticket_transit_pnr, trigger_signal=True):
        """
        Custom creation method that logs the process of creating a TicketUpdate.
        """
        logging.info(
            f"Creating TicketUpdate: details: {details}; ticket_transit_pnr: {ticket_transit_pnr}"
        )
        try:
            ticket = Ticket.objects.get(transit_pnr=ticket_transit_pnr)
        except Ticket.DoesNotExist:
            logging.error("Ticket not found with the provided transit PNR.")
            return None
        TicketUpdate(
            trigger_signal=trigger_signal,
            ticket=ticket,
            details=details,
        ).save()

    @staticmethod
    def build_instance(details, ticket_transit_pnr, trigger_signal=True):
        """
        Build a TicketUpdate instance without saving it to the database.
        """
        try:
            ticket = Ticket.objects.get(transit_pnr=ticket_transit_pnr)
        except Ticket.DoesNotExist:
            logging.error("Ticket not found with the provided transit PNR.")
            return None

        return TicketUpdate(
            trigger_signal=trigger_signal,
            ticket=ticket,
            details=details,
        )

    @classmethod
    def delete_older_ticket_updates(cls):
        """
        Deletes all ticket updates older than 7 days.
        """
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        old_updates = cls.objects.filter(created_at__lte=seven_days_ago)
        count = old_updates.count()
        old_updates.delete()
        logging.info(f"Deleted {count} old ticket updates.")
