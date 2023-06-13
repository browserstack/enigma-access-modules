"""opsgenie module views"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound
from django.core.paginator import Paginator
from . import helper
from Access.paginator_decorators import paginator

@login_required
@paginator
def get_opsgenie_team(request):
    """returns opsgenie teams json response

    Args:
        request (HttpRequest): http request form for opsgenie teams

    Returns:
        JsonResponse: json response with opsgenie teams
    """
    try:
        data = request.GET

        all_teams = helper.teams_list()
        search = (data["search"] if data.get("search") else "")

        teams = []
        for team in all_teams:
            if search.lower() in team.lower():
                teams.append(team)

        response = {"teamsList": teams, "rowList": "teamsList"}

        if not teams:
            response["teamsList"] = all_teams
            response["search_error"] = ("Please try adjusting your search",
                                        "to find what you're looking for.")

        return response
    except Exception:
        return JsonResponse({"error": "Failed to Fetch OpsGenie teams"}, status=500)
