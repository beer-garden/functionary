""" Team model """
import uuid

from django.db import models


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
