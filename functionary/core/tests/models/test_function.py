import pytest
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from core.models import Function, Package, ScheduledTask, Task, Team, User
from core.models.package import PACKAGE_STATUS


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
def package(environment):
    return Package.objects.create(
        name="testpackage", environment=environment, status=PACKAGE_STATUS.ACTIVE
    )


@pytest.fixture
def disabled_package(environment):
    return Package.objects.create(
        name="disabledpackage", environment=environment, status=PACKAGE_STATUS.DISABLED
    )


@pytest.fixture
def function(package):
    return Function.objects.create(
        name="testfunction",
        environment=package.environment,
        package=package,
        active=True,
    )


@pytest.fixture
def active_function_disabled_package(disabled_package):
    return Function.objects.create(
        name="activefunction_disabledpackage",
        environment=disabled_package.environment,
        package=disabled_package,
        active=True,
    )


@pytest.fixture
def task(function, environment, user):
    return Task.objects.create(
        function=function,
        environment=environment,
        parameters={"prop1": "value1"},
        creator=user,
    )


@pytest.fixture
def periodic_task():
    return PeriodicTask.objects.create(
        name="periodicTemp",
        task="task1",
        crontab=CrontabSchedule.objects.create(hour=7, minute=30, day_of_week=1),
    )


@pytest.fixture
def scheduled_task(function, environment, user, periodic_task):
    return ScheduledTask.objects.create(
        name="testtask",
        description="description",
        creator=user,
        tasked_object=function,
        environment=environment,
        parameters={"name": "input", "summary": "summary", "type": "text"},
        periodic_task=periodic_task,
        status=ScheduledTask.ACTIVE,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("scheduled_task")
def test_deactivate(function):
    """This marks the function to inactive and scheduled tasks to pause"""
    assert function.active is True
    assert function.scheduled_tasks.filter(status=ScheduledTask.ACTIVE).exists()

    function.deactivate()
    assert function.active is False

    for scheduled_t in function.scheduled_tasks.all():
        assert scheduled_t.status == ScheduledTask.PAUSED


@pytest.mark.django_db
@pytest.mark.usefixtures("package", "disabled_package")
def test_active_functions(function, active_function_disabled_package):
    """This checks filtering of functions that are inactive or who
    belong to packages which are disabled"""
    assert function.active is True
    assert active_function_disabled_package.active is True

    active_functions = Function.active_objects.all()
    assert len(active_functions) == 1
    assert active_function_disabled_package not in active_functions
    assert function in active_functions

    function.deactivate()
    active_functions = Function.active_objects.all()
    assert len(active_functions) == 0
