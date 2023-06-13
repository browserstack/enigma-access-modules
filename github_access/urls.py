"""github url configuration"""
from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/github/repos/", views.get_github_repos)
]
