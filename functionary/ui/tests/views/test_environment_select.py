import pytest
from django.urls import reverse

from core.auth import Role
from core.models import Environment, EnvironmentUserRole, Package, Team, User


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def environment_with_no_users():
    team2 = Team.objects.create(name="team2")
    return Environment.objects.create(team=team2, name="nousers")


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def user_with_access(environment):
    user_obj = User.objects.create(username="hasaccess")

    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.READ_ONLY.name, environment=environment
    )

    return user_obj


@pytest.fixture
def user_without_access():
    return User.objects.create(username="noaccess")


@pytest.mark.django_db
def test_environment_select_get(
    client, environment, environment_with_no_users, user_with_access
):
    client.force_login(user_with_access)

    url = reverse("ui:set-environment")
    response = client.get(url)
    response_body = response.content.decode()

    assert str(environment.id) in response_body
    assert str(environment_with_no_users.id) not in response_body


@pytest.mark.django_db
def test_environment_select_post(client, environment, user_with_access):
    client.force_login(user_with_access)

    url = reverse("ui:set-environment")
    response = client.post(url, {"environment_id": str(environment.id)})

    assert response.status_code == 200
    assert client.session.get("environment_id") == str(environment.id)


@pytest.mark.django_db
def test_environment_select_post_returns_403_for_no_access(
    client, environment, user_without_access
):
    client.force_login(user_without_access)

    url = reverse("ui:set-environment")
    response = client.post(url, {"environment_id": str(environment.id)})

    assert response.status_code == 403
    assert client.session.get("environment_id") != str(environment.id)
