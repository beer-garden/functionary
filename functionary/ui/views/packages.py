from core.models import Package

from .generic import PermissionedDetailView, PermissionedListView


class PackageListView(PermissionedListView):
    model = Package


class PackageDetailView(PermissionedDetailView):
    model = Package

    def get_queryset(self):
        return super().get_queryset().select_related("environment")
