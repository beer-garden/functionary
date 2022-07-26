"""Settings specific to the builder app"""
import os

BUILDER_WORKDIR_BASE = os.environ.get("BUILDER_WORKDIR_BASE", "/tmp")
