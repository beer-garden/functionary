from django.core.management.base import BaseCommand

from builder.celery import app


# TODO: Lots to do here:
#       1) Make various things configurable. Concurrency, etc.
#       2) Figure out how to get task logging working.
class Command(BaseCommand):
    help = "Run the workers that build package images"

    def handle(self, *args, **options):
        worker = app.Worker()
        worker.start()
