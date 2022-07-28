from django.core.management.base import BaseCommand

from builder.celery import app


# TODO: Make various things configurable. Concurrency, etc.
class Command(BaseCommand):
    help = "Run the workers that build package images"

    def handle(self, *args, **options):
        worker = app.Worker()
        worker.start()
