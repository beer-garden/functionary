from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import HttpRequest
from django.views.generic import TemplateView
from django_htmx import http

from ui.views.utils import set_session_environment


class EnvironmentSelectView(LoginRequiredMixin, TemplateView):
    def post(self, request: HttpRequest):
        pk = request.POST["environment_id"]

        try:
            environment = request.user.environments.get(pk=pk)
        except ObjectDoesNotExist:
            raise PermissionDenied

        set_session_environment(request, environment)

        return http.HttpResponseClientRedirect("/")
