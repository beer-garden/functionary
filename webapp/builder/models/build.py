""" Build model """
import uuid

from django.db import models

from core.models import Package, User


class Build(models.Model):
    """Tracks the package build status and history

    Attributes:
        created_at: time that the build was created
        updated_at: time of the most recent status update
        status: current status of the build
        package: reference to the Package created by a successful build. Will not be
                 set for builds that have failed or are in progress.
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

    STATUS_CHOICES = [
        (IN_PROGRESS, "In Progress"),
        (COMPLETE, "Complete"),
        (ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    creator = models.ForeignKey(to=User, on_delete=models.CASCADE, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="PENDING")
    package = models.ForeignKey(
        to=Package, on_delete=models.CASCADE, blank=True, null=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "created_at"], name="build_status_created_at"
            ),
            models.Index(
                fields=["status", "updated_at"], name="build_status_updated_at"
            ),
        ]

    def __str__(self):
        return f"{self.id}"


class BuildResource(models.Model):
    """Houses resources needed to perform a package build

    Attributes:
        package_contents: gzipped tarball containing package files
        package_definition: defines the package and its functions
        package_definition_version: the schema version used by package_definition
        build: the build with which these resources are associated
    """

    package_contents = models.BinaryField()
    package_definition = models.JSONField()
    package_definition_version = models.CharField(max_length=16)
    build = models.OneToOneField(
        to=Build, on_delete=models.CASCADE, related_name="resources"
    )
