from unittest.mock import Mock

import pytest

from core.auth import Role
from core.models import EnvironmentUserRole, Team, User
from ui.views.context_processors import user_environments


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def user(environment):
    user_obj = User.objects.create(username="hasaccess")

    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.READ_ONLY.name, environment=environment
    )

    return user_obj


@pytest.mark.django_db
def test_user_environments(environment, user):
    """user's environments are returned by the user_environments context processor"""
    request = Mock()
    request.user = user

    context = user_environments(request)

    assert environment in context["user_environments"][environment.team.name]
