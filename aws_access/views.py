"""aws module views"""
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from Access.paginator_decorators import paginator
from . import constants
from . import helpers
from . import access


@login_required
@paginator
def get_aws_groups(request):
    """returns aws group json response

    Args:
        request (HttpRequest): http request form for aws groups

    Returns:
        JsonResponse: json response with aws groups list
    """
    try:
        data = request.GET
        if not data.get("AWSAccount") and not helpers.aws_account_exists(data.get("AWSAccount")):
            response = {"error": constants.ERROR_MESSAGES["valid_account_required"]}
            return JsonResponse(response, status=400)
        account = data["AWSAccount"]
        search = (data["search"] if data.get("search") else "")
        aws_groups_data = access.AWSAccess.get_account_groups(account)

        groups = []
        all_groups = []
        for aws_group in aws_groups_data:
            if search.lower() in aws_group["GroupName"].lower():
                groups.append(aws_group["GroupName"])
            all_groups.append(aws_group["GroupName"])

        response = {
            "AWSGroups": groups if groups else all_groups,
            "rowList": "AWSGroups"
        }

        if not groups:
            response["search_error"] = ("Please try adjusting your search criteria or"
            " browse by filters to find what you're looking for.")
        return response
    except Exception as e:
        return JsonResponse({
            "error": "Something went wrong while fetching AWS groups."
        }, status=500)
