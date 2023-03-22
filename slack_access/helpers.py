from EnigmaAutomation.settings import ACCESS_MODULES
from slack_sdk import WebClient
import logging

logger = logging.getLogger(__name__)

def _get_team_id(workspace):
    try:
        client = WebClient(token=ACCESS_MODULES["slack_access"][workspace]["AUTH_TOKEN"])
        response = client.admin_teams_list()  # team:read
        res = None
        if response["ok"]:
            for response in response["teams"]:
                if response["name"] == workspace:
                    res = response["id"]
            return res, None
        else:
           return None, response["error"]
    except Exception as e:
        logger.error(
            f"Could not get team-id for workspace {workspace}. Error ocurred: {e}"
        )
        return  None ,"Could not get team id"
    
def _get_channel_ids(workspace):
    try:
        client = WebClient(token=ACCESS_MODULES["slack_access"][workspace]["AUTH_TOKEN"])
        response = client.admin_conversations_search()  # admin.conversations:read
        if response["ok"]:
            channel_ids=[]    
            for channel in response["conversations"]:
                if (channel["name"] in ACCESS_MODULES["slack_access"][workspace]["DEFAULT_CHANNEL"]):
                    channel_ids.append(channel["id"])
            return channel_ids , None
            
        return None, response["error"]

    except Exception as e:
        logger.error(
            f"Could not get channel id from workspace {workspace}. Error ocurred: {e}"
        )
        return None ,"Could not get channel id"

def invite_user(email, team_id, workspace):
    channel_ids ,error = _get_channel_ids(workspace)
    if error is not None:
        logger.error(
        f"Could not get channels for requested workspace {workspace}. Error ocurred: {error} "
             )
        return False
    try:    
        client = WebClient(token=ACCESS_MODULES["slack_access"][workspace]["AUTH_TOKEN"])
        response = client.admin_users_invite(
            team_id=team_id, email=email, channel_ids=channel_ids
        )  # admin.users:write
      
        if response["ok"]:
            return True
        return False
    except Exception as e:
        logger.error(
            f"Could not invite user from workspace {workspace}. Error ocurred: {e}"
        )
        return False


# from Access.access_modules.slack_access.helpers import remove_user
def remove_user(email, workspace,team_id):
    user_id, error_message = _get_user_id(email,workspace)
    if not user_id:
        logger.error(
            f"Could not remove user from workspace {workspace}. Error ocurred: {error_message}"
        )
        return False, error_message
    remove_user_resp = _remove_user(user_id, team_id, workspace)
    if not remove_user_resp:
        return (
            False,
            "Error ocurred while removing user from workspace. Please contact Admin",
        )

    return True, None


def _get_user_id(email,workspace):
    try:
        client = WebClient(token=ACCESS_MODULES["slack_access"][workspace]["AUTH_TOKEN"])
        response = client.users_lookupByEmail(
            email=email
        )  # users:read.email users:read
        if response["ok"]:
            return response["user"]["id"], None
        return None, response["error"]

    except Exception as e:
           logger.error(
            f"Could not get user_id from workspace {workspace}. Error ocurred: {e}"
        )
           return None ,"Could not get user id"
        



def _remove_user(user_id, team_id, workspace):
    try:
        client = WebClient(token=ACCESS_MODULES["slack_access"][workspace]["AUTH_TOKEN"])
        response = client.admin_users_remove(
            team_id=team_id, user_id=user_id
        )  # admin.users:write
        if response["ok"]:
            return True
        return False
    except Exception as e:
         logger.error(
            f"Could not remove from workspace {workspace}. Error ocurred: {e}"
           )
         return False


def get_workspace_list():
    workspaceList = []
    for workspace in ACCESS_MODULES['slack_access']:
        workspace_id , error = _get_team_id(workspace)
        if workspace_id is not None:
            workspaceList.append({
                "workspacename":workspace,
                "workspace_id":workspace_id
            })
    
    return workspaceList

