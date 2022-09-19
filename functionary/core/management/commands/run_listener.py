from django.core.management.base import BaseCommand

from core.utils.listener import start_listening
from core.utils.messaging import wait_for_connection


class Command(BaseCommand):
    help = "Ingest messages and hand them off to workers to be processed"

    def handle(self, *args, **kwargs):
        wait_for_connection()
        start_listening()
