"""ZoomAccess User feature tests."""

import pytest
from Access.access_modules.zoom_access import access
from Access.access_modules.zoom_access import helper
import json

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@pytest.fixture
def user_a(mocker):
    user_a = mocker.MagicMock()
    user_a.identity = {"user_email": "test@test.com"}
    return user_a


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
    usera.email = "test@test.com"
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
def user_does_not_exist(requests_mock):
    requests_mock.post(
        "https://test-base-url.com/users",
        headers={
            "Authorization": "token test-token",
            "Content-Type": "application/json",
        },
        json=json.dumps(
            {
                "action": "create",
                "user_info": {"email": "test@test.com", "type": 1},
            }
        ),
        status_code=404,
    )

    requests_mock.get(
        "https://test-base-url.com/users/test@test.com",
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
    return "test@test.com"


@when("I pass approval request", target_fixture="context_output")
def revoke_request(usera, user_a, labels):
    zoom_access = access.get_object()
    return zoom_access.approve(user_a, labels, "test-approver", usera)


@then("return value should be False")
def return_false(context_output):
    return_value = context_output[0]
    assert return_value is False
