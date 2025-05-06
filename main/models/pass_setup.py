import logging
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from phonenumber_field.modelfields import PhoneNumberField
from main.constants import GENERAL_PASS_TYPE_ID
from main.models.pass_fare_setup import PassFareBreakup
from main.models.tickets import (
    ActiveMixin,
    DateTimeMixin,
    TicketStatus,
    PaymentStatus, ClaimStatus, Agency, PaymentType,
)


class PassType(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True)
    pass_type = models.CharField(max_length=64, null=True, blank=True)
    description = models.CharField(max_length=125, null=True, blank=True)
    validity_in_days = models.IntegerField(help_text="Pass validity in days", default=1)
    is_document_required = models.BooleanField(default=False)
    is_ac = models.BooleanField(null=True, blank=True, default=False)
    price = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    is_active = models.BooleanField(default=True, db_index=True)
    item_id = models.CharField(max_length=30, null=True, blank=True)
    provider_id = models.CharField(max_length=64, null=True, blank=True)
    allowed_documents = models.JSONField(null=True, blank=True)

    @classmethod
    def get_default_pk(cls):
        return GENERAL_PASS_TYPE_ID

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Pass Type"
        verbose_name_plural = "Pass Types"


class Pass(DateTimeMixin, ActiveMixin):

    pnr = models.CharField(
        max_length=64, primary_key=True, db_index=True
    )
    pass_status = models.IntegerField(
        choices=TicketStatus.choices,
        help_text="Status of the pass",
        default=TicketStatus.PENDING,
        db_index=True,
    )

    # Pass-id/PNR given by the transit provider
    transit_pnr = models.CharField(max_length=128, null=True, blank=True)
    user_name = models.CharField(max_length=64, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    govt_id = models.CharField(max_length=64, null=True, blank=True)
    govt_id_number = models.CharField(max_length=64, null=True, blank=True)
    photo = models.TextField(null=True, blank=True)
    fare = models.OneToOneField(
        PassFareBreakup, null=True, blank=True, on_delete=models.PROTECT
    )
    subscriber_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    agency = models.ForeignKey(Agency, on_delete=models.PROTECT, null=True, blank=True)
    pass_type = models.ForeignKey(
        PassType,
        on_delete=models.PROTECT,
        default=PassType.get_default_pk,
    )
    is_ac = models.BooleanField(null=True, blank=True, default=False)
    amount = models.FloatField(default=0.0, null=True, blank=True)
    valid_till = models.DateTimeField(null=True, blank=True)
    claim_status = models.IntegerField(choices=ClaimStatus.choices, default=ClaimStatus.UNCLAIMED)

    class Meta:
        unique_together = ("pnr",)
        # plural name for admin
        verbose_name_plural = "Passes"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.pnr}"

    def get_ticket_status(self):
        return TicketStatus(self.status)

    def is_status_pending(self):
        return self.get_ticket_status() == TicketStatus.PENDING

    def is_status_confirmed(self):
        return self.get_ticket_status() == TicketStatus.CONFIRMED

    def is_status_cancelled(self):
        return self.get_ticket_status() == TicketStatus.CANCELLED

    def is_status_expired(self):
        return self.get_ticket_status() == TicketStatus.EXPIRED

    @staticmethod
    def has_incomplete_passes(user):
        """
        Checks if the pass has at least one pending transaction.
        Returns True if it does, False otherwise.
        """
        return Pass.objects.filter(
            created_for=user, status__in=[TicketStatus.PENDING, TicketStatus.CONFIRMED]
        ).exists()

    @staticmethod
    def get_all_payment_status_not_completed_tickets(sd=None, ed=None):
        passes = Pass.objects.filter(payment_status=PaymentStatus.NOT_COMPLETED)

        query = Q()
        if sd:
            query &= Q(created_at__gte=sd)
        if ed:
            query &= Q(created_at__lte=ed)

        passes = passes.filter(query)

        return passes

    @staticmethod
    def mark_passes_as_cancelled(start_datetime=None, end_datetime=None):
        """
        Update status of passes to CANCELLED based on the created_at timestamp range.

        :param start_datetime: Cancel passes created after this datetime (datetime object).
        :param end_datetime: Cancel passes created before this datetime (datetime object).
        """
        if not start_datetime and not end_datetime:
            raise ValueError("At least one of start_datetime or end_datetime must be provided")

        filters = {'status': TicketStatus.PENDING}

        if start_datetime:
            filters['created_at__gt'] = start_datetime
        if end_datetime:
            filters['created_at__lt'] = end_datetime

        # affected_rows = Ticket.objects.filter(**filters).update(status=TicketStatus.CANCELLED)
        # Fetch the tickets that match the criteria
        passes_to_cancel = Pass.objects.filter(**filters)

        # Print PNR for each ticket
        for bus_pass in passes_to_cancel:
            # log ticket's pnr, created_at, status, payment status
            logging.info(f"Cancelling Ticket PNR: {bus_pass.pnr}, "
                         f"Created At: {bus_pass.created_at}, "
                         f"Status: {bus_pass.status}, "
                         f"Transit PNR: {bus_pass.transit_pnr}, "
                         f"Service Details: {bus_pass.service_details}, "
                         f"Payment Status: {bus_pass.payment_status}")

            bus_pass.cancel_by_system(cancellation_reason="Unconfirmed pass cancelled by system.")
            # logging.info()
            logging.info(f"Cancelling ticket with PNR: {bus_pass.pnr}")

        # affected_rows = tickets_to_cancel.update(status=TicketStatus.CANCELLED)
        logging.info(f"Cancelled {passes_to_cancel.count()} ticket(s) with criteria: {filters}")

    @staticmethod
    def mark_pass_by_pnr_as_cancelled(pnr=None):
        logging.info(f"mark_pass_by_pnr_as_cancelled called with pnr: {pnr}")
        if not pnr:
            raise ValueError("PNR must be provided")

        pass_to_cancel = Pass.objects.get(pnr=pnr)

        logging.info(f"Cancelling Pass PNR: {pass_to_cancel.pnr}, "
                     f"Created At: {pass_to_cancel.created_at}, "
                     f"Status: {pass_to_cancel.status}, "
                     f"Transit PNR: {pass_to_cancel.transit_pnr}, "
                     f"Service Details: {pass_to_cancel.service_details}, "
                     f"Payment Status: {pass_to_cancel.payment_status}")

        pass_to_cancel.cancel_by_system(cancellation_reason="Unconfirmed pass cancelled by system.")
        logging.info(f"Cancelling pass with PNR: {pass_to_cancel.pnr}")

    @staticmethod
    def mark_passes_as_expired(start_datetime=None, end_datetime=None):
        """
        Update status of tickets to EXPIRED based on the created_at timestamp range.

        :param start_datetime: Expire tickets created after this datetime (datetime object).
        :param end_datetime: Expire tickets created before this datetime (datetime object).
        """
        if not start_datetime and not end_datetime:
            raise ValueError("At least one of start_datetime or end_datetime must be provided")

        filters = {'status': TicketStatus.CONFIRMED}

        if start_datetime:
            filters['created_at__gt'] = start_datetime
        if end_datetime:
            filters['created_at__lt'] = end_datetime

        affected_rows = Pass.objects.filter(**filters).update(status=TicketStatus.EXPIRED)
        logging.info(f"Expired {affected_rows} ticket(s) with criteria: {filters}")

    @staticmethod
    def mark_passes_as_expired_after_validity(start_datetime=None):
        """
        Update status of tickets to EXPIRED based on their validity period.

        :param start_datetime: Expire tickets valid until this datetime (datetime object).
        """
        if not start_datetime:
            raise ValueError("start_datetime must be provided")

        # Filter tickets that are confirmed and have a valid_till date earlier than start_datetime
        filters = {
            'pass_status': TicketStatus.CONFIRMED,
            'valid_till__lt': start_datetime
        }

        bus_passes = Pass.objects.filter(**filters)
        for bus_pass in bus_passes:
            bus_pass.update_status(TicketStatus.EXPIRED)
            logging.info(f"Expired bus_pass with PNR: {bus_pass.pnr} with criteria===: {filters}")

    def update_status(self, status, service_details=None, other_updates=None,
                      notification_title=None, notification_message=None,
                      notification=None):
        logging.critical(f"update_status for pnr: {self.pnr}, status={status}, service_details={service_details}, "
                         f"other_updates={other_updates}, notification_title={notification_title}, "
                         f"notification_message={notification_message}, notification={notification}.")
        try:
            if other_updates is not None:
                logging.critical(f"Applying other_updates=={self.pnr}: {other_updates}")
                for member, value in other_updates.items():
                    setattr(self, member, value)
                logging.critical(f"Other updates applied successfully.=={self.pnr}")

            if service_details:
                logging.critical(f"Updating service_details=={self.pnr}: {service_details}")
                self.service_details = service_details

            self.pass_status = status
            logging.critical(f"Status set to=={self.pnr}: {status}. Saving the object.")
            self.save()
            logging.critical(f"Object saved successfully.{self.pnr}")

            self.refresh_from_db()
            # Check if status was updated successfully
            if self.pass_status != status:
                logging.critical(f"Failed to update status for pnr: {self.pnr}. Refreshed status: {self.pass_status}")
        except Exception as e:
            logging.critical(f"An unexpected error occurred{self.pnr}: {e}")
            raise e
        finally:
            logging.critical(f"update_status method execution completed.=={self.pnr}")
