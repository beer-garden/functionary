from django_unicorn.components import UnicornView

from core.models import Environment
from core.models.user_role import EnvironmentUserRole


class EnvToSelectView(UnicornView):
    environments = {}

    def hydrate(self):
        # Clear any old environments first
        self.environments = {}

        if self.request.user.is_superuser:
            envs = Environment.objects.all().order_by("team__name", "name")
            for env in envs:
                self.environments.setdefault(env.team.name, []).append(env)
        else:
            roles = EnvironmentUserRole.objects.filter(user=self.request.user).order_by(
                "environment__team__name", "environment__name"
            )
            for role in roles:
                self.environments.setdefault(role.environment.team.name, []).append(
                    role.environment
                )