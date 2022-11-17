import json
import uuid
from typing import Optional

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.template import Context

from core.models import Task


class WorkflowRun(models.Model):
    """A WorkflowRun represents an run of a Workflow. When a WorkflowRun
    is created a task will be created for each of its WorkflowSteps, in order of their
    sequence number.

    Attributes:
        id: unique identifier (UUID)
        workflow: the Workflow being executed
        environment: the environment that this task belongs to. All queryset filtering
                     should include an environment.
        status: tasking status
        parameters: parameters that can be referenced by the steps in the WorkflowRun
        creator: the user that initiated the task
        created_at: task creation timestamp
        updated_at: task updated timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        to="Workflow", on_delete=models.CASCADE, related_name="runs"
    )
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=16, choices=Task.STATUS_CHOICES, default=Task.PENDING
    )
    parameters = models.JSONField(blank=True, null=True, encoder=DjangoJSONEncoder)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["environment", "status"], name="wr_environment_status"
            ),
            models.Index(
                fields=["environment", "creator"], name="wr_environment_creator"
            ),
            models.Index(
                fields=["environment", "created_at"], name="wr_environment_created_at"
            ),
            models.Index(
                fields=["environment", "updated_at"], name="wr_environment_updated_at"
            ),
        ]

    @classmethod
    def find_by_task(cls, task: Task) -> Optional["WorkflowRun"]:
        """Retrieve the WorkflowRun that spawned a Task, if one exists

        Args:
            task: the Task for which to find the WorkflowRun

        Returns:
            WorkflowRun if the Task was spawned by one. Otherwise None."""
        try:
            return task.workflow_run_step.workflow_run
        except ObjectDoesNotExist:
            return None

    def get_context(self) -> Context:
        """Generates a context for resolving tasking parameters.

        Returns:
            A Context containing data from all WorkflowRunSteps that have
            occurred for this WorkflowRun
        """

        # Malleable object class for storing context properties
        class Object:
            pass

        context = {"parameters": Object()}

        parameters = self.parameters or {}
        for key, value in parameters.items():
            setattr(context["parameters"], key, json.dumps(value))

        for step in self.steps.all():
            name = step.workflow_step.name
            task = step.task

            context[name] = Object()
            context[name].result = task.raw_result

        return Context(context)

    def _update_status(self, status: str) -> None:
        if self.status != status:
            self.status = status
            self.save()

    def complete(self) -> None:
        """Set the WorkflowRun status to COMPLETE"""
        self._update_status(Task.COMPLETE)

    def error(self) -> None:
        """Set the WorkflowRun status to ERROR"""
        self._update_status(Task.ERROR)

    def in_progress(self) -> None:
        """Set the WorkflowRun status to IN_PROGRESS"""
        self._update_status(Task.IN_PROGRESS)

    def execute_next_step(self) -> Optional[Task]:
        """Spawns a task for the next WorkflowStep in the Workflow

        Returns:
            The Task spawned for the next step in the Workflow. Returns None if there
            are no more remaining steps to be run.
        """
        steps = self.steps.all()

        if not steps.exists():
            max_sequence = 0
        else:
            max_sequence = steps.aggregate(models.Max("workflow_step__sequence"))[
                "workflow_step__sequence__max"
            ]

        # This intentionally avoids specifying what the exact sequence number is.
        # Instead it only cares about the next lowest sequence number.
        if workflow_step := (
            self.workflow.steps.filter(sequence__gt=max_sequence)
            .order_by("sequence")
            .first()
        ):
            self.in_progress()

            return workflow_step.execute(workflow_run=self)
        else:
            return None
