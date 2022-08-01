""" Team model """
import uuid

from django.apps import apps
from django.db import models, transaction


class Team(models.Model):
    """Namespace that teams of users work under

    Attributes:
        id: unique identifier (UUID)
        name: the name of the team
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True, db_index=True)

    def __str__(self):
        return self.name

    def _post_save(self, creating):
        """Post save hooks"""
        if creating:
            Environment = apps.get_model("core", "Environment")
            Environment.create_default(self)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        with transaction.atomic():
            team = super().save(*args, **kwargs)
            self._post_save(creating)

        return team
