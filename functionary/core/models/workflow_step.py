import json
import re
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.template import Context, Template

from core.models import Task, WorkflowRunStep
from core.utils.tasking import start_task

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
        tasked_type: the ContentType (model) of the object being tasked
        tasked_id: the UUID of the object being tasked
        tasked_object: foreign key to the object being tasked, built from tasked_type
                        and tasked_id.
        parameter_template: Stringified JSON representing the parameters that will be
                            passed to the tasked object. May contain django template
                            syntax in place of values (e.g. {{step_name.result}})
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(to="Workflow", on_delete=models.CASCADE)
    name = models.CharField(max_length=64, validators=[VALID_STEP_NAME])
    next = models.ForeignKey(
        to="WorkflowStep", blank=True, null=True, on_delete=models.PROTECT
    )
    tasked_type = models.ForeignKey(to=ContentType, on_delete=models.PROTECT)
    tasked_id = models.UUIDField()
    tasked_object = GenericForeignKey("tasked_type", "tasked_id")
    parameter_template = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "name"],
                name="ws_workflow_name_unique_together",
            ),
        ]
        indexes = [
            models.Index(
                fields=["workflow", "tasked_type", "tasked_id"],
                name="ws_contenttype",
            ),
        ]

    def __str__(self):
        return self.name

    def _inject_json_filter(self, parameter_template):
        """Injects the custom json filter into all template variables so that values
        get rendered as proper json"""
        # Add json filter to variables
        template = re.sub(r"{{([\w\.]+)}}", r"{{\1|json_safe}}", parameter_template)

        # Make json filter available for use
        template = "{% load workflow_filters %}" + template

        return template

    def _get_parameters(self, context: Context):
        """Uses a given Context to resolve the parameter_template into a parameters
        dict
        """
        if self.parameter_template is None:
            return {}

        template = self._inject_json_filter(self.parameter_template)
        resolved_parameters = Template(template).render(context)

        try:
            return json.loads(resolved_parameters)
        except json.JSONDecodeError:
            raise ValueError("Unable to determine Workflow Step parameters")

    def _get_run_context(self, workflow_run: "Task") -> Context:
        """Generates a context for resolving tasking parameters.

        Args:
            workflow_run: a Task associated with a specific run of a workflow

        Returns:
            A Context containing data from all WorkflowRunSteps that have
            occurred for this workflow run
        """
        context = {}
        context["parameters"] = workflow_run.parameters or {}

        for step in workflow_run.steps.filter(step_task__isnull=False):
            name = step.step_name
            task = step.step_task

            context[name] = {}
            context[name]["result"] = task.result

        return Context(context, autoescape=False)

    def _clean_tasked_object(self):
        """Validate the tasked_object is active for new scheduled tasks"""
        try:
            if not self.tasked_object and self.tasked_id:
                self.tasked_object = self.tasked_type.get_object_for_this_type(
                    id=self.tasked_id
                )
            if self.tasked_object.active is False:
                raise ValidationError("This Function is not active")
        except WorkflowStep.tasked_type.RelatedObjectDoesNotExist:
            # This occurs when the tasked_type isn't set
            raise ValidationError("Unable to get Task")

    def clean(self):
        self._clean_tasked_object()
        if self.workflow.environment != self.tasked_object.environment:
            raise ValidationError("Workflow and Task environments do not match")

    @property
    def previous(self):
        """Returns the step preceding this one in the workflow. For the first step in
        the workflow, returns None."""
        return self.workflowstep_set.filter(next=self).first()

    def execute(self, workflow_task: "Task") -> "Task":
        """Execute this workflow step as part of the supplied workflow task"""

        with transaction.atomic():
            run_context = self._get_run_context(workflow_task)

            task = Task.objects.create(
                creator=workflow_task.creator,
                environment=self.workflow.environment,
                tasked_object=self.tasked_object,
                parameters=self._get_parameters(run_context),
            )

            WorkflowRunStep.objects.filter(
                workflow_step=self, workflow_task=workflow_task
            ).update(step_task=task)

        start_task(task)

        return task

    @property
    def return_type(self) -> str | None:
        """Pass the tasked_object's return_type"""
        return getattr(self.tasked_object, "return_type", None)
