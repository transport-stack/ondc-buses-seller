import logging
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.apps import apps
from celery import shared_task


@shared_task(name="main.tasks.tasks.expire_previous_day_confirmed_tickets")
def expire_previous_day_confirmed_tickets():
    try:
        logging.info("expire_previous_day_confirmed_tickets")
        start_of_yesterday = datetime.combine(datetime.today() - timedelta(days=1), time.min)
        end_of_yesterday = datetime.combine(datetime.today(), time.min)
        logging.info(f"start_of_yesterday: {start_of_yesterday}")
        logging.info(f"end_of_yesterday: {end_of_yesterday}")
        Ticket = apps.get_model("main", "Ticket")
        Ticket.mark_tickets_as_expired(start_datetime=start_of_yesterday, end_datetime=end_of_yesterday)
    except Exception as e:
        logging.error(f"Error in expire_previous_day_confirmed_tickets: {e}")


@shared_task(name="main.tasks.tasks.expire_passes_after_validity")
def expire_passes_after_validity():
    logging.info("expire_passes_after_validity")
    current_time = timezone.now()
    BusPass = apps.get_model("main", "Pass")
    BusPass.mark_passes_as_expired_after_validity(start_datetime=current_time)
