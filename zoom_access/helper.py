""" helper functions for zoom access module"""

from time import sleep
import datetime
import json
import logging
import jwt
import requests

from EnigmaAutomation.settings import ACCESS_MODULES
from . import constants

logger = logging.getLogger(__name__)


def _get_api_key():
    return ACCESS_MODULES["zoom_access"]["ZOOM_API_KEY"]


def _get_zoom_api_base_url():
    return ACCESS_MODULES["zoom_access"]["ZOOM_BASE_URL"]


def _get_zoom_client_secret():
    return ACCESS_MODULES["zoom_access"]["ZOOM_CLIENT_SECRET"]


def get_token():
    """Returns the zoom token created using ZOOM API KEY and ZOOM CLIENT SECRET"""
    curr_dt = datetime.datetime.now() + datetime.timedelta(hours=1)
    encoded_jwt = jwt.encode(
        {"iss": _get_api_key(), "exp": curr_dt.timestamp()},
        _get_zoom_client_secret(),
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
            try:
                response = requests.patch(
                    url,
                    data=json.dumps(data),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + zoom_jwt_token,
                    },
                    timeout=constants.TIMEOUT_VALUE,
                )
            except requests.exceptions.ChunkedEncodingError:
                # this occurs on special case of 204 no content
                return [204, ""]

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


def grant_access(user, access_type):
    user_details = get_user(user.email)
    if user_details[0] == 200:
        response = update_user(user.email, access_type)
        if response[0] != 204:
            return False, "User updation failed" + str(response)
    else:
        response = create_user(user.email, access_type, user.name)
        if response[0] != 200 or response[0] != 201:
            return False, "User creation failed" + str(response)

    return True, ""


def get_user(email):
    """Gets user details
    Args:
        email (str): email of the user to be created
    Returns:
        details of user
    """
    url = _get_zoom_api_base_url() + "users/"
    user_details = make_request(url + email)
    logger.debug("[ZOOM] get_user - %s", str(user_details))
    return user_details


def delete_user(email):
    """Deletes offboarded or offboarding user
    Args:
        email (str): email of the user to be created
    Returns:
        userdetails of deleted user
    """
    url = _get_zoom_api_base_url() + "users/"
    user_details = get_user(email)
    if user_details[0] != 404:
        user_id = user_details[1]["id"]
        user_details = make_request(url + user_id, "DELETE")
        logger.info("[ZOOM] delete_user - %s", str(user_details))
        return user_details
    return [204]


def create_user(email, access_type, name=None):
    """Creates new user
    Args:
        email: email of the user to be created
        name(string): name of user
        access_type: type of access to be given (1-> standard , 2-> Pro License)
    Returns:
        userdetails of created user
    """
    url = _get_zoom_api_base_url() + "users/"
    data = {
        "action": "create",
        "user_info": {"email": email, "first_name": name, "type": access_type},
    }
    user_details = make_request(url, "POST", data)
    logger.info("[ZOOM] create_user - %s", str(user_details))
    return user_details


def update_user(email, access_type):
    """Updates user email
    Args:
        email (str): email of the user to be updated
        access_type : login types
    Returns:
        userdetails of updated user
    """
    url = _get_zoom_api_base_url() + "users/" + email
    data = {"type": access_type}
    user_details = make_request(url, "PATCH", data)
    logger.info("[ZOOM] update_user - %s", str(user_details))
    return user_details
