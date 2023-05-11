import json
import requests
import logging
from . import constants
from EnigmaAutomation.settings import ACCESS_MODULES

logger = logging.getLogger(__name__)
default_branch = ["master", "main"]


def _get_github_config():
    return ACCESS_MODULES["github_access"]


def _get_github_token():
    return _get_github_config()["GITHUB_TOKEN"]


def _get_github_base_url():
    return _get_github_config()["GITHUB_BASE_URL"]


def _get_github_org():
    return _get_github_config()["GITHUB_ORG"].lower()


def get_user(username):
    if not _get_user(username):
        return False
    return True


def _get_user(username):
    headers = {"Authorization": "token %s" % _get_github_token()}
    GET_USER_URL = "%s/users/%s" % (_get_github_base_url(), username)
    response = requests.get(GET_USER_URL, headers=headers)
    if response.status_code == 200:
        return True
    return False


def get_repo(repo):
    if not _get_repo(repo):
        return False
    return True


def _get_repo(repo):
    headers = {"Authorization": "token %s" % _get_github_token()}
    GET_REPO_URL = "%s/repos/%s" % (_get_github_base_url(), repo)
    response = requests.get(GET_REPO_URL, headers=headers)
    if response.status_code == 200:
        return True
    return False


def get_org(username):
    if not _get_org(username):
        return False
    return True


def _get_org(username):
    headers = {"Authorization": "token %s" % _get_github_token()}
    GET_ORG_URL = "%s/orgs/%s/members/%s" % (_get_github_base_url(), _get_github_org(), username)
    response = str(requests.get(GET_ORG_URL, headers=headers))
    if "204" not in response:
        return False
    else:
        return True


def get_org_invite(username):
    if not _get_org_invite(username):
        return False
    return True


def _get_org_invite(username):
    headers = {"Authorization": "token %s" % _get_github_token()}
    GET_ORG_INVITE_URL = "%s/orgs/%s/invitations" % (_get_github_base_url(), _get_github_org())
    response = requests.get(GET_ORG_INVITE_URL, headers=headers).json()
    return username in [member["login"] for member in response]


def put_user(username):
    if not _put_user(username):
        return False
    return True


def _put_user(username):
    headers = {"Authorization": "token %s" % _get_github_token()}
    PUT_USER_URL = "%s/orgs/%s/memberships/%s" % (_get_github_base_url(), _get_github_org(), username)
    response = str(requests.put(PUT_USER_URL, headers=headers))
    if "200" not in response:
        return False
    else:
        return True


def _get_branch_protection_enabled(repo, branch):
    headers = {
        "Authorization": "token %s" % _get_github_token(),
        "Accept": "application/vnd.github.v3+json",
    }
    GET_BRANCH_PTOTECTION_URL = "%s/repos/%s/branches/%s/protection" % (
        _get_github_base_url(),
        repo,
        branch,
    )
    response = requests.get(GET_BRANCH_PTOTECTION_URL, headers=headers)
    protected_branch_data = response.json()
    if (
        "restrictions" in protected_branch_data
        and "required_pull_request_reviews" in protected_branch_data
    ):
        return True
    return False


def grant_access(repo, access_level, username):
    response = ""
    try:
        headers = {"Authorization": "token %s" % _get_github_token()}
        repo = repo.strip()
        if not get_repo(repo):
            logger.debug(
                "Skipping git access for %s for user %s because repo does not exist"
                " anymore" % (repo, username)
            )
            return True
        if access_level == "merge":
            headers = {
                "Authorization": "token %s" % _get_github_token(),
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }
            for branch in default_branch:
                response = ""
                GET_USERS_ACCESS_URL = (
                    "%s/repos/%s/branches/%s/protection/restrictions/users"
                    % (_get_github_base_url(), repo, branch)
                )
                res = requests.get(GET_USERS_ACCESS_URL, headers=headers)
                protected_branch_data = res.json()
                is_protected = _is_protection_enabled(
                    repo, branch, protected_branch_data, username, response
                )
                if "Response [200]" in is_protected:
                    logger.debug(response)
                    return True
        else:
            payload = {"permission": access_level}
            PUT_COLLABORATOR_URL = "%s/repos/%s/collaborators/%s" % (
                _get_github_base_url(),
                repo,
                username,
            )
            res = requests.put(
                PUT_COLLABORATOR_URL, headers=headers, data=json.dumps(payload)
            )
            response += str(res)
            response += "\n"
            logger.debug(response)

        if "404" in response:
            return False
        return True
    except Exception as e:
        logger.error("Error while granting repo access to user " + username)
        logger.exception(str(e))
        return False


def _is_protection_enabled(repo, branch, protected_branch_data, username, response):
    if _get_branch_protection_enabled(repo, branch):
        data = [username]
        headers = {
            "Authorization": "token %s" % _get_github_token(),
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        POST_USERS_ACCESS_URL = (
            "%s/repos/%s/branches/%s/protection/restrictions/users"
            % (_get_github_base_url(), repo, branch)
        )
        res = requests.post(
            POST_USERS_ACCESS_URL, headers=headers, data=json.dumps(data)
        )
        response = res.json()
    elif (
        "message" in protected_branch_data
        and protected_branch_data["message"] == "Push restrictions not enabled"
    ):
        response += (
            f"404 - Push Restriction is not enabled for {repo} Repo.             Please"
            " contact Github Admin to enable branch protection for this repo"
        )

    return response


def get_org_repo_list():
    repoList = []
    headers = {
        "Authorization": "token %s" % _get_github_token(),
        "Accept": "application/vnd.github.v3+json",
    }
    GET_ORG_REPOS_URL = "%s/orgs/%s/repos" % (_get_github_base_url(), _get_github_org())
    response = requests.get(GET_ORG_REPOS_URL, headers=headers)
    if response.status_code == 200:
        user_orgs_data = response.json()
        for orgs in user_orgs_data:
            if "full_name" in orgs:
                repoList.append(orgs["full_name"])
        logger.debug("Collected All Repos")
        return repoList
    return []


def revoke_access(username, repo=None):
    return _revoke_github_user(username, repo)


def _revoke_github_user(username, repo):
    headers = {"Authorization": "token %s" % _get_github_token()}
    DELETE_ACCESS_URL = ""
    if repo is None:
        DELETE_ACCESS_URL = "%s/orgs/%s/memberships/%s" % (
            _get_github_base_url(),
            _get_github_org(),
            username,
        )
    else:
        DELETE_ACCESS_URL = "%s/repos/%s/%s/collaborators/%s" % (
            _get_github_base_url(),
            _get_github_org(),
            repo,
            username,
        )

    response = requests.delete(DELETE_ACCESS_URL, headers=headers)
    if response.status_code not in [200, 404, 204]:
        return False
    else:
        return True


def is_email_valid(username, email):
    headers = {"Authorization": "token %s" % _get_github_token()}
    GET_USER_URL = "%s/users/%s" % (_get_github_base_url(), username)
    response = requests.get(GET_USER_URL, headers=headers)
    if response.status_code == 200:
        if "email" in response.json():
            user_email = str(json.loads(response.text)["email"])
            if user_email is not None and user_email == email:
                return True
            else:
                logger.error(constants.GET_USER_BY_EMAIL_FAILED)
                return False
    return False
