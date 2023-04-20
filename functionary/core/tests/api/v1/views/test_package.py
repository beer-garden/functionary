import pytest
from django.urls import reverse

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
def all_packages(test_package1, test_package2):
    return [test_package1, test_package2]


def test_filterset_name(admin_client, all_packages, request_headers):
    """Filter by package_name"""
    url = reverse("package-list")
    package = all_packages[0]
    response = admin_client.get(
        url,
        data={"name": package.name},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(package.id)


def test_filterset_id(admin_client, all_packages, request_headers):
    """Filter by package_name"""
    url = reverse("package-list")
    package = all_packages[0]
    response = admin_client.get(
        url,
        data={"id": package.id},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(package.id)


def test_filterset_display_name(admin_client, all_packages, request_headers):
    """Filter by package_name"""
    url = reverse("package-list")
    package = all_packages[0]
    response = admin_client.get(
        url,
        data={"display_name": package.display_name},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(package.id)
