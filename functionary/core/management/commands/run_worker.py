from django.core.management.base import BaseCommand

from core.celery import app
from core.utils.messaging import initialize_messaging, wait_for_connection


# TODO: Make various things configurable. Concurrency, etc.
class Command(BaseCommand):
    help = "Run the task workers"

    def handle(self, *args, **options):
        wait_for_connection()

        # TODO: Once there's a proper runner registration process, the need for this
        #       largely goes away and it can potentially be moved to a mangement
        #       command.
        initialize_messaging()

        worker = app.Worker()
        worker.start()
