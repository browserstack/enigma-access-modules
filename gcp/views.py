from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from Access.paginator_decorators import paginator
from . import helpers
from . import access


@login_required
@paginator
def get_gcp_groups(request):
    try:
        data = request.GET
        if not data.get("gcp_domain") and not helpers.get_gcp_domain_details(
            data.get("gcp_domain")
        ):
            return JsonResponse({
                "error": "Valid domain is required for GCP Access."
            }, status=400)
        gcp_domain = data["gcp_domain"]
        search = (data["search"] if data.get("search") else "")
        gcp_groups_data = access.GCPAccess.get_domain_groups(gcp_domain)

        groups = []
        all_groups = []
        for gcp_group in gcp_groups_data:
            if search.lower() in gcp_group["name"].lower():
                groups.append(gcp_group["name"])
            all_groups.append(gcp_group["name"])
        
        response = {
            "gcp_groups": groups if groups else all_groups,
            "rowList": "gcp_groups",
        }

        if not groups:
            response["search_error"] = ("Please try adjusting your search criteria or"
            " browse by filters to find what you're looking for.")
        return response
    except Exception:
        return JsonResponse({
            "error": "Something went wrong while fetching GCP groups."
        }, status=500)

    
