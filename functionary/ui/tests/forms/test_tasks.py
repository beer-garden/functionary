import pytest

from core.models import Function, Package, Team
from ui.forms.tasks import TaskParameterTemplateForm


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    function_schema = {
        "title": "test",
        "type": "object",
        "properties": {
            "int_param": {"type": "integer", "title": "int_param"},
            "json_param": {"type": "json", "title": "json_param"},
        },
    }
    return Function.objects.create(
        name="testfunction", package=package, schema=function_schema
    )


@pytest.mark.django_db
def test_taskparametertemplateform_can_load_initial_values(function):
    form = TaskParameterTemplateForm(
        function=function,
        initial='{"int_param": {{var1}}, "json_param": {{var2}}}',
    )

    assert form.fields["int_param"].initial == "{{var1}}"
    assert form.fields["json_param"].initial == "{{var2}}"
