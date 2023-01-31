from core.models import Package

from .generic import PermissionedDetailView, PermissionedListView

PAGINATION_AMOUNT = 15


class PackageListView(PermissionedListView):
    model = Package
    paginate_by = PAGINATION_AMOUNT


class PackageDetailView(PermissionedDetailView):
    model = Package

    def get_queryset(self):
        return super().get_queryset().select_related("environment")
