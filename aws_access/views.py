"""aws module views"""
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound
from django.core.paginator import Paginator
from . import constants
from . import helpers
from . import access


@login_required
def get_aws_groups(request):
    """returns aws group json response

    Args:
        request (HttpRequest): http request form for aws groups

    Returns:
        JsonResponse: json response with aws groups list
    """
    data = request.GET
    if "AWSAccount" not in data and not helpers.aws_account_exists(data["AWSAccount"]):
        response = {"error": constants.ERROR_MESSAGES["valid_account_required"]}
        return HttpResponseNotFound(json.dumps(response))
    account = data["AWSAccount"]
    search = (data["search"] if data.get("search") else "")
    aws_groups_data = access.AWSAccess.get_account_groups(account)

    groups = []
    all_groups = []
    for aws_group in aws_groups_data:
        if search.lower() in aws_group["GroupName"].lower():
            groups.append(aws_group["GroupName"])
        all_groups.append(aws_group["GroupName"])

    paginator = Paginator(groups, 10) if groups else Paginator(all_groups, 10)

    page = (int(data.get("page")) if data.get("page") else 1)

    response = {
        "AWSGroups": list(paginator.get_page(page)),
        "next_page": (page + 1 if page < paginator.num_pages else None),
        "prev_page": (page - 1 if page > 1 else None),
    }

    if not groups:
        response["search_error"] = ("Please try adjusting your search criteria or"
        " browse by filters to find what you're looking for.")
    return JsonResponse(response)
