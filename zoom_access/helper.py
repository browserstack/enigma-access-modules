""" helper functions for zoom access module"""
import json
import logging
from time import sleep
import datetime
import requests
from requests.auth import HTTPBasicAuth
import jwt
from EnigmaAutomation.settings import ACCESS_MODULES
from . import constants

ZOOM_API_KEY = ACCESS_MODULES["zoom_access"]["ZOOM_API_KEY"]
ZOOM_BASE_URL = ACCESS_MODULES["zoom_access"]["ZOOM_BASE_URL"]
ZOOM_CLIENT_SECRET = ACCESS_MODULES["zoom_access"]["ZOOM_CLIENT_SECRET"]

logger = logging.getLogger(__name__)


def get_token():
    """Returns the zoom token created using ZOOM API KEY and ZOOM CLIENT SECRET"""
    curr_dt = datetime.datetime.now() + datetime.timedelta(hours=1)
    encoded_jwt = jwt.encode(
        {"iss": ZOOM_API_KEY, "exp": curr_dt.timestamp()},
        ZOOM_CLIENT_SECRET,
        algorithm="HS256",
    )
    return encoded_jwt


def make_request(url, request_type="GET", data=None):
    """Makes API request to zoom
    Args:
        url (str): requested API endpoint
        request_type(str): type of request
        data : data which is reqired for the request

    Returns:
        response details (array): array of response code and response data

    """
    success = False
    retry_count = 0
    response_data = None
    zoom_jwt_token = get_token()
    while not success:
        retry_count = retry_count + 1
        if request_type == "GET":
            response = requests.get(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + zoom_jwt_token,
                },
                timeout=constants.TIMEOUT_VALUE,
            )
        elif request_type == "PATCH":
            response = requests.patch(
                url,
                data=json.dumps(data),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + zoom_jwt_token,
                },
                timeout=constants.TIMEOUT_VALUE,
            )
        elif request_type == "DELETE":
            response = requests.delete(
                url,
                data=json.dumps(data),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + zoom_jwt_token,
                },
                timeout=constants.TIMEOUT_VALUE,
            )
        else:
            response = requests.post(
                url,
                data=json.dumps(data),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + zoom_jwt_token,
                },
                timeout=constants.TIMEOUT_VALUE,
            )
        success = (
            response.status_code in [200, 201, 204]
            or retry_count >= constants.RETRY_LIMIT
        )
        if not success:
            sleep(2**retry_count)
            continue
        try:
            response_data = response.json()
        except Exception:
            response_data = None
    if response.status_code == 401:
        raise Exception("Zoom Access token is Expired.")
    return [response.status_code, response_data]


def get_user(email):
    """Gets user details
    Args:
        email (str): email of the user to be created
    Returns:
        details of user
    """
    url = ZOOM_BASE_URL + "users/"
    user_details = make_request(url + email)
    logger.info("[ZOOM] get_user - %s", str(user_details))
    return user_details


def delete_user(email):
    """Deletes offboarded or offboarding user
    Args:
        email (str): email of the user to be created
    Returns:
        userdetails of deleted user
    """
    url = ZOOM_BASE_URL + "users/"
    user_details = get_user(email)
    if user_details[0] != 404:
        user_id = user_details[1]["id"]
        user_details = make_request(url + user_id, "DELETE")
        logger.info("[ZOOM] delete_user - %s", str(user_details))
        return user_details
    return [204]


def create_user(email, type, name=None):
    """Creates new user
    Args:
        email: email of the user to be created
        name(string): name of user
        type: type of access to be given (1-> standard , 2-> Pro License)
    Returns:
        userdetails of created user
    """
    url = ZOOM_BASE_URL + "users/"
    data = {
        "action": "create",
        "user_info": {"email": email, "first_name": name, "type": type},
    }
    user_details = make_request(url, "POST", data)
    logger.info("[ZOOM] create_user - %s", str(user_details))
    return user_details


def update_user(email, type):
    """Updates user email
    Args:
        email (str): email of the user to be updated
        type : login types
    Returns:
        userdetails of updated user
    """
    url = ZOOM_BASE_URL + "users/" + email
    data = {"type": type}
    user_details = make_request(url, "PATCH", data)
    logger.info("[ZOOM] update_user - %s", str(user_details))
    return user_details


def is_email_valid(user_email, email):
    """Checks email validation
    Args:
        user_email (str): new email to be updated
        email (str): email of the user to be validated
    Returns:
       true if user_email is active on zoom or false if not active.
    """
    zoom_jwt_token = get_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + zoom_jwt_token,
    }
    url = ZOOM_BASE_URL + "users/" + user_email
    response = requests.get(url, headers=headers, timeout=constants.TIMEOUT_VALUE)
    if response.status_code == 200:
        if "status" in response.json():
            usr_status = str(json.loads(response.text)["status"])
            if usr_status is not None and usr_status == "active":
                return True
            logger.error(constants.GET_USER_BY_EMAIL_FAILED)
            return False
    return False
