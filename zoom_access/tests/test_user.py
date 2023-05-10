"""ZoomAccess User feature tests."""

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
def user_identity_a(mocker):
    identity_mock = mocker.MagicMock()
    user_mock = mocker.MagicMock()
    user_mock.email = user_email()
    user_mock.name = user_name()
    identity_mock.user = user_mock
    return identity_mock


@pytest.fixture
def labels():
    form_labels = [{
        "action": "zoom_access",
        "access_type": "Standard License",
    }]
    return form_labels


@pytest.fixture
def usera(mocker):
    usera = mocker.MagicMock()
    usera.email = user_email()
    usera.state = 2
    return usera


@pytest.fixture(autouse=True)
def setup_test_config():
    helper.ZOOM_API_KEY = "test-token"
    helper.ZOOM_BASE_URL = "https://test-base-url.com/"
    helper.ZOOM_CLIENT_SECRET = "test-secret"


@scenario("features/user.feature", "User does not exist on zoom")
def test_user_does_not_exist_on_zoom():
    """User does not exist on zoom."""
    pass


@given("User does not exist on zoom")
def user_does_not_exist(requests_mock, mocker):
    mocker.patch(
        'Access.access_modules.zoom_access.helper.get_token',
        return_value="test-token"
    )
    requests_mock.post(
        "https://test-base-url.com/users/",
        headers={
            "Authorization": "token test-token",
            "Content-Type": "application/json",
        },
        json=json.dumps(
            {
                "action": "create",
                "user_info": {"email": user_email(), "type": 1},
            }
        ),
        status_code=404,
    )

    requests_mock.get(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "token test-token",
            "Content-Type": "application/json",
        },
        status_code=404,
    )

    return_value = helper.get_user(user_email())
    assert return_value[0] == 404


@given("a user email")
def user_email():
    """a user email."""
    return "invalid@nonexistent.com"


def user_name():
    """mock user name"""
    return "invalid_user_name"


@when("I pass approval request", target_fixture="context_output")
def revoke_request(usera, user_identity_a, labels):
    zoom_access = access.get_object()
    return zoom_access.approve(user_identity_a, labels, "test-approver", usera)


@then("return value should be False")
def return_false(context_output):
    return_value = context_output[0]
    assert return_value is False
