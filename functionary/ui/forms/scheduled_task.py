from django.forms import CharField, ModelForm, ValidationError
from django.urls import reverse
from django_celery_beat.validators import (
    day_of_month_validator,
    day_of_week_validator,
    hour_validator,
    minute_validator,
    month_of_year_validator,
)

from core.models import Environment, Function, ScheduledTask


class ScheduledTaskForm(ModelForm):
    scheduled_minute = CharField(
        max_length=60 * 4, label="Minute", initial="*", validators=[minute_validator]
    )
    scheduled_hour = CharField(
        max_length=24 * 4, label="Hour", initial="*", validators=[hour_validator]
    )
    scheduled_day_of_week = CharField(
        max_length=64,
        label="Day of Week",
        initial="*",
        validators=[day_of_week_validator],
    )
    scheduled_day_of_month = CharField(
        max_length=31 * 4,
        label="Day of Month",
        initial="*",
        validators=[day_of_month_validator],
    )
    scheduled_month_of_year = CharField(
        max_length=64,
        label="Month of Year",
        initial="*",
        validators=[month_of_year_validator],
    )

    class Meta:
        model = ScheduledTask
        fields = [
            "name",
            "description",
            "status",
            "function",
            "parameters",
            "environment",
        ]

    def __init__(self, *args, **kwargs):
        env: Environment = kwargs.pop("env")
        super().__init__(*args, **kwargs)
        self.fields["function"].queryset = Function.objects.filter(
            package__environment=env
        )
        self.fields["status"].choices = self._get_status_choices()
        self._setup_field_classes()

    def clean(self):
        cleaned_data = super().clean()
        available_functions = Function.objects.filter(
            package__environment=cleaned_data["environment"]
        )
        if cleaned_data["function"] not in available_functions:
            self.add_error(
                "function",
                ValidationError("Unknown function was provided.", code="invalid"),
            )

        return cleaned_data

    def _get_status_choices(self) -> list:
        choices = []
        for choice in ScheduledTask.STATUS_CHOICES:
            if choice[0] == ScheduledTask.PENDING or choice[0] == ScheduledTask.ERROR:
                continue
            choices.append(choice)
        return choices

    def _setup_field_classes(self):
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "input is-medium"})

        self.fields["name"].widget.attrs.update(
            {"class": "input is-medium is-fullwidth"}
        )

        self.fields["status"].widget.attrs.update(
            {"class": "input is-medium is-fullwidth"}
        )

        self.fields["function"].widget.attrs.update(
            {
                "hx-get": reverse("ui:function-parameters"),
                "hx-target": "#function-parameters",
            }
        )

        self._setup_crontab_fields()

    def _setup_crontab_fields(self):
        """Ugly method to attach htmx properties to the crontab components"""

        crontab_fields = [
            "scheduled_minute",
            "scheduled_hour",
            "scheduled_day_of_week",
            "scheduled_day_of_month",
            "scheduled_month_of_year",
        ]

        for field in crontab_fields:
            field_id = f"id_{field}"
            field_url = field.replace("_", "-")
            self.fields[field].widget.attrs.update(
                {
                    "hx-post": reverse(f"ui:{field_url}-param"),
                    "hx-trigger": "keyup delay:500ms",
                    "hx-target": f"#{field_id}_errors",
                }
            )
