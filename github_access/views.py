"""github module views"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from . import helpers
from Access.paginator_decorators import paginator

@login_required
@paginator
def get_github_repos(request):
    try:
        data = request.GET
        search = (data["search"] if data.get("search") else "")

        all_repos = helpers.get_org_repo_list()
        selected_repos = []

        for repo in all_repos:
            repo_id = repo["orgName"] + "/" + repo["repoName"]
            if search.lower() in repo_id.lower():
                selected_repos.append(repo)

        response = {"githubRepoList": selected_repos, "rowList": "githubRepoList"}

        if not selected_repos:
            response["githubRepoList"] = all_repos
            response["search_error"] = ("Please try adjusting your search",
                                        "to find what you're looking for.")

        return response
    except Exception:
        return JsonResponse({"error": "Failed to Fetch Github repos"}, status=500)
