import os

REGISTRY_HOST = os.environ.get("REGISTRY_HOST", "localhost")
REGISTRY_PORT = os.environ.get("REGISTRY_PORT", "5000")
REGISTRY = f"{REGISTRY_HOST}:{REGISTRY_PORT}"
