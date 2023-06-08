from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from . import helpers
from . import access


@login_required
def get_gcp_groups(request):
    data = request.GET
    if not data.get("gcp_domain") and not helpers.get_gcp_domain_details(
        data["gcp_domain"]
    ):
        return JsonResponse({"error": "Valid domain is required for GCP Access."})
    gcp_domain = data["gcp_domain"]
    search = (data["search"] if data.get("search") else "")
    gcp_groups_data = access.GCPAccess.get_domain_groups(gcp_domain)

    groups = []
    all_groups = []
    for gcp_group in gcp_groups_data:
        if search.lower() in gcp_group["name"].lower():
            groups.append(gcp_group["name"])
        all_groups.append(gcp_group["name"])
    
    paginator = Paginator(groups, 10) if groups else Paginator(all_groups, 10)

    page = (int(data.get("page")) if data.get("page") else 1)

    response = {
        "gcp_groups": list(paginator.get_page(page)),
        "next_page": (page + 1 if page < paginator.num_pages else None),
        "prev_page": (page - 1 if page > 1 else None),
    }

    if not groups:
        response["search_error"] = ("Please try adjusting your search criteria or"
        " browse by filters to find what you're looking for.")
    return JsonResponse(response)

    
