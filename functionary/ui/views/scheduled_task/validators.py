from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from core.utils.schedules import (
    is_valid_scheduled_day_of_month,
    is_valid_scheduled_day_of_week,
    is_valid_scheduled_hour,
    is_valid_scheduled_minute,
    is_valid_scheduled_month_of_year,
)


@require_POST
@login_required
def crontab_minute_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_minute(request.POST.get("scheduled_minute")):
        return render(request, "partials/crontab_invalid.html", {"field": "Minute"})
    return HttpResponse("")


@require_POST
@login_required
def crontab_hour_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_hour(request.POST.get("scheduled_hour")):
        return render(request, "partials/crontab_invalid.html", {"field": "Hour"})
    return HttpResponse("")


@require_POST
@login_required
def crontab_day_of_week_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_day_of_week(request.POST.get("scheduled_day_of_week")):
        return render(
            request, "partials/crontab_invalid.html", {"field": "Day of week"}
        )
    return HttpResponse("")


@require_POST
@login_required
def crontab_day_of_month_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_day_of_month(request.POST.get("scheduled_day_of_month")):
        return render(
            request, "partials/crontab_invalid.html", {"field": "Day of month"}
        )
    return HttpResponse("")


@require_POST
@login_required
def crontab_month_of_year_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_month_of_year(
        request.POST.get("scheduled_month_of_year")
    ):
        return render(
            request, "partials/crontab_invalid.html", {"field": "Month of year"}
        )
    return HttpResponse("")
