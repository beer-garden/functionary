from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ui.views.utils import set_session_environment


@login_required
def home(request):
    if "environment_id" not in request.session:
        environment = request.user.environments.order_by("team__name", "name").first()
        set_session_environment(request, environment)

    return redirect("ui:task-list")
