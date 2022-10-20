import csv
import io
import json
import logging

from django.template import Library, Node, Variable
from django.template.loader import get_template

logger = logging.getLogger(__name__)

register = Library()


def _format_json(result, result_type):
    """Convert a result of the given result_type to JSON.

    This function will take in an arbitrary result object and attempt
    to convert it to a JSON string."""
    obj_to_json = result if not isinstance(result, str) else json.loads(result)
    return json.dumps(obj_to_json)


def _format_table(result, result_type):
    """Convert a result of the given result_type to a table.

    This will take in a "string" or "json" result and return
    the headers and a list of rows for the data. A result_type of
    string is assumed to be csv formatted data - a csv reader
    parses the data into the resulting header and data.

    A result type of json can be one of the following formats:
    [
        {"prop1":"value1", "prop2":"value2"},
        {"prop1":"value3", "prop2":"value4"}
    ]
    or
    {   "foos" : [
            {"prop1":"value1", "prop2":"value2"},
            {"prop1":"value3", "prop2":"value4"}
        ]
    }
    In the second format, the key "foos" will be ignored and the
    value of that key(the list) will be used for the table data. The
    headers are derived from the keys of the first entry in the list.
    """
    if result_type == "string":
        data = io.StringIO(result)
        csv_data = csv.reader(data)
        result = {"headers": next(csv_data), "data": [row for row in csv_data]}
    elif result_type == "json":
        json_data = result
        if isinstance(result, str):
            json_data = json.loads(result)

        if len(json_data) > 0:
            data = []
            if isinstance(json_data, list):
                data = json_data
            elif isinstance(json_data, dict) and len(json_data.values()) == 1:
                values = next(iter((json_data.values())))
                if isinstance(values, list):
                    data = values

            if len(data) > 0:
                headers = data[0].keys()
                res_data = []
                for row in data:
                    r = []
                    for key in headers:
                        r.append(row[key])
                    res_data.append(r)

                result = {"headers": headers, "data": res_data}
            else:
                raise ValueError("Unable to determine the structure of the JSON")
        else:
            raise ValueError("JSON data appears to be empty")
    else:
        raise ValueError(f"Unable to convert {result_type} to csv")
    return result


# Add table first since we can convert some JSON to CSV
format_mapper = {
    "table": _format_table,
    "json": _format_json,
}


class TaskOutputNode(Node):
    def __init__(self, task):
        self.task = Variable(task)

    def render(self, context):
        the_task = self.task.resolve(context)
        if not the_task.result:
            return "<span>No results</span>"

        result = the_task.result
        return_type = the_task.return_type
        output_format = the_task.output_format

        formats_to_try = [output_format] if output_format else format_mapper.keys()

        # If the return type isn't set, do our best guess to
        # generate a useful output
        if not return_type and isinstance(result, str):
            return_type = "string"

        for fmt in formats_to_try:
            try:
                ctx = {
                    "format": fmt,
                    "result": format_mapper[fmt](result, return_type),
                }

                plate = get_template(f"tags/output_{fmt}.html")
                return plate.render(context=ctx)
            except Exception as e:
                logger.debug(
                    "Unable to convert output for %s to %s: %s",
                    the_task.id,
                    fmt,
                    e,
                )

        return f"<pre>{'<br/>'.join(the_task.result.splitlines())}</pre>"


@register.tag("task_output")
def do_task_output(parser, token):
    """Convert the result of the task to the specified format."""
    _, rest = token.contents.split(None, 1)
    return TaskOutputNode(rest)