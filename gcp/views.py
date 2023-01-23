from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from . import helpers


def get_gcp_domains(request):
    response = {"data": helpers.get_gcp_domains()}
    return JsonResponse(response)


@login_required
def get_gcp_groups(request):
    data = request.GET
    if not helpers.get_gcp_domain_details(data["gcp_domain"]):
        return JsonResponse({"error": "Valid domain is required for GCP Access."})

    groups = helpers.get_gcp_groups(data["gcp_domain"])
    group_names = []
    for group in groups:
        group_names.append({"group_name": group["name"], "group_email": group["email"]})

    response = {"gcp_groups": group_names}

    return JsonResponse(response)
