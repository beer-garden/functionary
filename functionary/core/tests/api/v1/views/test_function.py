import pytest
from django.urls import reverse

from core.models import Environment, Function, Package, Team
from core.models.package import PACKAGE_STATUS
from core.utils.parameter import PARAMETER_TYPE


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
        name="testpackage1", environment=environment, status=PACKAGE_STATUS.ACTIVE
    )


@pytest.fixture
def test_package2(environment: Environment) -> Package:
    return Package.objects.create(
        name="testpackage2", environment=environment, status=PACKAGE_STATUS.ACTIVE
    )


@pytest.fixture
def function1(test_package1: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction1",
        display_name="display_name1",
        package=test_package1,
        environment=test_package1.environment,
    )

    _function.parameters.create(name="int_param", parameter_type=PARAMETER_TYPE.INTEGER)
    _function.parameters.create(name="str_param", parameter_type=PARAMETER_TYPE.STRING)
    _function.parameters.create(name="json_param", parameter_type=PARAMETER_TYPE.JSON)
    _function.parameters.create(name="file_param", parameter_type=PARAMETER_TYPE.FILE)

    return _function


@pytest.fixture
def function2(test_package2: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction2",
        display_name="display_name2",
        package=test_package2,
        environment=test_package2.environment,
    )

    _function.parameters.create(name="int_param", parameter_type=PARAMETER_TYPE.INTEGER)
    _function.parameters.create(name="str_param", parameter_type=PARAMETER_TYPE.STRING)
    _function.parameters.create(name="json_param", parameter_type=PARAMETER_TYPE.JSON)
    _function.parameters.create(name="file_param", parameter_type=PARAMETER_TYPE.FILE)

    return _function


@pytest.fixture
def all_functions(function1, function2):
    return [function1, function2]


def test_filterset_id(admin_client, all_functions, request_headers):
    """Filter by ID"""
    url = reverse("function-list")
    function = all_functions[0]
    response = admin_client.get(
        url,
        data={"id": function.id},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(function.id)


def test_filterset_name(admin_client, all_functions, request_headers):
    """Filter by Name"""
    url = reverse("function-list")
    function = all_functions[0]
    response = admin_client.get(
        url,
        data={"name": function.name},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(function.id)


def test_filterset_display_name(admin_client, all_functions, request_headers):
    """Filter by display name"""
    url = reverse("function-list")
    function = all_functions[0]
    response = admin_client.get(
        url,
        data={"display_name": function.display_name},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(function.id)


def test_filterset_package_id(admin_client, all_functions, request_headers):
    """Filter by package_id"""
    url = reverse("function-list")
    function = all_functions[0]
    response = admin_client.get(
        url,
        data={"package__id": function.package.id},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(function.id)


def test_filterset_package_name(admin_client, all_functions, request_headers):
    """Filter by package_name"""
    url = reverse("function-list")
    function = all_functions[0]
    response = admin_client.get(
        url,
        data={"package__name": function.package.name},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(function.id)
