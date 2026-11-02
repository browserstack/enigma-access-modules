"""OpsgenieAccess User feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
import pytest
from .. import access
from .. import helper
import json


@pytest.fixture
def user_labels():
    form_label = [
        {
            "team": "team_100",
            "usertype": "user",
        }
    ]
    return form_label


@pytest.fixture
def patched_email(mocker):
    mocker.patch(
        "Access.access_modules.opsgenie_access.access.OpsgenieAccess._OpsgenieAccess__send_approve_email",
        return_value=""
    )


@pytest.fixture(autouse=True)
def setup_test_config(mocker):
    mocker.patch(
        "Access.access_modules.opsgenie_access.helper._get_opsgenie_token",
        return_value="test-token",
    )
    mocker.patch(
        "Access.access_modules.opsgenie_access.helper._get_ignored_teams",
        return_value=["team_1", "team_2"],
    )


@pytest.fixture
def user_identity(mocker, user):
    user_identity = mocker.MagicMock()
    user_identity.user = user
    return user_identity


@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.email = "invalid@nonexistent.com"
    user.user.username = "test-user"
    return user


@pytest.fixture
def request_obj(mocker):
    request_obj = mocker.MagicMock()
    request_obj.request_id = "123"
    return request_obj


@scenario("features/user.feature", "Add user to Opsgenie fails")
def test_add_user_to_opsgenie_fails():
    """Add user to Opsgenie fails."""
    pass


@scenario("features/user.feature", "Add user to Opsgenie success")
def test_add_user_to_opsgenie_success():
    """Add user to Opsgenie success."""
    pass


@scenario("features/user.feature", "User does not exist on Opsgenie")
def test_user_does_not_exist_on_opsgenie():
    """User does not exist on Opsgenie."""
    pass


@given("A user_email")
def user_email():
    """A user_email."""
    return "invalid@nonexistent.com"


@given("User does not exist on Opsgenie")
def user_fail(requests_mock):
    """User does not exist on Opsgenie."""

    requests_mock.get(
        url="https://api.opsgenie.com/v2/users/" + user_email(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        status_code=404,
    )

    return_value = helper.get_user(user_email())
    assert return_value.status_code == 404


@given("User can be added to Opsgenie")
def user_can_be_added(requests_mock):
    """Mock to allow adding user."""
    url = "https://api.opsgenie.com/v2/users"
    requests_mock.post(
        url=url,
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        json=json.dumps({
            "username": "invalid@nonexistent.com",
            "fullName": "test-user",
            "role": {"name": "user"}
        }),
        status_code=200,
    )


@given("User can be added to Opsgenie team")
def user_can_be_added_team(requests_mock):
    """Mock to allow adding user to team"""
    requests_mock.post(
        "https://api.opsgenie.com/v2/teams/"
        + "team_100"
        + "/members?teamIdentifierType=name",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        json=json.dumps({
            "user": {"username": "invalid@nonexistent.com"},
            "role": "user"
        }),
        status_code=201,
    )


@given("a name")
def user_name():
    """a name."""
    return "test-user"


@given("a role")
def role():
    """a role."""
    return "user"


@when("I pass approval request", target_fixture="context_output")
def approve_pass(user_identity, user_labels, request_obj, patched_email):
    opsgenie_access = access.get_object()
    return opsgenie_access.approve(
        user_identity, user_labels, "test-approver", request_obj
    )


@when(
    "I pass approval request for adding user to opsgenie",
    target_fixture="context_output",
)
def approve_pass(user_identity, user_labels, request_obj, patched_email):
    opsgenie_access = access.get_object()
    return opsgenie_access.approve(
        user_identity, user_labels, "test-approver", request_obj
    )


@then("return value should be False")
def false_value(context_output):
    """return value should be False."""
    return_value = context_output[0]
    assert return_value is False


@then("return value should be true")
def true_value(context_output):
    """return value should be True."""
    return_value = context_output[0]
    assert return_value is True
