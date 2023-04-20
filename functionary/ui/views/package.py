from django.urls import reverse

from core.models import Package
from ui.tables.package import PackageFilter, PackageTable

from .generic import PermissionedDetailView, PermissionedListView


class PackageListView(PermissionedListView):
    """List view for the Package model"""

    model = Package
    ordering = ["name"]
    table_class = PackageTable
    filterset_class = PackageFilter
    queryset = Package.active_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [{"label": "Packages"}]

        return context


class PackageDetailView(PermissionedDetailView):
    model = Package

    def get_queryset(self):
        return super().get_queryset().select_related("environment")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {
                "label": "Packages",
                "url": reverse("ui:package-list"),
            },
            {"label": self.object.display_name},
        ]

        return context
