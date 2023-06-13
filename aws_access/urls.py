"""aws url configuration"""
from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/aws/account/groups/", views.get_aws_groups),
]
