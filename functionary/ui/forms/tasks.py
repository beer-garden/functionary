import json
import re
from typing import TYPE_CHECKING, Optional, Tuple, Type, Union

from django.forms import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    Field,
    FileInput,
    FloatField,
    Form,
    IntegerField,
    JSONField,
    Textarea,
    TextInput,
)
from django.forms.widgets import DateInput, DateTimeInput, Widget

from core.utils.parameter import PARAMETER_TYPE

if TYPE_CHECKING:
    from django.http import QueryDict

    from core.models import Function, Workflow


class HTMLDateInput(DateInput):
    input_type = "date"


class HTMLDateTimeInput(DateTimeInput):
    input_type = "datetime-local"


_field_mapping = {
    PARAMETER_TYPE.INTEGER: (IntegerField, None),
    PARAMETER_TYPE.STRING: (CharField, None),
    PARAMETER_TYPE.TEXT: (CharField, Textarea(attrs={"rows": "2", "cols": "40"})),
    PARAMETER_TYPE.FLOAT: (FloatField, None),
    PARAMETER_TYPE.FILE: (CharField, FileInput),
    PARAMETER_TYPE.BOOLEAN: (BooleanField, None),
    PARAMETER_TYPE.DATE: (DateField, HTMLDateInput),
    PARAMETER_TYPE.DATETIME: (
        DateTimeField,
        HTMLDateTimeInput,
    ),
    PARAMETER_TYPE.JSON: (JSONField, Textarea(attrs={"rows": "2", "cols": "40"})),
}


def _transform_json(value: Union[str, dict]) -> Union[str, dict]:
    if type(value) is str:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    return value


_transform_initial_mapping = {PARAMETER_TYPE.JSON: _transform_json}


def _prepare_initial_value(param_type: str, initial: dict) -> Union[dict, None]:
    """Convert the initial value to the appropriate type.
    This function will massage the initial value as needed into the type
    required for the parameter field. Currently, JSON types need to be
    converted from a string into an object, otherwise display issues
    occur in the form.
    """
    if initial:
        if param_type in _transform_initial_mapping:
            return _transform_initial_mapping[param_type](initial)
        else:
            return initial
    return None


class TaskParameterForm(Form):
    """Form for providing task parameter input.

    Dynamically generates a form based on the provided Function. The schema for the
    Function is parsed and the appropriate fields are setup, including default values
    and correct input types to be used for validation.

    Attributes:
        tasked_object: Function instance for which to generate the form
        data: dict of data submitted to the form
        initial: dict of initial values that the form fields should be populated with
        prefix: Prefix to apply to the form field ids. Set this if the default value
                happens to cause conflicts with other fields when using multiple forms.
    """

    template_name = "forms/task_parameters.html"

    def __init__(
        self,
        tasked_object: Union["Function", "Workflow"],
        data: dict | None = None,
        initial: dict | None = None,
        prefix: str = "task-parameter",
        **kwargs,
    ):
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

            field_class, widget = self.get_field_info(
                param_type, input_value or initial_value
            )

            if not field_class:
                raise ValueError(f"Unknown field type for {param_name}: {param_type}")

            kwargs = {
                "label": param_name,
                "label_suffix": param_type,
                "initial": _prepare_initial_value(param_type, initial_value),
                "required": parameter.required,
                "help_text": parameter.description,
            }

            if widget:
                kwargs["widget"] = widget

            field = field_class(**kwargs)

            # Style input fields
            # TODO: select should be form-select-input
            if param_type != PARAMETER_TYPE.BOOLEAN:
                field.widget.attrs.update(
                    {
                        "class": "form-control",
                        "aria-describedby": f"{param_name}HelpBlock",
                    }
                )
            else:
                field.widget.attrs.update(
                    {
                        "class": "form-check-input",
                        "aria-describedby": f"{param_name}HelpBlock",
                    }
                )

            self.fields[param_name] = field

    def get_field_info(
        self, parameter_type: str, input_value: str | None
    ) -> Tuple[Type[Field], Type[Widget]]:
        """Gets the appropriate field class and widget for the provided parameter type.
        The input_value is not used in this implementation, but is expected to be
        provided so that alternative implementations of this method can use it to derive
        the field class and widget based on the input data.
        """
        return _field_mapping.get(parameter_type, (None, None))

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

    def _stringify_template_variables(self, parameter_template: str) -> str:
        """Converts the template variables in the parameter template to strings so
        that the template can be safely jsonified.
        """
        # Add quotes around {{template_variables}}
        json_safe_template = re.sub(
            r'"(\w+)": {{([\w\.]+)}}', r'"\1": "{{\2}}"', parameter_template
        )

        # Now strip the quotes from nested json so that it remains a single json string
        # For example:
        #   '{"nested": {{parameters.json_param}}}'
        # rather than:
        #   '{"nested": "{{paramters.json_param}}"}'
        template_dict = json.loads(json_safe_template)
        for name in list(template_dict.keys()):
            value = template_dict[name]
            if isinstance(value, dict):
                template_dict[name] = re.sub(
                    r'"{{([\w\.]*)}}"', r"{{\1}}", json.dumps(value)
                )

        return template_dict

    def _build_parameter_template(self, parameters: dict) -> str:
        """Construct the parameter template that can be rendered with a django Context
        to form the task parameters.
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

        template = []

        for name, value in parameters.items():
            template_value = (
                value
                if (
                    isinstance(value, str)
                    and value.startswith("{")
                    and not parameter_types[name] in str_types
                )
                else json.dumps(value)
            )

            template.append(f'"{name}": {template_value}')

        return "{" + ", ".join(template) + "}"

    def __init__(
        self,
        tasked_object: Union["Function", "Workflow"],
        data: Optional["QueryDict"] = None,
        initial: Optional[str] = None,
        **kwargs,
    ):
        """TaskParameterTemplateForm init

        Args:
            function: The Function that will be executed when the WorkflowStep runs
            data: Form submission data
            initial: Initial values to populate the form fields with on render
        """
        initial_data = self._stringify_template_variables(initial) if initial else {}

        super().__init__(
            tasked_object=tasked_object, data=data, initial=initial_data, **kwargs
        )

    def get_field_info(
        self, parameter_type: str, input_value: str | None
    ) -> Tuple[Type[Field], Type[Widget]]:
        """For fields that are allowed to provide template variables as input, alters
        the widget to be a TextInput. When input_value is provided, if the input is a
        template variable the field class is set to CharField, as validation against the
        original field class is no longer possible.
        """
        field_class, widget = super().get_field_info(parameter_type, input_value)

        if parameter_type in [
            PARAMETER_TYPE.INTEGER,
            PARAMETER_TYPE.FLOAT,
            PARAMETER_TYPE.JSON,
        ]:
            widget = TextInput

            if isinstance(input_value, str) and re.search(r"{{[\w\.]+}}", input_value):
                field_class = CharField

        return field_class, widget

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
