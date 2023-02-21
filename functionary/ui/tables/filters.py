from django.forms.widgets import DateTimeInput
from django_filters import DateTimeFilter as Django_filtersDateTimeFilter


class DateTimeFilter(Django_filtersDateTimeFilter):
    def __init__(self, *args, **kwargs):
        if "widget" not in kwargs:
            kwargs["widget"] = DateTimeInput(attrs={"type": "datetime-local"})
        super().__init__(*args, **kwargs)
