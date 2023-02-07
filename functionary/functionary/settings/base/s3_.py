from os import getenv

S3_HOST = getenv("S3_HOST")
S3_PORT = getenv("S3_PORT")
S3_REGION = getenv("S3_REGION")
S3_SECURE = False if getenv("S3_SECURE", "false").lower() == "false" else True
S3_ACCESS_KEY = getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = getenv("S3_SECRET_KEY")
S3_SIGNED_URL_TIMEOUT_MINUTES = 1
