import json
import logging

from EnigmaAutomation.settings import ACCESS_MODULES
from slack_sdk import WebClient

logger = logging.getLogger(__name__)


def _get_slack_config():
    return ACCESS_MODULES["slack_access"]


def _get_slack_auth_token(workspace_name):
    return _get_slack_config()[workspace_name]["AUTH_TOKEN"]


def _get_slack_default_channels(workspace_name):
    return _get_slack_config()[workspace_name]["DEFAULT_CHANNELS"]


def _get_slack_client(workspace_name):
    return WebClient(token=_get_slack_auth_token(workspace_name))


def _get_team_id(workspace_name):
    try:
        client = _get_slack_client(workspace_name)
        response = client.admin_teams_list()  # team:read
        res = None
        if response["ok"]:
            for response in response["teams"]:
                if response["name"] == workspace_name:
                    res = response["id"]
            return res, None
        else:
            return None, response["error"]
    except Exception as e:
        logger.error(
            "Could not get team-id for workspace %s. Error ocurred: %s",
            workspace_name, str(e)
        )
        return None, "Could not get team id"


def _get_channel_ids(workspace_name):
    try:
        client = _get_slack_client(workspace_name)
        response = client.admin_conversations_search()  # admin.conversations:read
        if response["ok"]:
            channel_ids = []
            for channel in response["conversations"]:
                if (
                    channel["name"]
                    in _get_slack_default_channels(workspace_name)
                ):
                    channel_ids.append(channel["id"])
            return channel_ids, None

        return None, response["error"]

    except Exception as e:
        logger.exception(
            f"Could not get channel id from workspace {workspace_name}. Error ocurred: {str(e)}"
        )
        return None, "Could not get channel id"


def invite_user(email, team_id, workspace_name):
    channel_ids, error = _get_channel_ids(workspace_name)
    if error is not None:
        logger.exception(
            "Could not get channels for requested workspace {}. Error ocurred: {}".format(
                workspace_name, error
            )
        )
        return False
    try:
        client = _get_slack_client(workspace_name)
        response = client.admin_users_invite(
            team_id=team_id, email=email, channel_ids=channel_ids
        )  # admin.users:write

        if response["ok"]:
            return True
        return False
    except Exception as e:
        logger.exception(
            "Could not invite user from workspace {}. Error ocurred: {}".format(
                workspace_name, str(e)
            )
        )
        return False


# from Access.access_modules.slack_access.helpers import remove_user
def remove_user(email, workspace_name, team_id):
    user_id, error_message = _get_user_id(email, workspace_name)
    if not user_id:
        logger.error(
            f"Could not remove user from workspace {workspace_name}. Error ocurred: {error_message}"
        )
        return False, error_message
    remove_user_resp = _remove_user(user_id, team_id, workspace_name)
    if not remove_user_resp:
        return (
            False,
            "Error ocurred while removing user from {} workspace. Please contact Admin".format(
                workspace_name
            ),
        )

    return True, None


def _get_user_id(email, workspace_name):
    try:
        client = _get_slack_client(workspace_name)
        response = client.users_lookupByEmail(
            email=email
        )  # users:read.email users:read
        if response["ok"]:
            return response["user"]["id"], None
        return None, response["error"]

    except Exception as e:
        logger.exception(
            "Could not get user_id from workspace {}. Error ocurred: {}".format(
                workspace_name, str(e)
            )
        )
        return None, "Could not get user id"


def _remove_user(user_id, team_id, workspace_name):
    try:
        client = _get_slack_client(workspace_name)
        response = client.admin_users_remove(
            team_id=team_id, user_id=user_id
        )  # admin.users:write
        if response["ok"]:
            return True
        return False
    except Exception as e:
        logger.exception(
            "Could not remove from workspace {}. Error ocurred: {}".format(
                workspace_name, str(e)
            )
        )
        return False


def get_workspace_list():
    workspaceList = []
    for workspace in _get_slack_config():
        workspace_id, error = _get_team_id(workspace)
        if workspace_id is not None:
            workspaceList.append(
                {"workspacename": workspace, "workspace_id": workspace_id}
            )

    return workspaceList
