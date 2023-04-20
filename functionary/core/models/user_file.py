""" File model """
import uuid

from django.conf import settings
from django.db import models


def _get_upload_to(instance: "UserFile", filename: str) -> str:
    """Construct the root path for file uploads"""
    return ("/").join(
        [
            str(instance.environment.id),
            "user_files",
            instance.creator.username,
            str(instance.id),
        ]
    )


class UserFile(models.Model):
    """Model for user files to be used as tasking input

    Attributes:
        id: Unique identifier (UUID)
        environment: Environment that the file belongs to
        name: File name
        file: Reference to the actual file in storage
        public: Whether this file should be accessible to all users of the Environment
        creator: User that uploaded the file
        created_at: When the file was uploaded
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    file = models.FileField(upload_to=_get_upload_to)
    public = models.BooleanField(default=False)
    creator = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["environment", "public", "name"],
                name="uf_env_public_name",
                condition=models.Q(public=True),
            ),
            models.Index(
                fields=["environment", "creator", "name"],
                name="uf_env_creator_name",
            ),
            models.Index(
                fields=["environment", "created_at"],
                name="uf_env_type_creator",
            ),
        ]

    def __str__(self):
        return self.name
