from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from . import helpers


def get_gcp_domains(request):
    response = {"data": helpers.get_gcp_domains()}
    return JsonResponse(response)


@login_required
def get_gcp_groups(request):
    data = request.GET
    if not data.get("gcp_domain") and not helpers.get_gcp_domain_details(
        data["gcp_domain"]
    ):
        return JsonResponse({"error": "Valid domain is required for GCP Access."})
    page_token = ""
    if data.get("page_token"):
        page_token = data.get("page_token")
    groups, page_token = helpers.get_gcp_groups(data["gcp_domain"], page_token)
    if groups is False:
        return JsonResponse(
            {"error": "Something went wrong while fetching GCP groups."}
        )
    response = {"gcp_groups": groups, "page_token": page_token}

    return JsonResponse(response)
