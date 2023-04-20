from django.contrib import messages
from django.forms import ModelForm
from django.shortcuts import get_object_or_404
from django_htmx.http import HttpResponseClientRedirect

from core.models import Environment, UserFile
from ui.views.generic import PermissionedCreateView


class UserFileCreateForm(ModelForm):
    """Form for File creation"""

    template_name = "forms/userfile/upload.html"

    class Meta:
        model = UserFile
        fields = ["file", "public", "name", "creator", "environment"]


class UserFileCreateView(PermissionedCreateView):
    """View for uploading files"""

    model = UserFile
    form_class = UserFileCreateForm
    template_name = UserFileCreateForm.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        return context

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        if data := kwargs.get("data", None):
            data = data.dict()
            data["creator"] = self.request.user
            data["environment"] = get_object_or_404(
                Environment, id=self.request.session.get("environment_id")
            )

            if (files := kwargs.get("files", None)) and "file" in files:
                data["name"] = files["file"].name
            kwargs["data"] = data
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "File uploaded.")
        return HttpResponseClientRedirect(self.request.headers.get("Referer"))
