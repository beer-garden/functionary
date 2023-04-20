from django.contrib.contenttypes.models import ContentType
from django.forms import CharField, Form, ModelChoiceField
from django.urls import reverse
from django_celery_beat.validators import (
    day_of_month_validator,
    day_of_week_validator,
    hour_validator,
    minute_validator,
    month_of_year_validator,
)

from core.models import Environment, Function, ScheduledTask, Workflow

from .custom_forms import BootstrapModelForm


class ScheduledTaskForm(BootstrapModelForm):
    scheduled_minute = CharField(
        max_length=60 * 4, label="Minute", initial="*", validators=[minute_validator]
    )
    scheduled_hour = CharField(
        max_length=24 * 4, label="Hour", initial="*", validators=[hour_validator]
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
    scheduled_day_of_week = CharField(
        max_length=64,
        label="Day of Week",
        initial="*",
        validators=[day_of_week_validator],
    )
    tasked_object = ModelChoiceField(
        # This queryset will change on form initialization based on the tasked_type
        queryset=Function.active_objects.all(),
        required=True,
    )

    class Meta:
        model = ScheduledTask
        icons = {
            "description": "fa-newspaper",
            "name": "fa-font",
            "status": "fa-heart-pulse",
            "tasked_object": "fa-cube",
        }

        # NOTE: The order of the fields matters. The clean_<field> methods run based on
        # the order they are defined in the 'fields =' attribute
        fields = [
            "name",
            "environment",
            "description",
            "status",
            "tasked_object",
            "tasked_type",
            "tasked_id",
            "parameters",
        ]

    def __init__(
        self,
        tasked_object: Function | Workflow,
        environment: Environment,
        *args,
        **kwargs,
    ):
        self._update_tasked_object_queryset(tasked_object, environment)
        super().__init__(*args, **kwargs)
        self._setup_field_choices(kwargs.get("instance") is not None, tasked_object)
        self._setup_crontab_fields()

    def _update_tasked_object_queryset(
        self, tasked_object: Function | Workflow, environment: Environment
    ):
        object_type = type(tasked_object)
        if object_type not in [Function, Workflow]:
            raise ValueError("Incorrect tasked object type")

        self.declared_fields["tasked_object"].label = (
            "Function" if isinstance(tasked_object, Function) else "Workflow"
        )
        self.declared_fields[
            "tasked_object"
        ].queryset = object_type.active_objects.filter(environment=environment)

    def _get_create_status_choices(self) -> list:
        """Don't want user to set status to Error"""
        choices = [
            choice
            for choice in ScheduledTask.STATUS_CHOICES
            if choice[0] != ScheduledTask.ERROR
        ]
        return choices

    def _get_update_status_choices(self) -> list:
        """Don't want user to set status to Error or Pending"""
        choices = [
            choice
            for choice in ScheduledTask.STATUS_CHOICES
            if choice[0] not in [ScheduledTask.ERROR, ScheduledTask.PENDING]
        ]
        return choices

    def _setup_field_choices(
        self, is_update: bool, tasked_object: Function | Workflow
    ) -> None:
        if is_update:
            self.fields["status"].choices = self._get_update_status_choices()
        else:
            self.fields["status"].choices = self._get_create_status_choices()
        if not tasked_object:
            raise ValueError("Unable to determine tasked object")

        self.fields["tasked_object"].choices = [(tasked_object.id, tasked_object)]

    def _setup_crontab_fields(self):
        """Ugly method to attach htmx properties to the crontab components"""

        crontab_fields = [
            "scheduled_minute",
            "scheduled_hour",
            "scheduled_day_of_month",
            "scheduled_month_of_year",
            "scheduled_day_of_week",
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


class ScheduledTaskWizardForm(Form):
    name = CharField(label="Name", max_length=200, required=True)
    tasked_object = ModelChoiceField(
        # The queryset will be adjusted based on the passed in tasked_type
        queryset=Function.active_objects.all(),
        required=True,
    )

    def __init__(
        self,
        environment: Environment = None,
        tasked_type: str | ContentType = None,
        *args,
        **kwargs,
    ):
        self._update_tasked_object_queryset(environment, tasked_type)
        super().__init__(*args, **kwargs)

    def _update_tasked_object_queryset(
        self, environment: Environment, tasked_type: str | ContentType
    ):
        if hasattr(tasked_type, "name"):
            tasked_type = tasked_type.name

        object_manager = (
            Function.active_objects
            if tasked_type != "workflow"
            else Workflow.active_objects
        )
        field = self.declared_fields["tasked_object"]
        field.queryset = object_manager.filter(environment=environment)
        field.empty_label = f"Select a {tasked_type}"
        field.label = tasked_type.capitalize()
