from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import HttpRequest
from django.shortcuts import render
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

        return http.HttpResponseClientRedirect("/ui")

    def get(self, request: HttpRequest):
        envs = self.request.user.environments.select_related("team").order_by(
            "team__name", "name"
        )

        environments = {}
        for env in envs:
            environments.setdefault(env.team.name, []).append(env)

        self.extra_context = {"environments": environments}
        context = self.get_context_data()

        return render(request, "forms/environment_selector.html", context)
