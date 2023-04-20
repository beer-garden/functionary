import os

from .base import *  # noqa

DEBUG = False

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# WhiteNoiseMiddleware must go immediately after SecurityMiddleware
# See https://whitenoise.readthedocs.io/en/stable/django.html#enable-whitenoise
whitenoise_index = 1 + MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
MIDDLEWARE.insert(whitenoise_index, "whitenoise.middleware.WhiteNoiseMiddleware")

STORAGES.update(
    {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        }
    }
)

WHITENOISE_MANIFEST_STRICT = False
