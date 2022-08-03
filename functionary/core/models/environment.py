""" Environment model """
import uuid
from typing import TYPE_CHECKING

from django.db import models

# Avoid circular import when import is needed only for type checking
if TYPE_CHECKING:
    from core.models import Team


class Environment(models.Model):
    """Second tier of a namespacing under Team. Environments act as the primary point
    of association for packages, tasks, etc.

    Attributes:
        id: unique identifier (UUID)
        name: the name of the environment
        team: the Team that this environment belongs to
        default: when true, this environment will act as the default for a Team in
                 cases where an environment is not specified.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    team = models.ForeignKey(
        to="Team", related_name="environments", on_delete=models.CASCADE, db_index=True
    )
    default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "name"], name="team_name_unique_together"
            ),
            models.UniqueConstraint(
                fields=["team", "default"],
                condition=models.Q(default=True),
                name="team_default_true_unique_together",
            ),
        ]

    def __str__(self):
        return f"{self.team.name} - {self.name}"

    @classmethod
    def create_default(cls, team: "Team") -> "Environment":
        """Create a default environment for the provided Team

        Args:
            team: Team to which the created environment will belong and be the default

        Returns:
            The created Environment
        """
        environment = cls.objects.create(name="default", team=team, default=True)
        environment.save()

        return environment
