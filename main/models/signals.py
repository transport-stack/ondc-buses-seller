from django.db.models.signals import post_save
from django.dispatch import receiver

from .tickets import Ticket, TicketUpdate


@receiver(post_save, sender=Ticket)
def create_ticket_update(sender, instance, created, **kwargs):
    if created:  # Check if the Ticket instance is being created (not updated)
        TicketUpdate.objects.create(ticket=instance, trigger_signal=True,
                                    details={"message": "Ticket created."})
