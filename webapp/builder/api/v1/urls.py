from django.urls import include, path
from rest_framework.routers import DefaultRouter

from builder.api.v1 import views

router = DefaultRouter()
router.register(r"builds", views.BuildViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("publish", views.PublishView.as_view()),
]
