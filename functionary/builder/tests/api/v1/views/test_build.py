import pytest
from django.urls import reverse

from builder.models import Build
from core.models import Environment, Package, Team
from core.models.package import PACKAGE_STATUS


@pytest.fixture
def environment() -> Environment:
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def request_headers(environment: Environment) -> dict:
    return {"X-Environment-Id": str(environment.id)}


@pytest.fixture
def test_package1(environment: Environment) -> Package:
    return Package.objects.create(
        name="testpackage1",
        display_name="display_name1",
        environment=environment,
        status=PACKAGE_STATUS.ACTIVE,
    )


@pytest.fixture
def test_package2(environment: Environment) -> Package:
    return Package.objects.create(
        name="testpackage2",
        display_name="display_name2",
        environment=environment,
        status=PACKAGE_STATUS.ACTIVE,
    )


@pytest.fixture
def test_build1(environment: Environment, test_package1: Package, admin_user) -> Build:
    return Build.objects.create(
        environment=environment,
        package=test_package1,
        status="PENDING",
        creator=admin_user,
    )


@pytest.fixture
def test_build2(environment: Environment, test_package2: Package, admin_user) -> Build:
    return Build.objects.create(
        environment=environment,
        package=test_package2,
        status="PENDING",
        creator=admin_user,
    )


@pytest.fixture
def all_builds(test_build1, test_build2):
    return [test_build1, test_build2]


def test_filterset_id(admin_client, all_builds, request_headers):
    """Filter by build_id"""
    url = reverse("build-list")
    build = all_builds[0]
    response = admin_client.get(
        url,
        data={"id": build.id},
        headers={
            **request_headers,
        },
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(build.id)


def test_filterset_package_name(admin_client, all_builds, request_headers):
    """Filter by package_name"""
    url = reverse("build-list")
    build = all_builds[0]
    response = admin_client.get(
        url,
        data={"package__name": build.package.name},
        headers={
            **request_headers,
        },
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(build.id)


def test_filterset_package_id(admin_client, all_builds, request_headers):
    """Filter by package_id"""
    url = reverse("build-list")
    build = all_builds[0]
    response = admin_client.get(
        url,
        data={"package__id": build.package.id},
        headers={
            **request_headers,
        },
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(build.id)
