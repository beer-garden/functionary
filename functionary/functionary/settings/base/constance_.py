CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_PREFIX = "constance:functionary:"
CONSTANCE_ADDITIONAL_FIELDS = {
    "config_field": ["django.forms.fields.JSONField", {}],
    "optional_int": [
        "django.forms.fields.IntegerField",
        {"widget": "django.forms.NumberInput", "required": False},
    ],
    "password_field": [
        "django.forms.fields.CharField",
        {
            "widget": "django.forms.PasswordInput",
            "widget_kwargs": {"render_value": True},
            "required": False,
        },
    ],
    "required_password_field": [
        "django.forms.fields.CharField",
        {
            "widget": "django.forms.PasswordInput",
            "widget_kwargs": {"render_value": True},
            "required": True,
        },
    ],
    "required_string": [
        "django.forms.fields.CharField",
        {"widget": "django.forms.TextInput", "required": True},
    ],
    "trusted_header_user_attribute_select": [
        "django.forms.fields.ChoiceField",
        {
            "widget": "django.forms.Select",
            "required": False,
            "choices": (
                ("username", "username"),
                ("distinguished_name", "distinguished_name"),
            ),
        },
    ],
}
CONSTANCE_CONFIG = {
    "RABBITMQ_HOST": ("", "Hostname", "required_string"),
    "RABBITMQ_PORT": (5672, "Port", int),
    "RABBITMQ_MANAGEMENT_PORT": (15672, "Management port", int),
    "RABBITMQ_USER": ("", "Username", str),
    "RABBITMQ_PASSWORD": ("", "Password", "password_field"),
    "RABBITMQ_TLS": (False, "Use TLS for RabbitMQ connection", bool),
    "RABBITMQ_CACERT": ("", "Path to CA cert for verifying RabbitMQ server cert", str),
    "RABBITMQ_CERT": ("", "Path to client certificate", str),
    "RABBITMQ_KEY": ("", "Path to client private key", str),
    "REGISTRY_HOST": ("", "Hostname", "required_string"),
    "REGISTRY_PORT": ("", "Port", "optional_int"),
    "REGISTRY_NAMESPACE": ("", "Namespace / Project", str),
    "REGISTRY_USER": ("", "Username", str),
    "REGISTRY_PASSWORD": ("", "Password", "password_field"),
    "SOCIALACCOUNT_PROVIDERS": (
        {
            "github": {},
            "gitlab": {},
            "keycloak": {},
        },
        "SocialAccount Providers Configuration",
        "config_field",
    ),
    "S3_HOST": ("", "Hostname", "required_string"),
    "S3_PORT": (9000, "Port", int),
    "S3_REGION": ("", "Region", str),
    "S3_BUCKET": ("", "Bucket Name", "required_string"),
    "S3_ACCESS_KEY": ("", "Access Key", "required_string"),
    "S3_SECRET_KEY": ("", "Secret Key", "required_password_field"),
    "S3_SECURE": (False, "Require Secure Access", bool),
    "S3_PRESIGNED_URL_TIMEOUT_MINUTES": (5, "Download URL Timeout (minutes)", int),
    "TRUSTED_HEADER_AUTHENTICATION_ENABLED": (
        False,
        "Trusted Header Authentication Enabled",
        bool,
    ),
    "TRUSTED_HEADER_AUTHENTICATION_HEADER": ("", "Trusted Header", str),
    "TRUSTED_HEADER_AUTHENTICATION_USER_ATTRIBUTE": (
        "username",
        "Trusted Header User Attribute",
        "trusted_header_user_attribute_select",
    ),
    "UI_BANNER_1_BG": ("", "Background Color", str),
    "UI_BANNER_1_FG": ("", "Foreground Color", str),
    "UI_BANNER_1_TEXT": ("", "Text", str),
    "UI_BANNER_2_BG": ("", "Background Color", str),
    "UI_BANNER_2_FG": ("", "Foreground Color", str),
    "UI_BANNER_2_TEXT": ("", "Text", str),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "Authentication": {
        "fields": (
            "TRUSTED_HEADER_AUTHENTICATION_ENABLED",
            "TRUSTED_HEADER_AUTHENTICATION_HEADER",
            "TRUSTED_HEADER_AUTHENTICATION_USER_ATTRIBUTE",
        )
    },
    "Container Registry Settings": {
        "fields": (
            "REGISTRY_HOST",
            "REGISTRY_PORT",
            "REGISTRY_NAMESPACE",
            "REGISTRY_USER",
            "REGISTRY_PASSWORD",
        )
    },
    "RabbitMQ Settings": {
        "fields": (
            "RABBITMQ_HOST",
            "RABBITMQ_PORT",
            "RABBITMQ_MANAGEMENT_PORT",
            "RABBITMQ_USER",
            "RABBITMQ_PASSWORD",
            "RABBITMQ_TLS",
            "RABBITMQ_CACERT",
            "RABBITMQ_CERT",
            "RABBITMQ_KEY",
        )
    },
    "S3 Settings": {
        "fields": (
            "S3_HOST",
            "S3_PORT",
            "S3_REGION",
            "S3_BUCKET",
            "S3_SECURE",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
            "S3_PRESIGNED_URL_TIMEOUT_MINUTES",
        )
    },
    "UI Banner 1": {"fields": ("UI_BANNER_1_TEXT", "UI_BANNER_1_BG", "UI_BANNER_1_FG")},
    "UI Banner 2": {"fields": ("UI_BANNER_2_TEXT", "UI_BANNER_2_BG", "UI_BANNER_2_FG")},
    "HIDDEN": {"fields": ("SOCIALACCOUNT_PROVIDERS",)},
}


def constance_settings_proxy(setting_name, default_value):
    """Custom settings function for django-allauth.

    This function will check Constance for the given setting_name and
    revert to the django.conf.settings if it's not found. This function
    allows the SOCIALACCOUNT_PROVIDERS to be configured outside of these
    config files.

    Args:
        setting_name: The name of the setting to fetch
        default_value: The default to use if it's not configured

    Returns:
        The configured setting from Constance. If it's not found, the setting
        from django.conf.settings, otherwise the default_value.
    """
    import json

    from constance import config
    from django.conf import settings

    value = getattr(config, setting_name, None)
    if value is None:
        return getattr(settings, setting_name, default_value)
    try:
        return json.loads(value)
    except Exception:
        return value
