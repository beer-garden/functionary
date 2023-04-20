from django.forms import ModelChoiceField
from django_filters import ModelChoiceFilter


class DisplayNameModelChoiceField(ModelChoiceField):
    """ModelChoiceField that uses the instance's display_name value rather than
    __str__ to render the choices."""

    def label_from_instance(self, obj):
        """Returns display_name if present. Otherwise reverts to __str__."""
        return getattr(obj, "display_name", str(obj))


class DisplayNameModelChoiceFilter(ModelChoiceFilter):
    """ModelChoiceFilter that uses the instance's display_name value rather than
    __str__ to render the choices."""

    field_class = DisplayNameModelChoiceField
