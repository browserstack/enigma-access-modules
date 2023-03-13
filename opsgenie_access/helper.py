import json, requests
import logging
from . import constants
from BrowserStackAutomation.settings import ACCESS_MODULES

OPSGENIE_TOKEN = ACCESS_MODULES["opsgenie_access"]["OPSGENIE_TOKEN"]
logger = logging.getLogger(__name__)


def add_user_to_opsgenie(Username, Useremail):
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
    data = {"username": Useremail, "fullName": Username, "role": {"name": "org_user"}}
    logger.debug(data)
    response = requests.post(url, headers=headers, json=data)
    logger.debug(response, response.content)


def get_user(username):
    """Gets user details
    Args:
        username (str): email of the user
    Returns:
        details of user
    """
    url = "https://api.opsgenie.com/v2/users/" + username
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    response = requests.get(url, headers=headers)
    logger.debug(response, response.content)
    return response


def get_user_list():
    """Returns Gets list of users"""
    url = "https://api.opsgenie.com/v2/users/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    response = requests.get(url, headers=headers)
    logger.debug(response, response.content)


def delete_user(username):
    """Deletes offboarded or offboarding user
    Args:
        username (str): email of the user to be deleted
    Returns:
        userdetails of deleted user
    """
    url = "https://api.opsgenie.com/v2/users/" + username
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    response = requests.delete(url, headers=headers)
    logger.debug(response, response.content)


def create_team_admin_role(Team):
    """creates teamAdmin role
    Args:
        Team (str): name of team in which admin role needs to be created
    Returns:
        details of created TeamAdmin role.
    """
    url = "https://api.opsgenie.com/v2/teams/" + Team + "/roles?teamIdentifierType=name"
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
    response = requests.post(url, headers=headers, json=data)
    logger.debug(response, response.content)
    return response


def teams_list():
    """Returns list of teams user have"""
    url = "https://api.opsgenie.com/v2/teams"
    headers = {"Authorization": "GenieKey %s" % OPSGENIE_TOKEN}
    teams_response = requests.get(url, headers=headers)
    teams_json = teams_response.json()
    all_teams = []
    ignore_teams = [
        "alertmanager-test-team",
        "rails",
        "test-team",
        "emergency",
        "catchall",
        "tunnel",
        "prod",
        "dcops",
        "nagiosteam",
    ]
    for team_index in range(len(teams_json["data"])):
        if teams_json["data"][team_index]["name"] in ignore_teams:
            continue
        all_teams.append(teams_json["data"][team_index]["name"])
    return all_teams


def add_user_to_team(Username, Useremail, team, role):
    """Add user to the team
    Args:
        username (str): fullname of the user
        useremail (str): email of the user
        team (str): team in which user needed to add
        role (str): role of user
    Returns:
        details of added user
    """
    add_user_to_opsgenie(Username, Useremail)
    url = (
        "https://api.opsgenie.com/v2/teams/" + team + "/members?teamIdentifierType=name"
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": "GenieKey %s" % OPSGENIE_TOKEN,
    }
    data = {"user": {"username": Useremail}, "role": role}
    response = requests.post(url, headers=headers, json=data)
    logger.debug(response, response.content)
    return response


def is_email_valid(user_email, email):
    """Returns that if user is already exist on Opgenie"""
    response = get_user(user_email)
    if "data" in response.json():
        return True
    return False
