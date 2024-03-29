import json
import requests
import logging
from EnigmaAutomation.settings import ACCESS_MODULES

logger = logging.getLogger(__name__)


def _get_opsgenie_token():
    return ACCESS_MODULES["ops_genie_access"]["OPSGENIE_TOKEN"]


def _get_ignored_teams():
    return ACCESS_MODULES["ops_genie_access"]["IGNORE_TEAMS"]


def get_team_id(team_name):
    """Getting the team id from the team name."""
    api_endpoint = "https://api.opsgenie.com/v2/teams"
    api_key = _get_opsgenie_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {api_key}",
    }
    params = {"query": team_name}
    try:
        response = requests.get(api_endpoint, headers=headers, params=params)
        if response.status_code == 200:
            teams = json.loads(response.text)["data"]
            for team in teams:
                if team["name"] == team_name:
                    team_id = team["id"]
                    return True, team_id
        else:
            return False, "Could not find team with %s name" % team_name
    except Exception as e:
        logger.error("Could not get team due to exception: {}".format(str(e)))
        return False, "Could not get team with %s name" % team_name


def remove_user_from_team(team, user_email):
    """Removing the user from the team."""
    return_value, team_id = get_team_id(team)
    if return_value is False:
        return False, str(team_id)

    url = "https://api.opsgenie.com/v2/teams/" + team_id + "/members/" + user_email
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % _get_opsgenie_token(),
    }
    try:
        response = requests.delete(url, headers=headers)
        logger.debug(response, response.content)
        return True, response
    except Exception as e:
        logger.error(f"Could not remove user from the team due to excpetion: {str(e)}")
        return False, "Could not remove user from the team"


def add_user_to_opsgenie(user_name, user_email, role):
    """Adds/creates user to opagenie.
    Args:
        Username (str): fullname of user
        Useremail (str): email of the user to be needed
    Returns:
        details of new user
    """
    url = "https://api.opsgenie.com/v2/users"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % _get_opsgenie_token(),
    }
    data = {"username": user_email, "fullName": user_name, "role": {"name": role}}
    logger.debug("Data used to make the add user to opsgenie request" + str(data))
    try:
        response = requests.post(url, headers=headers, json=data)
        return True, response.status_code
    except Exception as e:
        logger.exception(f"Could not add user to opsgenie due to exception {str(e)}")
        return False, "Could not add user to opsgenie"


def get_user(user_email):
    """Gets user details
    Args:
        user_email (str): email of the user
    Returns:
        details of user
    """
    url = "https://api.opsgenie.com/v2/users/" + user_email
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % _get_opsgenie_token(),
    }
    try:
        return requests.get(url, headers=headers)
    except Exception as e:
        logger.error(f"Could not get an user due to exception {str(e)}")
        return None


def delete_user(user_email):
    """Deletes offboarded or offboarding user
    Args:
        username (str): email of the user to be deleted
    Returns:
        userdetails of deleted user
    """
    url = "https://api.opsgenie.com/v2/users/" + user_email
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % _get_opsgenie_token(),
    }
    try:
        response = requests.delete(url, headers=headers)
        return response
    except Exception as e:
        logger.exception(f"Could not delete user due to exception: {str(e)}")
        return None


def create_team_admin_role(team, user_email):
    """creates teamAdmin role
    Args:
        Team (str): name of team in which admin role needs to be created
    Returns:
        details of created TeamAdmin role.
    """

    check_admin = get_user(user_email)
    if check_admin is not None and check_admin.status_code in (200, 201):
        role = check_admin.json()["data"]["role"]["name"]
        if role == "Admin":
            return False, "Admin role Alredy Exist for the %s" % user_email
    if check_admin is None:
        return False, "Could not find user"

    url = "https://api.opsgenie.com/v2/teams/" + team + "/roles?teamIdentifierType=name"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % _get_opsgenie_token(),
    }
    data = {
        "name": "TeamAdmin",
        "rights": [
            {"right": "manage-members", "granted": "false"},
            {"right": "edit-team-roles", "granted": "false"},
            {"right": "delete-team-roles", "granted": "false"},
            {"right": "access-member-profiles", "granted": "true"},
            {"right": "edit-member-profiles", "granted": "true"},
            {"right": "edit-routing-rules", "granted": "false"},
            {"right": "delete-routing-rules", "granted": "false"},
            {"right": "edit-escalations", "granted": "false"},
            {"right": "delete-escalations", "granted": "false"},
            {"right": "edit-schedules", "granted": "true"},
            {"right": "delete-schedules", "granted": "true"},
            {"right": "edit-integrations", "granted": "true"},
            {"right": "delete-integrations", "granted": "true"},
            {"right": "edit-heartbeats", "granted": "true"},
            {"right": "delete-heartbeats", "granted": "true"},
            {"right": "access-reports", "granted": "true"},
            {"right": "edit-services", "granted": "true"},
            {"right": "delete-services", "granted": "true"},
            {"right": "edit-rooms", "granted": "true"},
            {"right": "delete-rooms", "granted": "true"},
            {"right": "send-service-status-update", "granted": "true"},
            {"right": "edit-policies", "granted": "true"},
            {"right": "delete-policies", "granted": "true"},
            {"right": "edit-maintenance", "granted": "true"},
            {"right": "delete-maintenance", "granted": "true"},
            {"right": "edit-automation-actions", "granted": "true"},
            {"right": "delete-automation-actions", "granted": "true"},
            {"right": "subscription-to-services", "granted": "true"},
        ],
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code not in (200, 201):
            return False, "Could not create admin role for opsgenie"
        return True, "Successfully created Admin role"
    except Exception as e:
        logger.error(
            f"Could not create admin role to opsgenie due to exception: {str(e)}"
        )
        return False, "Could not create admin role for opsgenie"


def teams_list():
    """Returns list of teams user have"""
    url = "https://api.opsgenie.com/v2/teams"
    headers = {"Authorization": "GenieKey %s" % _get_opsgenie_token()}
    try:
        teams_response = requests.get(url, headers=headers)
        teams_json = teams_response.json()
        all_teams = []
        for team_index in range(len(teams_json["data"])):
            if teams_json["data"][team_index]["name"] in _get_ignored_teams():
                continue
            all_teams.append(teams_json["data"][team_index]["name"])
        return all_teams
    except Exception as e:
        logger.exception(f"Could not list team due to exception: {str(e)}")
        return None


def add_user_to_team(user_name, user_email, team, role):
    """Add user to the team
    Args:
        username (str): fullname of the user
        useremail (str): email of the user
        team (str): team in which user needed to add
        role (str): role of user
    Returns:
        details of added user
    """
    user_details = get_user(user_email)
    if user_details.status_code not in (200, 201):
        return_result, response_add_user_status_code = add_user_to_opsgenie(
            user_name, user_email, role
        )
        if return_result is False or response_add_user_status_code not in (201, 200):
            return False, "Could not add %s to opsgenie" % user_name

    url = (
        "https://api.opsgenie.com/v2/teams/" + team + "/members?teamIdentifierType=name"
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % _get_opsgenie_token(),
    }
    data = {"user": {"username": user_email}, "role": role}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code not in (200, 201):
            return False, "Could not add %s to opsgenie" % user_name
        return True, "Successfully Added User to Opsgenie"
    except Exception as e:
        logger.exception("Could not add user to opsgenie due to exception: " + str(e))
        return False, "Could not add user to opsgenie"
