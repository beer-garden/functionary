from django_celery_beat.models import CrontabSchedule
from django_celery_beat.validators import (
    crontab_validator,
    day_of_month_validator,
    day_of_week_validator,
    hour_validator,
    minute_validator,
    month_of_year_validator,
)


def get_or_create_crontab_schedule(
    minute, hour, day_of_month, month_of_year, day_of_week
) -> CrontabSchedule:
    """Creates and returns a crontab schedule

    If the submitted crontab schedule already exists, returns
    the existing crontab schedule. Otherwise, creates and
    returns a new crontab schedule.

    Args:
        minute: int or valid crontab str representing minute
        hour: int or valid crontab str representing hour
        day_of_month: int or valid crontab str representing the day of the month
        month_of_year: int or valid crontab str representing the month of the year
        day_of_week: int or valid crontab str representing the day of the week

    Returns:
        CronTabSchedule: The new, or existing, crontab schedule

    Raises:
        ValueError: One of the provided values was not valid crontab syntax
    """
    crontab_str = f"{minute} {hour} {day_of_month} {month_of_year} {day_of_week}"

    crontab_validator(crontab_str)
    crontab_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=minute,
        hour=hour,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
    )

    return crontab_schedule


def is_valid_scheduled_minute(field: str) -> bool:
    try:
        minute_validator(field)
        return True
    except Exception:
        return False


def is_valid_scheduled_hour(field: str) -> bool:
    try:
        hour_validator(field)
        return True
    except Exception:
        return False


def is_valid_scheduled_day_of_week(field: str) -> bool:
    try:
        day_of_week_validator(field)
        return True
    except Exception:
        return False


def is_valid_scheduled_day_of_month(field: str) -> bool:
    try:
        day_of_month_validator(field)
        return True
    except Exception:
        return False


def is_valid_scheduled_month_of_year(field: str) -> bool:
    try:
        month_of_year_validator(field)
        return True
    except Exception:
        return False
