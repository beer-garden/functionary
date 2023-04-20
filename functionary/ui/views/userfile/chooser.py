from django.core.exceptions import ValidationError
from django.forms import BooleanField, FileField, UUIDField
from django.forms.models import ModelForm
from django.shortcuts import render
from django.views.generic.edit import ModelFormMixin
from django_htmx.http import reswap, retarget, trigger_client_event
from django_tables2 import SingleTableView

from core.auth import Operation
from core.models import UserFile
from ui.tables.user_file import SelectableCreatorUserFileTable, SelectableUserFileTable
from ui.views.generic import PermissionedViewMixin


def _get_file_type(request):
    return getattr(request, request.method).get("file_type", "owned")


class UserFileChooserForm(ModelForm):
    """Form for UserFile selection"""

    selected_file = UUIDField(required=True)
    file = FileField(required=False)
    public = BooleanField(required=False)
    template_name = "forms/userfile/file_table.html"

    class Meta:
        model = UserFile
        fields = ["selected_file", "file", "public", "name", "creator", "environment"]

    def clean(self):
        if not self.cleaned_data.get("selected_file", None):
            raise ValidationError("No file selected")
        return self.cleaned_data


class UserFileUploadForm(ModelForm):
    """Form for UserFile uploads"""

    file = FileField(required=False)
    public = BooleanField(required=False)
    template_name = "forms/userfile/upload_card.html"

    class Meta:
        model = UserFile
        fields = ["file", "public", "name", "creator", "environment"]

    def clean_file(self):
        if not (file := self.cleaned_data.get("file", None)):
            raise ValidationError("No file selected")
        return file


class UserFileChooserView(PermissionedViewMixin, SingleTableView, ModelFormMixin):
    """View for selecting or uploading files"""

    model = UserFile
    template_name = "forms/userfile/chooser.html"
    post_action = Operation.READ

    def get_table_class(self):
        if _get_file_type(self.request) == "shared":
            return SelectableCreatorUserFileTable

        return SelectableUserFileTable

    def get_queryset(self):
        qs = super().get_queryset()
        if _get_file_type(self.request) == "shared":
            qs = qs.filter(public=True).exclude(creator=self.request.user)
        else:
            qs = qs.filter(creator=self.request.user)

        return qs.order_by("name")

    def get_context_data(self, **kwargs) -> dict:
        request_data = getattr(self.request, self.request.method, {})
        context = super().get_context_data(**kwargs)
        context["parameter"] = request_data.get("parameter", None)
        context["parameter_id"] = request_data.get("parameter_id", None)
        context["file_type"] = _get_file_type(self.request)
        return context

    def get_form_class(self):
        return (
            UserFileUploadForm
            if self.request.GET.get("upload", False)
            else UserFileChooserForm
        )

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        if data := kwargs.get("data", None):
            data = data.dict()
            env = self.get_environment()
            data["creator"] = self.request.user
            data["environment"] = env

            if (files := kwargs.get("files", None)) and "file" in files:
                data["name"] = files["file"].name
            elif selected_file := data.get("selected_file", None):
                uf = UserFile.objects.filter(environment=env, id=selected_file).first()
                data["name"] = getattr(uf, "name", None)
            kwargs["data"] = data
        return kwargs

    def post(self, request):
        self.object = None
        is_upload = request.GET.get("upload", False)
        selected_file = request.POST.get("selected_file", None)

        form = self.get_form()

        if form.is_valid():
            cleaned_data = form.cleaned_data
            if not is_upload:
                selected_file = cleaned_data["selected_file"]
                self.object = UserFile.objects.filter(id=selected_file).first()
            else:
                self.object = UserFile.objects.create(
                    file=cleaned_data["file"],
                    public=cleaned_data["public"],
                    name=cleaned_data["name"],
                    creator=cleaned_data["creator"],
                    environment=cleaned_data["environment"],
                )

        if self.object:
            # We have successfully selected a file but the table view requires
            # a query_set or object_list when calling get_context_data. Override
            # object_list to be the selected file.
            self.object_list = [self.object]

            context = self.get_context_data()
            context["file_name"] = self.object.name
            context["file_id"] = self.object.pk
            context["widget"] = {
                "attrs": {"id": context["parameter"]},
            }

            response = render(request, "partials/userfile/selected_file.html", context)
            return trigger_client_event(
                reswap(
                    retarget(response, f'#{context["parameter_id"]}-container'),
                    "outerHTML",
                ),
                "fileSelected",
                {
                    "file_id": str(self.object.pk),
                    "file_name": self.object.name,
                },
            )

        # The table is going to be reshown, use the full queryset for the view
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        # The file owned/shared chooser passes in the type parameter
        # so send the table vs the whole chooser
        self.object = None
        if "file_type" in request.GET:
            self.template_name = "partials/userfile/file_table.html"

        return super().get(request, *args, **kwargs)
