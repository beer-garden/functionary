import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core.utils.parameter import get_schema


class ActiveWorkflowManager(models.Manager):
    """Manager that filters out Workflows marked inactive."""

    def get_queryset(self):
        return super().get_queryset().filter(active=True)


class Workflow(models.Model):
    """A Workflow defines a series of tasks to be executed in sequence.

    Attributes:
        id: unique identifier (UUID)
        environment: the environment that this task belongs to. All queryset filtering
                     should include an environment.
        name: the name of the Workflow
        description: details about the Workflow
        creator: the user that initiated the task
        created_at: task creation timestamp
        updated_at: task updated timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tasks = GenericRelation(
        to="Task", content_type_field="tasked_type", object_id_field="tasked_id"
    )
    scheduled_tasks = GenericRelation(
        to="ScheduledTask",
        content_type_field="tasked_type",
        object_id_field="tasked_id",
    )
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = ActiveWorkflowManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "name"],
                name="workflow_environment_name_unique_together",
            )
        ]
        indexes = [
            models.Index(
                fields=["environment", "creator"], name="workflow_environment_creator"
            ),
            models.Index(
                fields=["environment", "created_at"],
                name="workflow_created_at",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def steps(self):
        """Convenience alias for workflowstep_set"""
        # Provides better static type checking than using related_name
        return self.workflowstep_set  # type: ignore

    @property
    def first_step(self):
        """Retrieves the first step of the Workflow"""
        next_steps = list(self.steps.values_list("next", flat=True))

        # The step that has nothing pointing to it as "next" is the first step
        return self.steps.exclude(pk__in=next_steps).first()

    @property
    def ordered_steps(self):
        """Provides the associated WorkflowSteps as an ordered list"""
        steps = []

        if step := self.first_step:
            steps.append(step)

            while step := step.next:
                steps.append(step)

        return steps

    @property
    def parameters(self):
        """Convenience alias for workflowparameter_set"""
        # Provides better static type checking than using related_name
        return self.workflowparameter_set  # type: ignore

    @property
    def display_name(self) -> str:
        """Returns the template-renderable name of the workflow"""
        return self.name

    @property
    def schema(self) -> dict:
        """Workflow definition schema"""
        return get_schema(self)

    def activate(self):
        """Activate the workflow"""
        self.active = True
        self.save()

    def deactivate(self):
        """Deactivate the workflow and pause any associated scheduled tasks"""
        self.active = False
        self.save()
        self.pause_scheduled_tasks()

    def pause_scheduled_tasks(self) -> None:
        """Pauses all scheduled tasks."""
        # Building the queryset this way lets us avoid importing ScheduledTask
        active_scheduled_tasks = (
            self.scheduled_tasks.all() & self.scheduled_tasks.model.active_objects.all()
        )

        for scheduled_task in active_scheduled_tasks:
            scheduled_task.pause()

    @property
    def is_active(self) -> bool:
        """Returns true if the workflow is active"""
        return self.active

    @property
    def return_type(self) -> str | None:
        """The Workflows return type should be the value of the
        final step in the workflow"""
        last_step = self.ordered_steps[-1]
        return last_step.return_type
