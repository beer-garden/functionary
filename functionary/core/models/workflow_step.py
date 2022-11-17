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
    regex="^[a-zA-Z0-9_]+$",
    message="Invalid step name. Only numbers, letters, and underscore are allowed.",
)


class WorkflowStep(models.Model):
    """A WorkflowStep is the definition of a Task that will be executed as part of a
    Workflow

    Attributes:
        id: unique identifier (UUID)
        workflow: the Workflow to which this element belongs
        sequence: The element's order of run within the Workflow
        name: An internal name for the element which can be used as a reference for
              input into other elements of the Workflow.
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
    sequence = models.IntegerField()
    function = models.ForeignKey(to="Function", on_delete=models.CASCADE)
    parameter_template = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "sequence"],
                name="ws_workflow_sequence_unique_together",
            ),
            models.UniqueConstraint(
                fields=["workflow", "name"],
                name="ws_workflow_name_unique_together",
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
        """Executes a Task base on this element's function and parameters

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
