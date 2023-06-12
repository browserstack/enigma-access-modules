"""opsgenie url configuration"""
from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r"^api/v1/opsgenie/teams/$", views.get_opsgenie_team)
]
