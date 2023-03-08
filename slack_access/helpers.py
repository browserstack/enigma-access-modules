from BrowserStackAutomation.settings import ACCESS_MODULES
from slack_sdk import WebClient
import logging

logger = logging.getLogger(__name__)


# from Access.access_modules.slack_access.helpers import get_info
def get_info(workspace):
    info_list = {}
    team_id, error_message = _get_team_id(workspace)
    if not team_id:
        logger.error(
            f"Could not get information for requested workspace {workspace}. Error ocurred: {error_message}"
        )
        return None, error_message

    channel_id, error_message = _get_channel_id(workspace)
    if not channel_id:
        logger.error(
            f"Could not get channels for requested workspace {workspace}. Error ocurred: {error_message} "
        )
        return None, error_message

    info_list["team_id"] = team_id
    info_list["channel_id"] = channel_id
    return info_list, None


def _get_team_id(workspace):
    client = WebClient(token=ACCESS_MODULES["slack_access"]["AUTH_TOKEN"])

    response = client.admin_teams_list()  # team:read
    print(response)
    if response["ok"]:
        res = [response["id"] for response in response["teams"]]

    if not res:
        return None, response["error"]

    return res, None


def _get_channel_id(workspace):
    client = WebClient(token=ACCESS_MODULES["slack_access"]["AUTH_TOKEN"])
    response = client.admin_conversations_search()  # admin.conversations:read
    if response["ok"]:
        return [
            channel["id"]
            for channel in response["conversations"]
            if (
                channel["name"]
                == ACCESS_MODULES["slack_access"][workspace]["DEFAULT_CHANNEL"]
            )
        ], None

    return None, response["error"]


def invite_user(email, team_id, channel_id, workspace):
    if not _invite_user(email, team_id, channel_id, workspace):
        return False
    return True


def _invite_user(email, team_id, channel_id, workspace):
    try:
        client = WebClient(token=ACCESS_MODULES["slack_access"]["AUTH_TOKEN"])
        response = client.admin_users_invite(
            team_id=team_id, email=email, channel_ids=channel_id
        )  # admin.users:write
        if response["ok"]:
            return True
    except Exception as e:
        print("error-->", e)
    return False


# from Access.access_modules.slack_access.helpers import remove_user
def remove_user(email, workspace):
    user_id, error_message = _get_user_id(email)
    if not user_id:
        logger.error(
            f"Could not remove user from workspace {workspace}. Error ocurred: {error_message}"
        )
        return False, error_message

    team_id, error_message = _get_team_id(workspace)
    print("team-id", team_id)
    print("user-id", user_id)
    if not team_id:
        logger.error(
            f"Could not remove user from workspace {workspace}. Error ocurred: {error_message}"
        )
        return False, error_message
    if not _remove_user(user_id, team_id[0], workspace):
        return (
            False,
            "Error ocurred while removing user from workspace. Please contact Admin",
        )

    return True, None


def _get_user_id(email):
    try:
        client = WebClient(token=ACCESS_MODULES["slack_access"]["AUTH_TOKEN"])
        response = client.users_lookupByEmail(
            email=email
        )  # users:read.email users:read
        if response["ok"]:
            return response["user"]["id"], None
        return None, response["error"]

    except Exception as e:
        return None, e


def is_email_valid(email):
    user_id, error_message = _get_user_id(email)
    if error_message is None:
        print("user-id-->", user_id)
        return True
    return False


def _remove_user(user_id, team_id, workspace):
    try:
        client = WebClient(token=ACCESS_MODULES["slack_access"]["AUTH_TOKEN"])
        response = client.admin_users_remove(
            team_id=team_id, user_id=user_id
        )  # admin.users:write
        if response["ok"]:
            return True
        return False
    except Exception as e:
        print("error-->", e)
        return False


def get_workspace_list():
    workspaceList = []
    client = WebClient(token=ACCESS_MODULES["slack_access"]["AUTH_TOKEN"])
    response = client.admin_teams_list()  # admin.teams:read
    print(response)
    if response["ok"]:
        for teams in response["teams"]:
            if "name" in teams:
                workspaceList.append(teams["name"])
        logger.debug("Collected All Workspaces")
        return workspaceList

    print(response["eror"])
    return []
