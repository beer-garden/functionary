from typing import TYPE_CHECKING, Union

from django.core.exceptions import ValidationError
from django.forms import HiddenInput, ModelChoiceField, ModelForm

from core.models import Function, WorkflowStep
from core.models.workflow_step import VALID_STEP_NAME

if TYPE_CHECKING:
    from uuid import UUID

    from core.models import Environment


class WorkflowStepCreateForm(ModelForm):
    """Form for WorkflowStep creation"""

    template_name = "forms/workflow/step_edit.html"

    tasked_object = ModelChoiceField(
        label="Function",
        queryset=Function.active_objects.all(),
        required=True,
    )

    class Meta:
        model = WorkflowStep
        fields = [
            "workflow",
            "name",
            "tasked_object",
            "tasked_type",
            "tasked_id",
            "next",
        ]
        widgets = {"workflow": HiddenInput(), "next": HiddenInput()}

    def __init__(
        self,
        environment: Union["Environment", "UUID", str, None] = None,
        *args,
        **kwargs
    ):
        """WorkflowStepForm init

        Args:
            environment: Environment instance or id. When provided, the queryset of the
                tasked_object field will be filtered to only the functions for the
                environment.
        """
        self.declared_fields["tasked_object"].queryset = Function.active_objects.filter(
            environment=environment
        )
        super().__init__(*args, **kwargs)

        self.fields["name"].widget.attrs.update(
            {
                "pattern": VALID_STEP_NAME.regex.pattern,
                "title": VALID_STEP_NAME.message,
            }
        )


class WorkflowStepUpdateForm(WorkflowStepCreateForm):
    """Form for WorkflowStep updates"""

    class Meta:
        model = WorkflowStep
        fields = ["name", "tasked_object", "tasked_type", "tasked_id"]

    def full_clean(self):
        # Run the base full_clean() first. The constraints run against a model
        # instance and self.instance isn't update until _post_clean() is run.
        super().full_clean()
        try:
            self.instance.validate_constraints()
        except ValidationError as e:
            self._update_errors(e)
