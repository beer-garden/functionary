import re
from typing import Union

PREFIX = "param"
SEPARATOR = r"\."

param_name_format = re.compile(rf"^({PREFIX}){SEPARATOR}(\w+)$")


def get_parameter_name(parameter: str) -> Union[str, None]:
    """Return parameter name if parameter format is valid"""
    if not (param_name := param_name_format.match(parameter)):
        return None
    return param_name.group(2)
