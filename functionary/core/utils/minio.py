from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.http import HttpRequest
from minio import Minio
from minio.error import S3Error
from urllib3.response import HTTPResponse

from core.models import Task


class MinioInterface:
    def __init__(self, bucket_name: str):
        self.client = Minio(
            endpoint=f"{settings.S3_HOST}:{settings.S3_PORT}",
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_SECURE,
            region=settings.S3_REGION,
        )

        self.bucket_name = bucket_name
        self._create_bucket()

    def bucket_exists(self) -> bool:
        return self.client.bucket_exists(self.bucket_name)

    def put_file(self, file: BytesIO, length: int, filename: str) -> None:
        _ = self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=filename,
            data=file,
            length=length,
        )

    def get_filenames(self) -> list[str]:
        objects = self.client.list_objects(self.bucket_name)
        object_names = []
        for object in objects:
            object_names.append(object.object_name)
        return object_names

    def does_file_exist(self, filename: str) -> bool:
        try:
            _ = self.client.stat_object(self.bucket_name, filename)
            return True
        except S3Error:
            return False

    def get_object(self, filename: str) -> HTTPResponse:
        try:
            if not self.does_file_exist(filename):
                return None
            response: HTTPResponse = self.client.get_object(self.bucket_name, filename)
            return response
        finally:
            response.close()
            response.release_conn()

    def get_presigned_url(self, filename: str) -> str:
        if self.bucket_exists():
            return self.client.get_presigned_url(
                method="GET",
                bucket_name=self.bucket_name,
                object_name=filename,
                expires=timedelta(
                    minutes=settings.S3_SIGNED_URL_TIMEOUT_MINUTES,
                ),
            )

    def _create_bucket(self) -> None:
        if self.bucket_exists():
            return
        self.client.make_bucket(self.bucket_name)

    def delete_bucket(self) -> None:
        if self.bucket_exists():
            self.client.remove_bucket(self.bucket_name)


def handle_file_parameters(
    task: Task,
    request: HttpRequest,
) -> None:
    """Uploads any files in the incoming request to an S3 bucket

    This function will check the request for any files. Each file will
    be uploaded to an S3 bucket that matches the environment ID.
    The file's name will be the same, so to access the file in Minio, you
    would go to <environment_id>/filename

    Arguments:
        task: The task object created as a result of the request
        request: The HttpRequest that the form came from

    Returns:
        None
    """
    if request.FILES:
        minio = MinioInterface(bucket_name=str(task.environment.id))

        for param_name, file in request.FILES.items():
            # Remove parameter prefix
            param_name = param_name.split("-")[-1]
            filename = generate_filename(task, param_name, file.name)
            minio.put_file(file=file.file, length=file.size, filename=filename)


def generate_filename(task: Task, param_name: str, filename: str) -> str:
    """Generate a filename suitable for storage in a bucket

    Generates a filename based on the task id, parameter name, and filename

    Args:
        task: The task object
        param_name: The parameter name
        filename: The filename
    """
    return f"{task.id}/{param_name}/{filename}"
