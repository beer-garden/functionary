from unittest.mock import Mock

import pytest

from core.auth import Role
from core.models import EnvironmentUserRole, Team, User
from ui.views.utils import set_session_environment


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
def test_set_session_environment(environment, user):
    request = Mock()
    request.session = {}
    request.user = user

    set_session_environment(request, environment)

    assert request.session["environment_id"] == str(environment.id)

    # User with READ_ONLY role should have various read permissions
    assert request.session["user_can_read_function"] is True
    assert request.session["user_can_read_task"] is True

    # User with READ_ONLY role should *not* have non-read permissions
    assert request.session["user_can_create_function"] is False
    assert request.session["user_can_create_task"] is False
