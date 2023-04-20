import os

from django.contrib import messages

LOGIN_URL = "account_login"
LOGOUT_URL = "account_logout"
LOGIN_REDIRECT_URL = "ui:home"
LOGOUT_REDIRECT_URL = "account_login"
MESSAGE_TAGS = {
    messages.DEBUG: "text-info-emphasis bg-info-subtle border-info",
    messages.INFO: "text-info-emphasis bg-info-subtle border-info",
    messages.SUCCESS: "text-success-emphasis bg-success-subtle border-success",
    messages.WARNING: "text-warning-emphasis bg-warning-subtle border-warning",
    messages.ERROR: "text-danger-emphasis bg-danger-subtle border-danger",
}
FILTERS_EMPTY_CHOICE_LABEL = "All"
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
DOCUMENTATION_LINK = os.environ.get("DOCUMENTATION_LINK", "/static/docs/index.html")
