"""OpsgenieAccess Grant feature tests."""

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


@pytest.fixture(autouse=True)
def setup_test_config():
    helper.OPSGENIE_TOKEN = ("test-token",)
    helper.IGNORE_TEAMS = ["team_1", "team_2"]


@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.email = "test@test.com"
    user.user.username = "test-user"
    return user


@pytest.fixture
def user_identity(mocker, user):
    user_identity = mocker.MagicMock()
    user_identity.user = user
    return user_identity


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
def admin_labels():
    form_label = [
        {
            "team": "team_100",
            "usertype": "team_admin",
        }
    ]
    return form_label


@pytest.fixture
def user_identity_1(mocker, user):
    user_identity_1 = mocker.MagicMock()
    user_identity_1.user = user
    return user_identity_1


@pytest.fixture
def request_obj(mocker):
    request_obj = mocker.MagicMock()
    request_obj.request_id = "123"
    return request_obj


@scenario("features/approve.feature", "Grant Access Fails")
def test_grant_access_fails():
    """Grant Access Fails."""
    pass


@scenario("features/approve.feature", "Grant Add user to team Success")
def test_grant_add_user_to_team_success():
    """Grant Add user to team Success."""
    pass


@scenario("features/approve.feature", "Grant Give Admin Access Success")
def test_grant_give_admin_access_success():
    """Grant Give Admin Access Success."""
    pass


@given("Access can be granted to user to add into team")
def access_grant_add_user_to_team(requests_mock):
    """Access can be granted to user to add into team."""
    requests_mock.get(
        "https://api.opsgenie.com/v2/users/test@test.com",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        json={"name": "test-user"},
        status_code=200,
    )

    requests_mock.post(
        "https://api.opsgenie.com/v2/teams/"
        + "team_100"
        + "/members?teamIdentifierType=name",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        json=json.dumps({"user": {"username": "test@test.com"}, "role": "user"}),
        status_code=201,
    )

    return_value, messages = helper.add_user_to_team(
        "test-user", user_email(), "team_100", "user"
    )
    assert return_value is True


@given("Access can be granted to user to give admin access")
def access_grant_team_admin_success(requests_mock):
    """Access can be granted to user to give admin access."""
    requests_mock.get(
        "https://api.opsgenie.com/v2/users/test@test.com",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        json={
            "data": {
                "username": "test@test.com",
                "role": {"name": "user"},
            },
        },
        status_code=200,
    )
    requests_mock.post(
        "https://api.opsgenie.com/v2/teams/"
        + "team_100"
        + "/roles?teamIdentifierType=name",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        json=json.dumps({"name": "TeamAdmin", "rights": []}),
        status_code=201,
    )

    requests_mock.post(
        "https://api.opsgenie.com/v2/teams/"
        + "team_100"
        + "/members?teamIdentifierType=name",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        json=json.dumps(
            {
                "user": {
                    "username": "test@test.com",
                },
                "role": "TeamAdmin",
            }
        ),
        status_code=201,
    )
    return_value, messages = helper.create_team_admin_role("team_100", user_email())
    assert return_value is True


@given("User exists on opsgenie")
def user_exists(requests_mock):
    """User exists on opsgenie."""
    requests_mock.get(
        "https://api.opsgenie.com/v2/users/test@test.com",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey test-token",
        },
        json={"name": "test-user"},
        status_code=200,
    )
    response = helper.get_user("test@test.com")
    assert response.status_code == 200
    assert response.json() == {"name": "test-user"}


@given("an user email")
def user_email():
    """an user email."""
    return "test@test.com"


@when("I pass approval request for add user to team", target_fixture="context_output")
def user_approve(user_identity, user_labels, request_obj):
    opsgenie_access = access.get_object()
    return opsgenie_access.approve(
        user_identity, user_labels, "test-approver", request_obj
    )


@when("I pass approval request to give admin access", target_fixture="context_output")
def admin_approve(user_identity, admin_labels, request_obj):
    opsgenie_access = access.get_object()
    return opsgenie_access.approve(
        user_identity, admin_labels, "test-approver", request_obj
    )


@then("return value should be False")
def false_value(context_output):
    """return value should be False."""
    return_value = context_output[0]
    assert return_value is False


@then("return value should be True")
def true_output(context_output):
    """return value should be True."""
    return_value = context_output[0]
    assert return_value is True
