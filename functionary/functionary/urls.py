"""functionary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from importlib import resources

from django.apps import apps
from django.templatetags.static import static
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.authtoken.views import obtain_auth_token

from ui.views.login import LoginView

urlpatterns = [
    path("", include("ui.urls")),
    path("api/v1/", include("core.api.v1.urls")),
    path("api/v1/", include("builder.api.v1.urls")),
    path("api/v1/api-token-auth", obtain_auth_token),
    path("admin/", include("ui.admin.urls")),
    # allauth.urls includes its own account_login endpoint, but defining this one
    # first gives it precedence, since the first match wins when routing.
    path("accounts/login/", LoginView.as_view(), name="account_login"),
    path("accounts/", include("allauth.urls")),
]

# Use the generated schema if it exists
schema_kwargs = {}
if resources.files("core").joinpath("static", "functionary.yaml").is_file():
    schema_kwargs["url"] = static("functionary.yaml")
else:
    schema_kwargs["url_name"] = "schema"

urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(**schema_kwargs),
        name="swagger",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(**schema_kwargs),
        name="redoc",
    ),
]

# Add URLs for debug plugins if they are installed
if apps.is_installed("debug_toolbar"):
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
