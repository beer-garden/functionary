import json
import re

FINISHED_STATUS = ["COMPLETE", "ERROR"]


def parse_parameter_template(parameter_template: str) -> dict:
    """Takes a parameter template string and converts it to a dict."""
    # Add quotes around {{template_variables}}
    json_safe_template = re.sub(
        r'"(\w+)": {{([\w\.]+)}}', r'"\1": "{{\2}}"', parameter_template
    )

    # Now strip the quotes from nested json so that it remains a single json string
    # For example:
    #   '{"nested": {{parameters.json_param}}}'
    # rather than:
    #   '{"nested": "{{paramters.json_param}}"}'
    return json.loads(json_safe_template)
