from django.urls import re_path

from .views import get_gcp_domains, get_gcp_groups

urlpatterns = [
    re_path(r"^api/v1/gcp/domains$", get_gcp_domains),
    re_path(r"^api/v1/gcp/domain/groups", get_gcp_groups),
]
