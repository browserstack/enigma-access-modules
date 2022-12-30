from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound
import json
import helpers


@login_required
def get_aws_groups(request, account):
    if not helpers.aws_account_exists(account):
        response = {"error" : "{} does not exist".format(account)}
        return HttpResponseNotFound(json.dumps(response))

    aws_groups_data = helpers.get_aws_groups(account=account)
    data = []
    for group in aws_groups_data:
        data.append(group['GroupName'])
    response = {"data":data}
    return JsonResponse(response)
