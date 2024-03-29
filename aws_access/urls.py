"""aws url configuration"""
from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r"^api/v1/aws/accounts/$", views.get_aws_accounts),
    re_path(r"^api/v1/aws/account/groups/$", views.get_aws_groups),
]
