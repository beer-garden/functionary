from allauth.account.views import LoginView as AllAuthLoginView
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.http import HttpResponseRedirect

from core.auth.backends import CoreBackend
from ui.views.utils import set_session_environment

NO_ENVIRONMENTS_MESSAGE = (
    "Access Denied: You are not a member of any Environments. "
    "Contact an admin to request access and then try again."
)


def _get_session_environment(user):
    """Picks an active environment for the user"""

    # Query against the user's environments rather than getting the environment
    # directly to ensure the user still has access.
    previous_session_environment = user.environments.filter(
        id=user.get_preference("environment")
    ).first()

    return (
        previous_session_environment
        or user.environments.order_by("team__name", "name").first()
    )


def _ensure_theme_selected(request):
    """Default the user to the light theme if nothing is selected"""
    if not request.user.get_preference("theme"):
        request.user.set_preference("theme", "light", True)


class LoginView(AllAuthLoginView):
    def get(self, request, *args, **kwargs):
        """Custom LoginView that will auto-login a user if the CoreBackend's trusted
        header authentication is enabled."""
        if authenticated_user := CoreBackend().authenticate(request):
            if environment := _get_session_environment(authenticated_user):
                auth_login(
                    request, authenticated_user, "core.auth.backends.CoreBackend"
                )
                set_session_environment(request, environment)
                _ensure_theme_selected(self.request)
                redirect = request.GET.get("next", "/")
                return HttpResponseRedirect(redirect)
            else:
                messages.error(request, NO_ENVIRONMENTS_MESSAGE)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle login form and set session environment"""
        if environment := _get_session_environment(form.user):
            response = super().form_valid(form)

            # HttpResponseRedirect is the expected response type on successful login
            # form processing, so only set the session environment in that case.
            if type(response) == HttpResponseRedirect:
                set_session_environment(self.request, environment)
                _ensure_theme_selected(self.request)

            return response
        else:
            messages.error(self.request, NO_ENVIRONMENTS_MESSAGE)
            return self.render_to_response(self.get_context_data(form=form))
