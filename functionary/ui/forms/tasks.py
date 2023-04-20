import datetime
import json
import re
from typing import TYPE_CHECKING, Tuple, Type, Union

from django.db.models import Q
from django.forms import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    Field,
    FloatField,
    Form,
    IntegerField,
    JSONField,
    ModelChoiceField,
    Textarea,
    TextInput,
    TypedChoiceField,
)
from django.forms.widgets import DateInput, DateTimeInput, Widget

from core.models import UserFile
from core.utils.parameter import DATE_FORMAT, DATETIME_FORMAT, PARAMETER_TYPE
from ui.views.task.utils import parse_parameter_template

if TYPE_CHECKING:
    from core.models import Environment, Function, User, Workflow


class HTMLDateInput(DateInput):
    input_type = "date"


class HTMLDateTimeInput(DateTimeInput):
    input_type = "datetime-local"


class UploadableFileInput(TextInput):
    template_name = "forms/widgets/uploadable_file.html"

    def get_context(self, name, value, attrs):
        if value:
            attrs.update({"file_name": UserFile.objects.filter(id=value).get().name})
        return super().get_context(name, value, attrs)


class PrimaryKeyModelChoiceField(ModelChoiceField):
    """Custom ModelChoiceField that returns the pk cast as a str for its value"""

    def to_python(self, value) -> str | None:
        """Returns the pk of the model instance as a str for use as a task parameter"""
        if instance := super().to_python(value):
            return str(instance.id)
        else:
            return None


_field_mapping = {
    PARAMETER_TYPE.INTEGER: (IntegerField, None),
    PARAMETER_TYPE.STRING: (CharField, None),
    PARAMETER_TYPE.TEXT: (CharField, Textarea),
    PARAMETER_TYPE.FLOAT: (FloatField, None),
    PARAMETER_TYPE.FILE: (PrimaryKeyModelChoiceField, UploadableFileInput),
    PARAMETER_TYPE.BOOLEAN: (BooleanField, None),
    PARAMETER_TYPE.DATE: (DateField, HTMLDateInput),
    PARAMETER_TYPE.DATETIME: (
        DateTimeField,
        HTMLDateTimeInput,
    ),
    PARAMETER_TYPE.JSON: (JSONField, Textarea),
}

_type_mapping = {
    PARAMETER_TYPE.INTEGER: int,
    PARAMETER_TYPE.STRING: str,
    PARAMETER_TYPE.TEXT: str,
    PARAMETER_TYPE.FLOAT: float,
}


def _transform_date(value: str) -> datetime.date:
    return datetime.datetime.strptime(value, DATE_FORMAT).date()


def _transform_datetime(value: str) -> datetime.datetime:
    return datetime.datetime.strptime(value, DATETIME_FORMAT)


def _transform_json(value: Union[str, dict]) -> Union[str, dict]:
    if type(value) is str:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    return value


_transform_initial_mapping = {
    PARAMETER_TYPE.DATE: _transform_date,
    PARAMETER_TYPE.DATETIME: _transform_datetime,
    PARAMETER_TYPE.JSON: _transform_json,
}


def _prepare_initial_value(param_type: str, initial: dict) -> Union[dict, None]:
    """Convert the initial value to the appropriate type.
    This function will massage the initial value as needed into the type
    required for the parameter field. Currently, JSON types need to be
    converted from a string into an object, otherwise display issues
    occur in the form.
    """
    if initial:
        if isinstance(initial, str) and initial.startswith("{{"):
            return initial
        elif param_type in _transform_initial_mapping:
            return _transform_initial_mapping[param_type](initial)
        else:
            return initial
    return None


def _generate_parameter_choices(options):
    return [(None, "Select a value"), *[(option, option) for option in options]]


class TaskParameterForm(Form):
    """Form for providing task parameter input.

    Dynamically generates a form based on the provided Function or Workflow. The schema
    for the tasked_object is parsed and the appropriate fields are setup, including
    default values and correct input types to be used for validation.

    Attributes:
        tasked_object: Function or Workflow instance for which to generate the form
        creator: User executing the task
        data: dict of data submitted to the form
        initial: dict of initial values that the form fields should be populated with
        prefix: Prefix to apply to the form field ids. Set this if the default value
                happens to cause conflicts with other fields when using multiple forms.
    """

    allow_templates = False
    template_name = "forms/task_parameters.html"

    def __init__(
        self,
        tasked_object: Union["Function", "Workflow"],
        creator: "User",
        data: dict | None = None,
        initial: dict | None = None,
        prefix: str = "task-parameter",
        **kwargs,
    ):
        # NOTE: initial is intentionally excluded from this call. We handle the initial
        # values separately and passing it through here causes problems with the
        # rendering of json parameter values.
        super().__init__(data=data, prefix=prefix, **kwargs)

        self.tasked_object = tasked_object
        full_prefix = f"{prefix}-" if prefix else ""

        if initial is None:
            initial = {}

        for parameter in tasked_object.parameters.all():
            param_name = parameter.name
            param_type = parameter.parameter_type
            initial_value = initial.get(param_name, None) or parameter.default
            input_value = data.get(f"{full_prefix}{param_name}") if data else None

            field_class, widget, base_type = self.get_field_info(
                param_type, input_value or initial_value, parameter.options
            )

            if not field_class:
                raise ValueError(f"Unknown field type for {param_name}: {param_type}")

            field_kwargs = {
                "label": param_name,
                "label_suffix": param_type,
                "initial": _prepare_initial_value(param_type, initial_value),
                "required": parameter.required,
                "help_text": parameter.description,
            }

            if parameter.options:
                field_kwargs["choices"] = _generate_parameter_choices(parameter.options)
                field_kwargs["coerce"] = _type_mapping.get(param_type, str)

            if param_type == PARAMETER_TYPE.FILE:
                field_kwargs["queryset"] = self._get_file_queryset(
                    tasked_object.environment, creator
                )

            if widget:
                field_kwargs["widget"] = widget

            self.fields[param_name] = field_class(**field_kwargs)
            self.fields[param_name].widget.attrs.update({"base_type": base_type})

    def _get_file_queryset(self, environment: "Environment", creator: "User"):
        """Builds a UserFile queryset limited to the files that the tasking user has
        access to for the environment"""
        return UserFile.objects.filter(environment=environment).filter(
            Q(creator=creator) | Q(public=True)
        )

    def get_field_info(
        self, parameter_type: str, input_value: str | None, options: list | None
    ) -> Tuple[Type[Field], Type[Widget], str]:
        """Gets the appropriate field class and widget for the provided parameter type.
        The input_value is not used in this implementation, but is expected to be
        provided so that alternative implementations of this method can use it to derive
        the field class and widget based on the input data.
        """
        if options:
            field = TypedChoiceField
            widget = None
        else:
            field, widget = _field_mapping.get(parameter_type, (None, None))
        base_type = (
            getattr(widget, "input_type", "text") if widget else field.widget.input_type
        )
        return field, widget, base_type

    def _remove_empty_fields(self, parameters: dict) -> None:
        """Removes any fields that were empty (no value entered in the form) from the
        parameters dict so they can be treated as optional values that weren't provided,
        rather than values that were provided with the Field class's `empty_value`.
        """
        for name in list(parameters.keys()):
            value = parameters[name]

            if value is None or value == "":
                _ = parameters.pop(name)

    def clean(self):
        """Form level validation and data cleanup"""
        cleaned_data = super().clean()
        self._remove_empty_fields(cleaned_data)

        return cleaned_data


class TaskParameterTemplateForm(TaskParameterForm):
    """TaskParameterForm variant with template variable support

    This is a version of TaskParameterForm that allows template variables to be entered
    as values regardless of parameter type. That is, a field requiring an integer will
    allow either and integer value or a template variable such as {{step.result}}.
    Other than the exception for template variables, other validation rules still apply.
    """

    allow_templates = True

    def _stringify_template_variables(self, parameter_template: str) -> str:
        """Converts the template variables in the parameter template to strings so
        that the template can be safely jsonified.
        """
        template_dict = parse_parameter_template(parameter_template)
        for name in list(template_dict.keys()):
            value = template_dict[name]
            if isinstance(value, dict):
                template_dict[name] = re.sub(
                    r'"{{([\w\.]*)}}"', r"{{\1}}", json.dumps(value)
                )

        return template_dict

    def _get_template_value(self, name, value) -> str:
        """Generates the correct template value based on the type of the supplied
        value
        """
        str_types = [
            PARAMETER_TYPE.STRING,
            PARAMETER_TYPE.TEXT,
            PARAMETER_TYPE.DATE,
            PARAMETER_TYPE.DATETIME,
        ]

        parameter_types = {
            type_map[0]: type_map[1]
            for type_map in self.tasked_object.parameters.values_list(
                "name", "parameter_type"
            )
        }

        template_value = value
        json_dump = True

        match value:
            case str():
                if value.startswith("{") and not parameter_types[name] in str_types:
                    json_dump = False
            case datetime.datetime():
                template_value = value.strftime(DATETIME_FORMAT)
            case datetime.date():
                template_value = value.strftime(DATE_FORMAT)

        return json.dumps(template_value) if json_dump else template_value

    def _build_parameter_template(self, parameters: dict) -> str:
        """Construct the parameter template that can be rendered with a django Context
        to form the task parameters.
        """
        template = []

        for name, value in parameters.items():
            template.append(f'"{name}": {self._get_template_value(name, value)}')

        return "{" + ", ".join(template) + "}"

    def __init__(
        self,
        tasked_object: Union["Function", "Workflow"],
        creator: "User",
        data: dict | None = None,
        initial: str | None = None,
        **kwargs,
    ):
        """TaskParameterTemplateForm init

        Args:
            tasked_object: Function or Workflow instance for which to generate the form
            creator: User executing the task
            data: Form submission data
            initial: Initial values to populate the form fields with on render
        """
        initial_data = self._stringify_template_variables(initial) if initial else {}

        super().__init__(
            tasked_object=tasked_object,
            creator=creator,
            data=data,
            initial=initial_data,
            **kwargs,
        )

    def get_field_info(
        self, parameter_type: str, input_value: str | None, options: list | None
    ) -> Tuple[Type[Field], Type[Widget], str]:
        """For fields that are allowed to provide template variables as input, alters
        the widget to be a TextInput. When input_value is provided, if the input is a
        template variable the field class is set to CharField, as validation against the
        original field class is no longer possible.
        """
        field_class, widget, base_type = super().get_field_info(
            parameter_type, input_value, options
        )

        # Files are not allowed here yet due to difficulty in determining
        # where the uploaded file lives at
        if parameter_type in [
            PARAMETER_TYPE.INTEGER,
            PARAMETER_TYPE.FLOAT,
            PARAMETER_TYPE.JSON,
            PARAMETER_TYPE.DATE,
            PARAMETER_TYPE.DATETIME,
            PARAMETER_TYPE.BOOLEAN,
        ]:
            if isinstance(input_value, str) and re.search(r"{{[\w\.]+}}", input_value):
                field_class = CharField
                widget = TextInput

        return field_class, widget, base_type

    @property
    def parameter_template(self):
        """Returns the json-string parameter template for parameters form. This can
        only be access after validation via is_valid().
        """
        assert hasattr(self, "cleaned_data"), (
            "You cannot access parameter_template until cleaned_data is made available"
            "by calling is_valid()."
        )

        return self._build_parameter_template(self.cleaned_data)


class TaskMetadataForm(Form):
    comment = CharField(
        label="",
        widget=Textarea,
        required=False,
    )

    def __init__(
        self,
        prefix: str = "task-metadata",
        *args,
        **kwargs,
    ):
        super().__init__(prefix=prefix, *args, **kwargs)
