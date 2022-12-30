from django.core.validators import RegexValidator
from django.db import models

PARAMETER_TYPES = [
    ("integer", "integer"),
    ("string", "string"),
    ("text", "text"),
    ("float", "float"),
    ("boolean", "boolean"),
    ("date", "date"),
    ("datetime", "datetime"),
    ("json", "json"),
]

VALID_PARAMETER_NAME = RegexValidator(
    regex=r"^\w+$",
    message=(
        "Invalid parameter name. Only numbers, letters, and underscore are allowed."
    ),
)


class WorkflowParameter(models.Model):
    """Input parameters for Workflows

    Attributes:
        workflow: foreign key to the Workflow the parameter belongs to
        name: parameter name
        description: parameter description
        parameter_type: data type
        default: default value to display for the parameter
        required: whether or note the parameter is required
    """

    workflow = models.ForeignKey(
        to="Workflow", related_name="parameters", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=64, validators=[VALID_PARAMETER_NAME])
    description = models.TextField(blank=True, null=True)
    parameter_type = models.CharField(max_length=64, choices=PARAMETER_TYPES)
    default = models.CharField(max_length=128, blank=True, null=True)
    required = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "name"], name="wp_workflow_name_unique"
            )
        ]
