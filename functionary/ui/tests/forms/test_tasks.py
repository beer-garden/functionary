import json

import pytest

from core.models import Function, Package, Team
from core.utils.parameter import PARAMETER_TYPE
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
    _function = Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="int_param", parameter_type=PARAMETER_TYPE.INTEGER)
    _function.parameters.create(name="json_param", parameter_type=PARAMETER_TYPE.JSON)
    _function.parameters.create(name="str_param", parameter_type=PARAMETER_TYPE.STRING)

    return _function


@pytest.mark.django_db
def test_taskparametertemplateform_can_load_initial_values(function):
    form = TaskParameterTemplateForm(
        tasked_object=function,
        initial='{"int_param": {{var1}}, "json_param": {{var2}}}',
    )

    assert form.fields["int_param"].initial == "{{var1}}"
    assert form.fields["json_param"].initial == "{{var2}}"


@pytest.mark.django_db
def test_taskparametertemplateform_can_load_mixed_template_initial_values(function):
    str_param_value = "{{var1}} is a good var"
    json_param_value = '{"nested_param": {{var1}}}'

    form = TaskParameterTemplateForm(
        tasked_object=function,
        initial=json.dumps(
            {"str_param": str_param_value, "json_param": json_param_value}
        ),
    )

    assert form.fields["str_param"].initial == str_param_value
    assert form.fields["json_param"].initial == json_param_value


@pytest.mark.django_db
def test_taskparametertemplateform_handles_templating_in_json(function):
    form_data = {"json_param": '{"input": {{parameters.json_param}}}'}

    form = TaskParameterTemplateForm(
        tasked_object=function, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert form_data["json_param"] in form.parameter_template
