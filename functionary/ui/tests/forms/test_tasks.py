import json
from datetime import datetime

import pytest

from core.models import Function, Package, Team, User, UserFile
from core.utils.parameter import DATE_FORMAT, DATETIME_FORMAT, PARAMETER_TYPE
from ui.forms.tasks import TaskParameterForm, TaskParameterTemplateForm


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def param_options():
    return ["option1", "option2"]


@pytest.fixture
def function(package, param_options):
    _function = Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(
        name="bool_param", parameter_type=PARAMETER_TYPE.BOOLEAN
    )
    _function.parameters.create(name="date_param", parameter_type=PARAMETER_TYPE.DATE)
    _function.parameters.create(
        name="datetime_param", parameter_type=PARAMETER_TYPE.DATETIME
    )
    _function.parameters.create(name="float_param", parameter_type=PARAMETER_TYPE.FLOAT)
    _function.parameters.create(name="int_param", parameter_type=PARAMETER_TYPE.INTEGER)

    _function.parameters.create(name="json_param", parameter_type=PARAMETER_TYPE.JSON)
    _function.parameters.create(name="str_param", parameter_type=PARAMETER_TYPE.STRING)
    _function.parameters.create(
        name="str_param_with_options",
        parameter_type=PARAMETER_TYPE.STRING,
        options=param_options,
    )
    _function.parameters.create(name="file_param", parameter_type=PARAMETER_TYPE.FILE)

    return _function


@pytest.fixture
def user():
    return User.objects.create(username="user")


@pytest.fixture
def personal_file(environment, user):
    return UserFile.objects.create(
        environment=environment, creator=user, name="personal_file", public=False
    )


@pytest.fixture
def public_file_of_another_user(environment, admin_user):
    return UserFile.objects.create(
        environment=environment, creator=admin_user, name="public_file", public=True
    )


@pytest.fixture
def private_file_of_another_user(environment, admin_user):
    return UserFile.objects.create(
        environment=environment, creator=admin_user, name="private_file", public=False
    )


@pytest.mark.django_db
def test_taskparametertemplateform_can_load_initial_values(function, user):
    form = TaskParameterTemplateForm(
        tasked_object=function,
        creator=user,
        initial="""
            {
                "bool_param": {{bool_param}},
                "date_param": "{{date_param}}",
                "datetime_param": "{{datetime_param}}",
                "float_param": {{float_param}},
                "int_param": {{int_param}},
                "json_param": {{json_param}},
                "str_param": "{{str_param}}",
                "str_param_with_options": "{{str_param_with_options}}"
            }
        """,
    )

    assert form.fields["bool_param"].initial == "{{bool_param}}"
    assert form.fields["date_param"].initial == "{{date_param}}"
    assert form.fields["datetime_param"].initial == "{{datetime_param}}"
    assert form.fields["float_param"].initial == "{{float_param}}"
    assert form.fields["int_param"].initial == "{{int_param}}"
    assert form.fields["json_param"].initial == "{{json_param}}"
    assert form.fields["str_param"].initial == "{{str_param}}"
    assert form.fields["str_param_with_options"].initial == "{{str_param_with_options}}"


@pytest.mark.django_db
def test_taskparametertemplateform_can_load_mixed_template_initial_values(
    function, user
):
    str_param_value = "{{var1}} is a good var"
    json_param_value = '{"nested_param": {{var1}}}'

    form = TaskParameterTemplateForm(
        tasked_object=function,
        creator=user,
        initial=json.dumps(
            {"str_param": str_param_value, "json_param": json_param_value}
        ),
    )

    assert form.fields["str_param"].initial == str_param_value
    assert form.fields["json_param"].initial == json_param_value


@pytest.mark.django_db
def test_taskparametertemplateform_handles_templating_in_json(function, user):
    form_data = {"json_param": '{"input": {{parameters.json_param}}}'}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert form_data["json_param"] in form.parameter_template


@pytest.mark.django_db
def test_taskparametertemplateform_handles_booleans(function, user):
    form_data = {"bool_param": True}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert '"bool_param": true' in form.parameter_template


@pytest.mark.django_db
def test_taskparametertemplateform_handles_dates(function, user):
    date_value = datetime.now().strftime(DATE_FORMAT)
    form_data = {"date_param": date_value}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert date_value in form.parameter_template


@pytest.mark.django_db
def test_taskparametertemplateform_handles_datetimes(function, user):
    datetime_value = datetime.now().strftime(DATETIME_FORMAT)
    form_data = {"datetime_param": datetime_value}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert datetime_value in form.parameter_template


@pytest.mark.django_db
def test_taskparametertemplateform_handles_floats(function, user):
    form_data = {"float_param": 4.2}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert '"float_param": 4.2' in form.parameter_template


@pytest.mark.django_db
def test_taskparametertemplateform_handles_integers(function, user):
    form_data = {"int_param": 42}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert '"int_param": 42' in form.parameter_template


@pytest.mark.django_db
def test_taskparametertemplateform_handles_strings(function, user):
    form_data = {"str_param": "forty two"}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert '"str_param": "forty two"' in form.parameter_template


@pytest.mark.django_db
def test_taskparameterform_limits_file_choices(
    function,
    user,
    personal_file,
    public_file_of_another_user,
    private_file_of_another_user,
):
    """TaskParameterTemplateForm should limit the choices for FILE fields to files owned
    by the tasking user or files marked as public"""
    form = TaskParameterForm(tasked_object=function, creator=user)
    file_parameter = function.parameters.get(parameter_type=PARAMETER_TYPE.FILE)

    eligible_files = form.fields[file_parameter.name].queryset.all()

    # The personal and public file should be present. The private one should not.
    assert personal_file in eligible_files
    assert public_file_of_another_user in eligible_files
    assert private_file_of_another_user not in eligible_files


@pytest.mark.django_db
def test_taskparameterform_casts_file_id_as_str(function, user, personal_file):
    """TaskParameterForm supplies a str as the cleaned_data value for FILE parameters"""
    file_parameter = function.parameters.get(parameter_type=PARAMETER_TYPE.FILE)

    form = TaskParameterForm(
        tasked_object=function,
        data={file_parameter.name: str(personal_file.id)},
        creator=user,
        prefix=None,
    )

    _ = form.is_valid()

    # Default ModelChoiceField behavior would be to return the model instance object.
    # Here we verify that our custom field that builds on ModelChoiceField correctly
    # results in the instance id coming back as a string instead.
    assert form.cleaned_data[file_parameter.name] == str(personal_file.id)


@pytest.mark.django_db
def test_taskparametertemplateform_handles_str_with_options(
    function, user, param_options
):
    form_data = {"str_param_with_options": param_options[0]}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert form.is_valid()
    assert f'"str_param_with_options": "{param_options[0]}"' in form.parameter_template


@pytest.mark.django_db
def test_taskparametertemplateform_handles_str_with_invalid_option(function, user):
    form_data = {"str_param_with_options": "invalid"}

    form = TaskParameterTemplateForm(
        tasked_object=function, creator=user, data=form_data, prefix=None
    )

    assert not form.is_valid()
    assert '"str_param_with_options": "invalid"' not in form.parameter_template
