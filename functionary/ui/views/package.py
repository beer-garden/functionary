from core.models import Package
from ui.tables.package import PackageFilter, PackageTable

from .generic import PermissionedDetailView, PermissionedListView


class PackageListView(PermissionedListView):
    model = Package
    table_class = PackageTable
    filterset_class = PackageFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb"] = "Package List"

        return context


class PackageDetailView(PermissionedDetailView):
    model = Package

    def get_queryset(self):
        return super().get_queryset().select_related("environment")
