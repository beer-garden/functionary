import json
from functools import cached_property

from django.core.files.base import ContentFile
from django.db import models


def _get_upload_to(instance: "TaskOutput", _) -> str:
    """Construct the path for task output files"""
    return ("/").join(
        [
            str(instance.task.environment.id),
            instance.storage_folder,
            str(instance.task.id),
        ]
    )


class TaskOutput(models.Model):
    task = models.OneToOneField(primary_key=True, to="Task", on_delete=models.CASCADE)
    file = models.FileField(upload_to=_get_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def get_content(self):
        """Returns the file contents"""
        return self.file.read().decode() if self.file else None

    def save_content(self, content: str) -> None:
        """Helper for setting the file contents from a string. Automatically
        saves the instance."""

        # NOTE: Ensuring that we do not store empty files would normally not be worth
        # the effort, but a bug in boto3 causes issues after uploading an empty file.
        # see:
        # https://github.com/minio/minio/issues/6540
        #    and
        # https://github.com/boto/boto3/issues/1341
        if len(content) > 0:
            self.file.save(str(self.task.id), ContentFile(content.encode()))
        else:
            # Save the instance to ensure consistent behavior
            self.save()


class TaskLog(TaskOutput):
    """Log output from the execution of a Task"""

    storage_folder = "task_logs"

    @cached_property
    def log(self) -> str | None:
        """Returns the TaskLog file contents"""
        return self.get_content()

    def save_log(self, log: str) -> None:
        """Helper for setting the log file contents from a string. Automatically saves
        the instance."""
        self.save_content(log)


class TaskResult(TaskOutput):
    """Results from the execution of a Task"""

    storage_folder = "task_results"

    @cached_property
    def result(self):
        """Returns the TaskLog file contents"""
        return self.get_content()

    @property
    def json(self):
        """Return the result as loaded JSON rather than the raw string"""
        return json.loads(self.result) if self.result else None

    def save_result(self, result: str) -> None:
        """Helper for setting the result file contents from a string. Automatically
        saves the instance."""
        self.save_content(result)
