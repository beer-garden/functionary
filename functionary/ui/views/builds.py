from django.core.exceptions import ObjectDoesNotExist

from builder.models import Build

from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class BuildListView(PermissionedEnvironmentListView):
    model = Build
    order_by_fields = ["-created_at"]
    queryset = Build.objects.select_related("creator", "package").all()


class BuildDetailView(PermissionedEnvironmentDetailView):
    model = Build
    queryset = Build.objects.select_related("creator", "package").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["build_log"] = context["object"].buildlog
        except ObjectDoesNotExist:
            context["build_log"] = None
        return context
