from django.urls import re_path
import views

urlpatterns = [
    re_path(r"^api/v1/aws/accounts/", views.get_aws_accounts),
    re_path(r"^api/v1/aws/accounts/(?P<account>[\w-]+)/groups/", views.get_aws_groups),
]
