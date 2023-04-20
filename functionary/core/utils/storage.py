import os

from storages.backends.s3boto3 import S3Boto3Storage

from core.utils.constance import get_config


def _get_endpoint_url(config) -> str:
    """Builds the endpoint_url settings for S3Storage"""
    protocol = "https" if config.S3_SECURE else "http"
    host = os.getenv("S3_HOST", config.S3_HOST)
    port = config.S3_PORT

    return f"{protocol}://{host}:{port}"


class S3Storage(S3Boto3Storage):
    """S3 storage backend that pulls its settings from constance"""

    def __init__(self, *args, **kwargs):
        config = get_config(
            [
                "S3_ACCESS_KEY",
                "S3_SECRET_KEY",
                "S3_REGION",
                "S3_BUCKET",
                "S3_SECURE",
                "S3_HOST",
                "S3_PORT",
            ]
        )
        self.access_key = config.S3_ACCESS_KEY
        self.secret_key = config.S3_SECRET_KEY
        self.region_name = config.S3_REGION
        self.bucket_name = config.S3_BUCKET
        self.endpoint_url = _get_endpoint_url(config)
        self.use_ssl = config.S3_SECURE
        super().__init__(*args, **kwargs)
