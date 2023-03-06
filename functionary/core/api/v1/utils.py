import json
import re
from collections import OrderedDict
from typing import Union

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.models import Function, Workflow
from core.utils.parameter import PARAMETER_TYPE

PREFIX = "param"
SEPARATOR = r"\."

param_name_format = re.compile(rf"^({PREFIX}){SEPARATOR}(\w+)$")


def parse_parameters(values: OrderedDict) -> None:
    """Mutate given values to move all `param.` arguments in parameters field"""
    _update_parameter_field_type(values)

    # Avoid dictionary changed size error by wrapping items in list
    for param, _ in list(values.items()):
        if not (valid_param_name := get_parameter_name(param)):
            continue

        value = values.pop(param)
        if type(value) == InMemoryUploadedFile:
            value = value.name

        values["parameters"][valid_param_name] = value


def cast_parameters(values: OrderedDict) -> None:
    """Parent method to cast parameters to necessary types"""
    _cast_json_parameters(values)


def get_parameter_name(parameter: str) -> Union[str, None]:
    """Return parameter name if parameter format is valid"""
    if not (param_name := param_name_format.match(parameter)):
        return None
    return param_name.group(2)


def _cast_json_parameters(values: OrderedDict) -> None:
    """Mutates all JSON parameter fields into python objects

    Args:
        values: An OrderedDict containing the values passed to the serializer

    Returns:
        None

    Raises:
        ValidationError: When a JSON parameter is not valid JSON
    """
    tasked_object: Union[Function, Workflow] = values["tasked_object"]
    json_params = tasked_object.parameters.filter(parameter_type=PARAMETER_TYPE.JSON)

    for json_param in json_params:
        try:
            if not values["parameters"].get(json_param.name):
                continue

            if type(values["parameters"][json_param.name]) == dict:
                continue

            values["parameters"][json_param.name] = json.loads(
                values["parameters"][json_param.name]
            )
        except json.decoder.JSONDecodeError as err:
            exception_map = {json_param.name: err.msg}
            exc = ValidationError(exception_map)
            raise serializers.ValidationError(serializers.as_serializer_error(exc))


def _update_parameter_field_type(values: OrderedDict) -> None:
    """Mutates the `parameters` field to a dictionary"""
    if not values.get("parameters"):
        values["parameters"] = {}
    elif type(values.get("parameters")) == str:
        values["parameters"] = json.loads(values["parameters"])
