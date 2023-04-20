from core.models import UserFile
from ui.tables.user_file import UserFileFilter, UserFileTable
from ui.views.generic import PermissionedListView


class UserFileListView(PermissionedListView):
    """List view for the UserFile model"""

    model = UserFile
    ordering = ["name"]
    table_class = UserFileTable
    template_name = "core/userfile_list.html"
    filterset_class = UserFileFilter

    def get_queryset(self):
        user = self.request.user
        queryset = (
            super()
            .get_queryset()
            .filter(creator=user)
            .select_related("environment", "creator")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [{"label": "Files"}]

        return context
