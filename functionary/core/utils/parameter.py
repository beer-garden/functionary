import datetime
import json
from copy import deepcopy
from typing import TYPE_CHECKING, List, Type, TypeVar, Union

import jsonschema
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import UUID4, BaseModel, Field, Json, ValidationError, create_model

if TYPE_CHECKING:
    from core.models import Function, FunctionParameter, Workflow


class PARAMETER_TYPE:
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    FILE = "file"
    FLOAT = "float"
    INTEGER = "integer"
    JSON = "json"
    STRING = "string"
    TEXT = "text"


_PARAMETER_TYPE_MAP = {
    PARAMETER_TYPE.BOOLEAN: bool,
    PARAMETER_TYPE.DATE: datetime.date,
    PARAMETER_TYPE.DATETIME: datetime.datetime,
    PARAMETER_TYPE.FILE: UUID4,
    PARAMETER_TYPE.FLOAT: float,
    PARAMETER_TYPE.INTEGER: int,
    PARAMETER_TYPE.JSON: TypeVar("json", Json, str),
    PARAMETER_TYPE.STRING: str,
    PARAMETER_TYPE.TEXT: TypeVar("text", str, bytes),
}

PARAMETER_TYPE_CHOICES = [(_type, _type) for _type in _PARAMETER_TYPE_MAP.keys()]

DATE_FORMAT = r"%Y-%m-%d"
DATETIME_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"


def _get_pydantic_model(instance: Union["Function", "Workflow"]) -> Type[BaseModel]:
    """Get a pydantic model describing the parameters of the provided instance"""
    params_dict = {}

    for parameter in instance.parameters.all():
        field = Field()
        field.alias = parameter.name
        field.title = parameter.name
        field.description = parameter.description

        field.default = ... if parameter.required else parameter.default
        type_ = _PARAMETER_TYPE_MAP[parameter.parameter_type]

        # Append _ to ensure name does not conflict with pydantic BaseModel properties
        params_dict[f"{field.alias}_"] = (type_, field)

    model_name = f"{type(instance).__name__}ParameterModel"

    return create_model(model_name, **params_dict)


def _filter_by_type(parameters: List["FunctionParameter"], type: Type):
    """Filter the provided parameters by the specified type and return as a list"""
    return [p for p in parameters if p.parameter_type == type]


def _serialize_date_parameters(
    task_parameters: dict, function_parameters: List["FunctionParameter"]
) -> None:
    """Serialize date parameters"""
    date_parameters = _filter_by_type(function_parameters, PARAMETER_TYPE.DATE)

    for parameter in date_parameters:
        name = parameter.name
        value = task_parameters[name]

        if type(value) is datetime.date:
            task_parameters[name] = value.strftime(DATE_FORMAT)


def _serialize_datetime_parameters(
    task_parameters: dict, function_parameters: List["FunctionParameter"]
) -> None:
    """Serialize datetime parameters"""
    datetime_parameters = _filter_by_type(function_parameters, PARAMETER_TYPE.DATETIME)

    for parameter in datetime_parameters:
        name = parameter.name
        value = task_parameters[name]

        if type(value) is datetime.datetime:
            task_parameters[name] = value.strftime(DATETIME_FORMAT)


def _serialize_json_parameters(
    task_parameters: dict, function_parameters: List["FunctionParameter"]
) -> None:
    """Serialize json parameters"""
    json_parameters = _filter_by_type(function_parameters, PARAMETER_TYPE.JSON)

    for parameter in json_parameters:
        name = parameter.name
        task_parameters[name] = json.dumps(task_parameters[name])


def _serialize_parameters(
    parameters: dict, instance: Union["Function", "Workflow"]
) -> dict:
    """Serializes json type parameters for use in validation"""
    parameters_copy = deepcopy(parameters)

    # Retrieve all parameters, then filter later, to avoid multiple database lookups
    present_parameters = list(
        instance.parameters.filter(name__in=parameters.keys()).all()
    )

    _serialize_date_parameters(parameters_copy, present_parameters)
    _serialize_datetime_parameters(parameters_copy, present_parameters)
    _serialize_json_parameters(parameters_copy, present_parameters)

    return parameters_copy


def get_schema(instance: Union["Function", "Workflow"]) -> dict:
    """Creates a pydantic model from the parameter definitions and returns the schema
    as a JSON string

    Args:
        instance: A Function or Workflow instance to generate a schema for

    Returns:
        An OpenAPI / JSON Schema compatible schema dictionary
    """
    return _get_pydantic_model(instance).schema()


def validate_parameters(parameters: dict, instance: Union["Function", "Workflow"]):
    """Validate the provided input parameters against the instance's parameter
    definitions

    Args:
        parameters: dict containing the parameters as key / value pairs
        instance: Function or Workflow instance to validate the parameters against

    Raises:
        ValidationError: The parameters are invalid for the provided instance
    """
    try:
        pydantic_model = _get_pydantic_model(instance)
        serialized_parameters = _serialize_parameters(parameters, instance)
        jsonschema.validate(
            serialized_parameters, pydantic_model(**serialized_parameters).schema()
        )
    except (
        ValidationError,
        jsonschema.ValidationError,
        json.JSONDecodeError,
    ) as exc:
        raise DjangoValidationError(exc)
