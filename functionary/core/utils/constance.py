from constance.admin import get_values


class SettingsBox:
    def __init__(self, data: dict):
        self._data = data

    def __getattr__(self, name: str):
        return self._data.get(name)


def get_config(keys: list[str]) -> SettingsBox:
    """This function will query constance and return the values matching the given keys.

    Args:
        keys: List of names of keys to return

    Returns:
        A wrapped dict allowing for settings access via property. A missing key will
        raise a KeyError.
    """
    # The import for get_values may need to change to constance.utils in v3.0
    all_values = get_values()
    config = SettingsBox({key: all_values[key] for key in keys})

    return config
