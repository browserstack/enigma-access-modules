"""opsgenie url configuration"""
from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/opsgenie/teams/", views.get_opsgenie_team)
]
