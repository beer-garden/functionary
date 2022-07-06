""" Package model """
import uuid

from django.db import models


class Package(models.Model):
    """A Package is a grouping of functions made available for tasking

    Attributes:
        id: unique identifier (UUID)
        team: the team that this package belongs to
        name: internal name that published package definition keys off of
        display_name: optional display name
        description: more details about the function
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(to="Team", on_delete=models.CASCADE)

    # TODO: This shouldn't be changeable after creation
    name = models.CharField(max_length=64, blank=False)

    display_name = models.CharField(max_length=64, null=True)
    description = models.TextField(null=True)

    # TODO: Restrict to list of choices?
    language = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "name"], name="team_name_unique_together"
            )
        ]

    def __str__(self):
        return self.name
