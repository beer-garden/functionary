import uuid

from django.conf import settings
from django.db import models


class Workflow(models.Model):
    """A Workflow defines a series of tasks to be executed in sequence.

    Attributes:
        id: unique identifier (UUID)
        environment: the environment that this task belongs to. All queryset filtering
                     should include an environment.
        name: the name of the Workflow
        description: details about the Workflow
        schema: describes the parameters that runs of this Workflow may provide
        creator: the user that initiated the task
        created_at: task creation timestamp
        updated_at: task updated timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.TextField(null=True)
    schema = models.JSONField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    def get_first_step(self):
        """Retrieves the first step of the Workflow"""
        next_steps = list(self.steps.values_list("next", flat=True))

        # The step that has nothing pointing to it as "next" is the first step
        return self.steps.exclude(pk__in=next_steps).get()
