""" Package model """
import uuid

from django.conf import settings
from django.db import models
from django.db.models import QuerySet

from core.models import Environment


class Package(models.Model):
    """A Package is a grouping of functions made available for tasking

    Attributes:
        id: unique identifier (UUID)
        environment: the environment that this package belongs to
        name: internal name that published package definition keys off of
        display_name: optional display name
        summary: summary of the package
        description: more details about the package
        language: the language the functions in the package are written in
        image_name: the docker image name for the package
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.ForeignKey(to=Environment, on_delete=models.CASCADE)

    # TODO: This shouldn't be changeable after creation
    name = models.CharField(max_length=64, blank=False)

    display_name = models.CharField(max_length=64, null=True)
    summary = models.CharField(max_length=128, null=True)
    description = models.TextField(null=True)

    # TODO: Restrict to list of choices?
    language = models.CharField(max_length=64)

    image_name = models.CharField(max_length=256)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "name"], name="environment_name_unique_together"
            )
        ]

    def __str__(self):
        return self.name

    def update_image_name(self, image_name: str) -> None:
        """Update the package's image name with the given image name"""
        self.image_name = image_name
        self.save()

    @property
    def render_name(self) -> str:
        """Returns the template-renderable name of the package"""
        return self.display_name if self.display_name else self.name

    @property
    def full_image_name(self) -> str:
        """Returns the package's image name prepended with the registry info"""
        return f"{settings.REGISTRY}/{self.image_name}"

    @property
    def active_functions(self) -> QuerySet:
        """Returns a QuerySet of all active functions in the package"""
        return self.functions.filter(active=True)
