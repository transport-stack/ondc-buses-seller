import logging

from modules.constants import SchedulesEnum

logger = logging.getLogger(__name__)

from django_celery_beat.models import PeriodicTask, CrontabSchedule
from pytz import timezone


def _add_crontab(schedule):
    # Create a new crontab schedule
    if not "timezone" in schedule:
        schedule["timezone"] = "Asia/Kolkata"

    crontab, created = CrontabSchedule.objects.get_or_create(
        minute=schedule["minute"],
        hour=schedule["hour"],
        day_of_week=schedule["day_of_week"],
        day_of_month=schedule["day_of_month"],
        month_of_year=schedule["month_of_year"],
        timezone=timezone(schedule["timezone"]),
    )


def _add_celery_task(name, task, schedule, args=None, kwargs=None):
    try:
        # Check if the task already exists in the database

        task_exists = PeriodicTask.objects.filter(name=name).exists()
        if task_exists:
            print(f"Task '{name}' already exists. Ignoring...")
            return

        # Create a new crontab schedule
        crontab = CrontabSchedule.objects.get(
            minute=schedule["minute"],
            hour=schedule["hour"],
            day_of_week=schedule["day_of_week"],
            day_of_month=schedule["day_of_month"],
            month_of_year=schedule["month_of_year"],
        )

        # Create a new periodic task
        periodic_task = PeriodicTask.objects.create(
            name=name,
            task=task,
            args=args or [],
            kwargs=kwargs or {},
            crontab=crontab,
        )

        print(f"Task '{name}' added successfully.")
    except Exception as e:
        print(f"Error adding task '{name}': {str(e)}")


def add_crontabs():
    logging.debug("Adding crontabs...")

    for schedule_name, schedule in vars(SchedulesEnum).items():
        # We only want the attributes that end with "_SCHEDULE_DICT"
        if schedule_name.endswith("_SCHEDULE_DICT"):
            _add_crontab(schedule=schedule)


def add_celery_tasks():
    add_crontabs()

    PeriodicTask.objects.all().delete()

    _add_celery_task(
        name="main.tasks.tasks.expire_previous_day_confirmed_tickets",
        task="main.tasks.tasks.expire_previous_day_confirmed_tickets",
        schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,  # Run every 60 seconds (1 minute)
    )

    _add_celery_task(
        name="main.tasks.tasks.expire_passes_after_validity",
        task="main.tasks.tasks.expire_passes_after_validity",
        schedule=SchedulesEnum.EVERY_MORNING_AT_02_00_SCHEDULE_DICT,  # Run every 60 seconds (1 minute)
    )
