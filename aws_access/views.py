"""aws module views"""
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound
from . import constants
from . import helpers


@login_required
def get_aws_accounts(request):
    """returns aws account json response

    Args:
        request (HttpRequest): http request form for aws accounts

    Returns:
        JsonResponse: json response with aws account list
    """
    response = {"data": helpers.get_aws_accounts()}
    return JsonResponse(response)


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
    marker = None
    if data.get(
        "marker"
    ):  # marker to the page to be fetched if AWS response is paginated
        marker = data["marker"]
    aws_groups_data = helpers.get_aws_groups(account=account, marker=marker)
    data = []
    for group in aws_groups_data["Groups"]:
        data.append(group["GroupName"])
    response = {"AWSGroups": data, "marker": None}
    if aws_groups_data.get("IsTruncated"):
        response["marker"] = aws_groups_data["Marker"]
    return JsonResponse(response)
