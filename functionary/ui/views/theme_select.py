from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRefresh


class ThemeSelectView(LoginRequiredMixin, TemplateView):
    def post(self, request: HttpRequest):
        theme = request.POST["theme"]
        request.user.set_preference("theme", theme, True)

        return HttpResponseClientRefresh()
