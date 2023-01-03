from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound
import json
from aws_access import constants
from BrowserStackAutomation.settings import data as CONFIG
import helpers


@login_required
def get_aws_accounts(request):
    response = {"data": helpers.get_aws_accounts()}
    return JsonResponse(response)


@login_required
def get_aws_groups(request, account):
    data = request.GET
    if not helpers.aws_account_exists(account):
        response = {"error" : constants.ERROR_MESSAGES["valid_account_required"]}
        return HttpResponseNotFound(json.dumps(response))
    if data.get("marker"):  # marker to the page to be fetched if AWS response is paginated
        marker = data["marker"]
    aws_groups_data = helpers.get_aws_groups(account=account, marker=marker)
    data = []
    for group in aws_groups_data["Groups"]:
        data.append(group['GroupName'])
    response = {"data": data}
    if aws_groups_data.get("IsTruncated"):
        response["marker": aws_groups_data["Marker"]]
    return JsonResponse(response)
