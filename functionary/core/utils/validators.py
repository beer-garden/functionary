from django.core.exceptions import ValidationError


def list_of_strings(value):
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return

    raise ValidationError(
        '"%(value)s" is not a list of strings', params={"value": value}
    )
