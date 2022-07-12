"""Settings specific to the builder app"""
import os

BUILDER_WORKDIR_BASE = os.environ.get("BUILDER_WORKDIR_BASE", "/tmp")
BUILDER_REGISTRY = os.environ.get("BUILDER_REGISTRY", "localhost:5000")
