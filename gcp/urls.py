from django.urls import path

from .views import get_gcp_groups

urlpatterns = [
    path("api/v1/gcp/domain/groups", get_gcp_groups, name="getGCPGroups"),
]
