import pytest

from builder import utils
from core.models import Function, Package, Team, User


@pytest.fixture
def user():
    return User.objects.create(username="user")


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def package1(environment):
    return Package.objects.create(name="testpackage1", environment=environment)


@pytest.fixture
def package2(environment):
    return Package.objects.create(name="testpackage2", environment=environment)


@pytest.fixture
def function1(package1):
    function_schema = {
        "title": "test",
        "type": "object",
        "properties": {"prop1": {"type": "integer"}},
    }

    return Function.objects.create(
        name="function1",
        environment=package1.environment,
        package=package1,
        schema=function_schema,
        active=True,
    )


@pytest.fixture
def function2(package1):
    function_schema = {
        "title": "test",
        "type": "object",
        "properties": {"prop1": {"type": "integer"}},
    }

    return Function.objects.create(
        name="function2",
        environment=package1.environment,
        package=package1,
        schema=function_schema,
        active=True,
    )


@pytest.fixture
def function3(package2):
    function_schema = {
        "title": "test",
        "type": "object",
        "properties": {"prop1": {"type": "integer"}},
    }

    return Function.objects.create(
        name="function3",
        environment=package2.environment,
        package=package2,
        schema=function_schema,
        active=True,
    )


@pytest.fixture
def function4(package2):
    function_schema = {
        "title": "test",
        "type": "object",
        "properties": {"prop1": {"type": "integer"}},
    }
    return Function.objects.create(
        name="function4",
        environment=package2.environment,
        package=package2,
        schema=function_schema,
        active=True,
    )


@pytest.fixture
def definitions(function1, function2):
    function_dict1 = {
        "name": function1.name,
        "summary": function1.summary,
        "parameters": [],
        "description": "description",
        "display_name": function1.name,
    }

    function_dict2 = {
        "name": function2.name,
        "summary": function2.summary,
        "parameters": [],
        "description": "description",
        "display_name": function2.name,
    }
    return function_dict1, function_dict2


@pytest.mark.django_db
@pytest.mark.usefixtures("function1", "function2", "function3", "function4")
def test_deactivate_functions(definitions, package1):
    db_functions = Function.objects.all()
    for function in db_functions:
        assert function.active is True

    utils._deactivate_functions(definitions, package1)
    all_functions = Function.objects.all()
    assert all_functions.get(name="function1").active is True
    assert all_functions.get(name="function2").active is True
    assert all_functions.get(name="function3").active is False
    assert all_functions.get(name="function4").active is False
