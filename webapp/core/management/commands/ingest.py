from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ingest messages and hand them off to workers to be processed"

    # TODO: Implement
    def handle(self, *args, **kwargs):
        pass
