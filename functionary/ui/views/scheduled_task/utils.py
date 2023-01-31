from django_celery_beat.models import CrontabSchedule

from core.utils.schedules import get_or_create_crontab_schedule


def get_crontab_schedule(schedule_form_data: dict) -> CrontabSchedule:
    """Retrieve or create a CrontabSchedule for the provided ScheduledTaskForm data"""
    minute = schedule_form_data.get("scheduled_minute")
    hour = schedule_form_data.get("scheduled_hour")
    day_of_month = schedule_form_data.get("scheduled_day_of_month")
    month_of_year = schedule_form_data.get("scheduled_month_of_year")
    day_of_week = schedule_form_data.get("scheduled_day_of_week")

    return get_or_create_crontab_schedule(
        minute, hour, day_of_month, month_of_year, day_of_week
    )
