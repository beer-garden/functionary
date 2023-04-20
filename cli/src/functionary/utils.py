import datetime

import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .client import get


def flatten(results, object_fields):
    """Flattens any nested objects in results.

    The keys from each dict in results is checked for a replacement
    in object_fields. If found in object_fields, the original value
    will be replaced by new entries for each mapping specified.

    Args:
        results: List of dict objects to process
        object_fields: mapping of keys from a nested object in each
            result item that should be in used instead of the object.
            For example:
                object_fields={
                    "package": [("name", "package")],
                    "user": [("first_name", "first"), ("last_name", "last")],
                }
            will return:
                [ ...,
                  "package": <package.name>,
                  "first": <user.first_name>,
                  "last": <user.last_name>,
                  ...
                ]

    Returns:
        The input list with the replacements from object_fields included
    """
    new_results = []

    for item in results:
        new_item = {}
        for key, value in item.items():
            if key in object_fields:
                replacements = object_fields[key]
                for nested_key, label in replacements:
                    new_item[label] = value[nested_key] if value else None
            else:
                new_item[key] = value
        new_results.append(new_item)

    return new_results


def _fix_datetime_display(value):
    """
    Helper function for format_results to remove milliseconds from datetime

    Args:
        value: string representing datetime value
    Returns:
        value as a string representing datetime value without milliseconds
    """
    value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
    return value.strftime("%Y-%m-%d %H:%M:%S%Z")


def format_results(results, title="", excluded_fields=[]):
    """
    Helper function to organize table results using Rich

    Args:
        results: Results to format as a List
        title: Optional table title as a String
        excluded_fields: Optional list of keys to filter out

    Returns:
        None
    """
    table = Table(title=title, show_lines=True, title_justify="left")
    console = Console()
    first_row = True

    for item in results:
        row_data = []
        for key, value in item.items():
            if key in excluded_fields:
                continue
            if first_row:
                table.add_column(key.capitalize())
            if key.endswith("_at"):
                value = _fix_datetime_display(value)
            row_data.append(str(value) if value else None)
        table.add_row(*row_data)
        first_row = False
    console.print(table)


def _get_package_functions(path):
    """Returns list of dictionary of functions in the package.yaml"""
    with open(path, "r") as package_yaml:
        package_definition = yaml.safe_load(package_yaml)
    return package_definition["package"]


def _get_functions_for_package(package_name):
    """
    Takes in package_name, returns functions associated with package
    """
    packages = get("packages")
    functions = get("functions")
    if not packages or not functions:
        return {}
    package_id = _get_package_id(packages, package_name)
    if package_id is None:
        return {}
    package_functions = sort_functions_by_package(functions)
    return package_functions[package_id]


def _get_package_id(packages, package_name):
    """
    Takes in packages, desired package_name, returns associated package id
    """
    for package in packages:
        if package["name"] == package_name:
            return package["id"]


def sort_functions_by_package(functions):
    """
    Sorts functions by their package id
    """
    functions_lookup = {}
    for function in functions:
        package_id = function["package"]
        if package_id in functions_lookup:
            functions_lookup[package_id].append(function)
        else:
            functions_lookup[package_id] = [function]
    return functions_lookup


def check_changes(path):
    """
    Checks for discrepancies between the package.yaml and the API functions, returns
    whether or not changes occurred
    """
    packagefunctions = _get_package_functions(path)["functions"]
    apifunctions = _get_functions_for_package(_get_package_functions(path)["name"])

    if not apifunctions:
        newfunctions = packagefunctions
        removedfunctions = {}
        updatedfunctions = {}
    else:
        newfunctions = new_functions(packagefunctions, apifunctions)
        removedfunctions = removed_element(packagefunctions, apifunctions)
        updatedfunctions = updated_functions(packagefunctions, apifunctions)

    if newfunctions:
        bullet_list(newfunctions, "New functions")
    if removedfunctions:
        bullet_list(removedfunctions, "Removed Functions")
    if updatedfunctions:
        _format_updated_functions(updatedfunctions, "Updated Functions")

    return bool(newfunctions or removedfunctions or updatedfunctions)


def new_functions(packagefunctions, apifunctions):
    """
    Compares package functions to api functions will return list of new functions
    """
    newfunctions = packagefunctions.copy()
    for packagefunction in packagefunctions:
        for apifunction in apifunctions:
            if packagefunction.get("name") == apifunction.get("name"):
                newfunctions.remove(packagefunction)
                break
    return newfunctions


def removed_element(elementremovedlist, fulllist):
    """
    Takes in 2 lists of dictionaries
    Returns list of dictionaries in the fulllist that are not in elementremovedlist
    """
    items = fulllist.copy()
    for item in fulllist:
        for element in elementremovedlist:
            if item.get("name") == element.get("name"):
                items.remove(item)
                break
    return items


def updated_functions(packagefunctions, apifunctions):
    """
    Compares package functions to api functions will return dictionary of updated
    function names and the changed fields
    """
    updatedfunctions = {}
    skip_fields = {"variables"}
    for packagefunction in packagefunctions:
        changedfield = []
        for apifunction in apifunctions:
            if packagefunction.get("name") == apifunction.get("name"):
                for key in packagefunction.keys():
                    if key in skip_fields:
                        continue
                    if key == "parameters":
                        if _updated_parameters(packagefunction[key], apifunction[key]):
                            changedfield.append(key)
                        continue
                    if packagefunction[key] != apifunction[key]:
                        changedfield.append(key)
        if changedfield:
            updatedfunctions[packagefunction.get("name")] = changedfield

    return updatedfunctions


def _updated_parameters(packagefunctionparameters, apifunctionparameters):
    """
    Compares the parameters for each function in the package to the parameters
    in api's functions. Returns True if there are changes, false if not
    """
    skip_fields = {"display_name"}
    if removed_element(packagefunctionparameters, apifunctionparameters):
        return True
    if packagefunctionparameters and apifunctionparameters:
        for packagefunctionparameter in packagefunctionparameters:
            newparameter = True
            for apifunctionparameter in apifunctionparameters:
                if packagefunctionparameter.get("name") == apifunctionparameter.get(
                    "name"
                ):
                    newparameter = False
                    for paramkey in packagefunctionparameter:
                        apiparamvalue = apifunctionparameter.get(paramkey)
                        packageparamvalue = packagefunctionparameter.get(paramkey)
                        if paramkey in skip_fields:
                            continue
                        if paramkey == "default":
                            packageparamvalue = str(packageparamvalue)
                        if packageparamvalue != apiparamvalue:
                            return True
                    break
            if newparameter:
                return True

    return False


def bullet_list(list, title):
    """
    Prints to console: Title in blue and list in bullet form
    """
    console = Console()
    console.print(Text(f"{title}", style="bold blue"))
    for entry in list:
        print(f"\u2022 {entry.get('name')}")


def _format_updated_functions(results, title=""):
    """
    Print The function name and changed fields in a table
    """
    title = Text(f"{title}", style="bold blue")
    table = Table(title=title, show_lines=True, title_justify="left")
    console = Console()
    table.add_column("Function Name")
    table.add_column("Changed Fields")
    for key in results.keys():
        row_data = ""
        for value in results[key]:
            row_data = row_data + value + "\n"
        table.add_row(key, row_data)
    console.print(table)
