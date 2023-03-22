import json, requests
import logging
from . import constants
from EnigmaAutomation.settings import ACCESS_MODULE

OPSGENIE_TOKEN = ACCESS_MODULES["opsgenie_access"]["OPSGENIE_TOKEN"]
logger = logging.getLogger(__name__)


def add_user_to_opsgenie(user_name, user_email):
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
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    data = {"username": user_email, "fullName": user_name, "role": {"name": "org_user"}}
    logger.debug(data)
    try:
        response = requests.post(url, headers=headers, json=data)
        logger.debug(response, response.content)
        return response.status_code
    except Exception as e:
        logger.error("Could not add user to opsgenie")


def get_user(user_name):
    """Gets user details
    Args:
        username (str): email of the user
    Returns:
        details of user
    """
    url = "https://api.opsgenie.com/v2/users/" + user_name
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    try:
        response = requests.get(url, headers=headers)
        logger.debug(response, response.content)
        return response
    except Exception as e:
        logger.error("Could not get an user")
        return response


def get_user_list():
    url = "https://api.opsgenie.com/v2/users/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    response = requests.get(url, headers=headers)
    logger.debug(response, response.content)


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
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    try:
        response = requests.delete(url, headers=headers)
        logger.debug(response, response.content)
        return response
    except Exception as e:
        logger.error("Could not delete user")
        return None


def create_team_admin_role(team):
    """creates teamAdmin role
    Args:
        Team (str): name of team in which admin role needs to be created
    Returns:
        details of created TeamAdmin role.
    """
    url = "https://api.opsgenie.com/v2/teams/" + team + "/roles?teamIdentifierType=name"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
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
        logger.error("Could not create admin role to opsgenie")
        return False, "Could not create admin role for opsgenie"


def teams_list():
    """Returns list of teams user have"""
    url = "https://api.opsgenie.com/v2/teams"
    headers = {"Authorization": "GenieKey %s" % OPSGENIE_TOKEN}
    teams_response = requests.get(url, headers=headers)
    teams_json = teams_response.json()
    all_teams = []
    ignore_teams = []
    for team_index in range(len(teams_json["data"])):
        if teams_json["data"][team_index]["name"] in ignore_teams:
            continue
        all_teams.append(teams_json["data"][team_index]["name"])
    return all_teams


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
    return_value = True
    user_details = get_user(user_email)
    if user_details.status_code not in (200, 201):
        return_value = False

    if return_value == False:
        response_add_user_status_code = add_user_to_opsgenie(user_name, user_email)
        if response_add_user_status_code not in (201, 200):
            return False, "Could not add %s to opsgenie" % user_name

    url = (
        "https://api.opsgenie.com/v2/teams/" + team + "/members?teamIdentifierType=name"
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    data = {"user": {"username": user_email}, "role": role}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code not in (200, 201):
            return False, "Could not add %s to opsgenie" % user_name
        return True, "Successfully Added User to Opsgenie"
    except Exception as e:
        logger.error("Could not add user to opsgenie")
        return False, str(e)
