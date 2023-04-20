import django_tables2 as tables

from ui.tables.meta import BaseMeta


class TaskOutputTable(tables.Table):
    class Meta(BaseMeta):
        attrs = {"class": "table table-striped text-break"}
