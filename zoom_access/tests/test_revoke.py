"""ZoomAccess Revoke feature tests."""

import pytest
from .. import access
from .. import helper
import json

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@pytest.fixture
def labels():
    form_label = {
        "action": "zoom_access",
        "access_type": "Standard License",
    }
    return form_label


@pytest.fixture
def usera(mocker):
    usera = mocker.MagicMock()
    usera.email = user_email()
    usera.state = 2
    return usera


@pytest.fixture
def user_a(mocker):
    user_a = mocker.MagicMock()
    user_a.identity = {"user_email": user_email()}
    return user_a


@pytest.fixture(autouse=True)
def setup_test_config():
    helper.ZOOM_API_KEY = "test-token"
    helper.ZOOM_BASE_URL = "https://test-base-url.com/"
    helper.ZOOM_CLIENT_SECRET = "test-secret"


@scenario("features/revoke.feature", "Revoke User Access to a zoom success")
def test_revoke_user_access_to_a_zoom_success():
    """Revoke User Access to a zoom success."""
    pass


@given("Access will be revoked")
def revoke_sucess(requests_mock, mocker):
    mocker.patch(
        'Access.access_modules.zoom_access.helper.get_token',
        return_value="test-token"
    )
    requests_mock.get(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "token test-token",
            "Content-Type": "application/json",
        },
        status_code=200,
        json={
            "id": user_id(),
        },
    )
    requests_mock.delete(
        "https://test-base-url.com/users/" + user_id(),
        headers={
            "Authorization": "token test-token",
            "Content-Type": "application/json",
        },
        status_code=204,
    )
    mocker.patch(
        "Access.access_modules.zoom_access.access.Zoom._Zoom__send_revoke_email",
        return_value=""
    )
    return_value = helper.delete_user(user_email())
    assert return_value[0] == 204


@given("a user email")
def user_email():
    return "invalid@nonexistent.com"


def user_id():
    return "test-id"


@when("I pass revoke request", target_fixture="context_output")
def revoke_request(usera, user_a, labels, mocker):
    zoom_access = access.get_object()
    return zoom_access.revoke(usera, user_a, labels, mocker.Mock())


@then("Email will be sent")
def success_message(context_output):
    return_value = context_output
    assert return_value[0] is True


@scenario("features/revoke.feature", "Revoke User Access to a zoom fails")
def test_revoke_user_fails_to_a_zoom_fails():
    """Revoke User Access to a zoom fails."""
    pass


@given("Access can not be revoked")
def revoke_fails(requests_mock, mocker):
    mocker.patch(
        'Access.access_modules.zoom_access.helper.get_token',
        return_value="test-token"
    )
    requests_mock.get(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "token test-token",
            "Content-Type": "application/json",
        },
        status_code=404,
    )
    requests_mock.delete(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "token test-token",
            "Content-Type": "application/json",
        },
        status_code=404,
    )
    mocker.patch(
        "Access.access_modules.zoom_access.access.Zoom._Zoom__send_revoke_email",
        return_value=""
    )
    return_value = helper.delete_user(user_email())
    assert return_value[0] == 204
