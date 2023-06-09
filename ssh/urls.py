"""ssh url configuration"""
from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/ssh/machines/", views.get_ssh_machines),
]
