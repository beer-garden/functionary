"""Test login views"""
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from core.auth import Role
from core.models import EnvironmentUserRole, Team, User
from ui.views.login import NO_ENVIRONMENTS_MESSAGE

if TYPE_CHECKING:
    from django.test.client import Client

TRUSTED_HEADER = "X-Username"


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def user(environment):
    user_ = User.objects.create(username="testuser")

    EnvironmentUserRole.objects.create(
        user=user_,
        environment=environment,
        role=Role.DEVELOPER.name,
    )

    return user_


@pytest.fixture
def user_without_role():
    return User.objects.create(username="roleless_user")


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_login_automatically_authenticates_via_trusted_header(
    client: "Client", user: User
):
    """LoginView should automatically authenticate a user if a valid trusted header
    value is supplied"""

    url = reverse("account_login")
    destination = "/somewhere"
    response = client.get(
        url, data={"next": destination}, headers={TRUSTED_HEADER: user.username}
    )

    # 302 Redirect expected on successful auto-login
    assert response.status_code == 302
    assert response.url == destination


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_login_does_not_auto_login_with_bad_trusted_header_value(client: "Client"):
    """LoginView should render the login form rather than auto login if the trusted
    header value supplied does not match a valid user"""

    url = reverse("account_login")
    response = client.get(url, headers={TRUSTED_HEADER: "notauser"})

    # 200 Indicates the "GET" succeeded and the login form was rendered
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_login_sets_theme(client: "Client", user: User):
    """Ensure that the theme is set on login"""

    url = reverse("account_login")
    destination = "/somewhere"

    assert not user.get_preference("theme")

    # Check the trusted header path
    client.get(url, data={"next": destination}, headers={TRUSTED_HEADER: user.username})

    user.refresh_from_db()
    assert user.get_preference("theme") == "light"

    # Check the separate path for user/pass login
    user.set_password("test_password")
    user.set_preference("theme", None)
    user.save()
    user.refresh_from_db()

    assert not user.get_preference("theme")

    login_data = {"login": user.username, "password": "test_password"}
    response = client.post(f"{url}?next={destination}", data={**login_data})

    assert response.status_code == 302

    user.refresh_from_db()
    assert user.get_preference("theme") == "light"


@pytest.mark.django_db
@pytest.mark.override_config(
    TRUSTED_HEADER_AUTHENTICATION_HEADER=TRUSTED_HEADER,
    TRUSTED_HEADER_AUTHENTICATION_ENABLED=True,
)
def test_login_requires_environment(client: "Client", user_without_role: User):
    """Ensure that a user without access to an environment can't log in"""

    url = reverse("account_login")
    destination = "/somewhere"

    # Check the trusted header path
    response = client.get(
        url,
        data={"next": destination},
        headers={TRUSTED_HEADER: user_without_role.username},
    )

    assert response.status_code == 200
    assert NO_ENVIRONMENTS_MESSAGE in response.content.decode()

    # Check the separate path for user/pass login
    user_without_role.set_password("test_password")
    user_without_role.save()
    user_without_role.refresh_from_db()

    login_data = {"login": user_without_role.username, "password": "test_password"}
    response = client.post(f"{url}?next={destination}", data={**login_data})

    assert response.status_code == 200
    assert NO_ENVIRONMENTS_MESSAGE in response.content.decode()
