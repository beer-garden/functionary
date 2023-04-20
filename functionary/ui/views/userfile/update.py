from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Environment, UserFile
from ui.views.generic import PermissionedUpdateView


class UserFileUpdateForm(ModelForm):
    """Form for updating UserFile"""

    template_name = "forms/userfile/upload.html"

    class Meta:
        model = UserFile
        fields = ["file", "name"]


class UserFileUpdateView(PermissionedUpdateView):
    """View for updating files"""

    model = UserFile
    form_class = UserFileUpdateForm
    template_name = UserFileUpdateForm.template_name

    def get_queryset(self):
        return super().get_queryset().filter(creator=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = self.kwargs["action"]

        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f"File {self.kwargs['action']}d.")
        return HttpResponseClientRedirect(self.request.headers.get("Referer"))


@require_POST
@login_required
def update_share(request: HttpRequest, pk):
    """Update just the public setting of a UserFile"""

    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.USERFILE_UPDATE, env):
        return HttpResponseForbidden()

    public = request.POST["public"]
    userfile = get_object_or_404(UserFile, pk=pk, environment=env, creator=request.user)

    try:
        userfile.public = str(public).lower() == "true"
        userfile.save()
    except ValueError:
        return HttpResponseBadRequest("Invalid public setting")

    messages.success(request, f"File {'shared' if userfile.public else 'restricted'}.")

    # Return to the page that the user was on
    return redirect(request.headers.get("Referer", "ui:file-list"))
