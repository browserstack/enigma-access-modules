"""OpsgenieAccess Revoke feature tests."""
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
def user_labels():
    form_label = [
        {
            "team": "team_100",
            "usertype": "user",
        }
    ]
    return form_label


@pytest.fixture(autouse=True)
def setup_test_config():
    helper.OPSGENIE_TOKEN = ("test-token",)
    helper.IGNORE_TEAMS = ["team_1", "team_2"]


@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.email = "invalid@nonexistent.com"
    user.user.username = "test-user"
    user.state = 2
    return user


@scenario("features/revoke.feature", "Revoke User Access to a opsgenie fails")
def test_revoke_user_access_to_a_opsgenie_fails():
    """Revoke User Access to a opsgenie fails."""
    pass


@scenario("features/revoke.feature", "Revoke User Access to a opsgenie success")
def test_revoke_user_access_to_a_opsgenie_success():
    """Revoke User Access to a opsgenie success."""
    pass


@given("Access can not be revoked")
def revoke_fail(requests_mock):
    """Access can not be revoked."""
    requests_mock.delete(
        "https://api.opsgenie.com/v2/users/" + "invalid@nonexistent.com",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey GenieKey test-token",
        },
        status_code=404,
    )

    return_value = helper.delete_user(user_email())
    assert return_value.status_code == 404


@given("Access will be revoked")
def revoke_success(requests_mock):
    """Access will be revoked."""
    requests_mock.delete(
        "https://api.opsgenie.com/v2/users/" + "invalid@nonexistent.com",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey GenieKey test-token",
        },
        status_code=201,
        json={
            "result": "Deleted",
        },
    )

    return_value = helper.delete_user(user_email())
    assert return_value is not None


@given("a user email")
def user_email():
    """a user email."""
    return "invalid@nonexistent.com"


@when("I pass revoke request", target_fixture="context_output")
def revoke_request(user, user_labels, mocker):
    """I pass revoke request."""
    opsgenie_access = access.get_object()
    return opsgenie_access.revoke(user, user, user_labels, mocker.Mock())


@then("Approved Email will be sent")
def success_message(context_output):
    return_value = context_output
    assert return_value[0] is True


@then("Grantfailed Email will be sent")
def failed_message(context_output):
    return_value = context_output
    assert return_value[0] is False
