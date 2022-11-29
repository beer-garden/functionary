import json
import uuid
from typing import TYPE_CHECKING

from django.core.validators import RegexValidator
from django.db import models, transaction
from django.template import Context, Template

from core.models import Task, Workflow, WorkflowRunStep

if TYPE_CHECKING:
    from core.models import WorkflowRun


VALID_STEP_NAME = RegexValidator(
    regex=r"^\w+$",
    message="Invalid step name. Only numbers, letters, and underscore are allowed.",
)


class WorkflowStep(models.Model):
    """A WorkflowStep is the definition of a Task that will be executed as part of a
    Workflow

    Attributes:
        id: unique identifier (UUID)
        workflow: the Workflow to which this step belongs
        next: The step that follows this one in the workflow. A value of None indicates
              that this is the final step.
        name: An internal name for the step which can be used as a reference for
              input into other steps of the Workflow.
        function: the function that the task will be an run of
        parameter_template: Stringified JSON representing the parameters that will be
                            passed to the function. May contain django template syntax
                            in place of values (e.g. {{step_name.result}})
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        to=Workflow, on_delete=models.CASCADE, related_name="steps"
    )
    name = models.CharField(max_length=64, validators=[VALID_STEP_NAME])
    next = models.ForeignKey(
        to="WorkflowStep", blank=True, null=True, on_delete=models.PROTECT
    )
    function = models.ForeignKey(to="Function", on_delete=models.CASCADE)
    parameter_template = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "name"],
                name="ws_workflow_name_unique_together",
            ),
            models.UniqueConstraint(
                fields=["workflow", "next"],
                name="ws_workflow_next_unique_together",
            ),
        ]

    def _get_parameters(self, context: Context):
        """Uses a given Context to resolve the parameter_template into a parameters
        dict
        """

        resolved_parameters = (
            Template(self.parameter_template or "{}")
            .render(context)
            .replace("&quot;", '"')
        )

        return json.loads(resolved_parameters)

    def execute(self, workflow_run: "WorkflowRun") -> Task:
        """Executes a Task based on this step's function and parameters

        Args:
            workflow_run: The WorkflowRun that the task belongs to

        Returns:
            The executed Task
        """

        with transaction.atomic():
            run_context = workflow_run.get_context()

            task = Task(
                creator=workflow_run.creator,
                environment=self.workflow.environment,
                function=self.function,
                parameters=self._get_parameters(run_context),
            ).save()

            WorkflowRunStep.objects.create(
                task=task, workflow_step=self, workflow_run=workflow_run
            )

        return task
