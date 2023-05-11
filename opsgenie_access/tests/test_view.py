"""Opsgenie Module Display Teams feature tests."""

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
def user_labels():
    form_label = [
        {
            "team": "team_100",
            "usertype": "user",
        }
    ]
    return form_label


@scenario("features/view.feature", "View Requests Data returns empty")
def test_view_requests_data_returns_empty():
    """View Requests Data returns empty."""
    pass


@scenario("features/view.feature", "View teams list return data")
def test_view_teams_list_return_data():
    """View teams list return data."""
    pass


@given("Orgs team list does not exists")
def get_org_team_list_fails(requests_mock):
    requests_mock.get(
        "https://api.opsgenie.com/v2/teams",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey GenieKey test-token",
        },
        json={},
    )
    return_value = helper.teams_list()
    assert return_value == None


@given("Orgs team list exists")
def get_org_team_list_success(requests_mock):
    """Orgs team list exists."""
    requests_mock.get(
        "https://api.opsgenie.com/v2/teams",
        headers={
            "Content-Type": "application/json",
            "Authorization": "GenieKey GenieKey test-token",
        },
        json={
            "data": [
                {
                    "id": "90098alp9-f0e3-41d3-a060-0ea895027630",
                    "name": "ops_team",
                    "description": "",
                },
                {
                    "id": "a30alp45-65bf-422f-9d41-67b10a67282a",
                    "name": "TeamName2",
                    "description": "Description",
                },
            ],
        },
    )
    return_value = helper.teams_list()
    assert return_value == ["ops_team", "TeamName2"]


@when("View requests data", target_fixture="context_output")
def access_request_data(mocker):
    opsgenie_access = access.get_object()
    return opsgenie_access.access_request_data(mocker.Mock())


@then("teams_list is empty")
def list_empty(context_output):
    return_value = context_output
    assert return_value["opsgenie"] == None


@then("teams_list is not empty")
def list_not_empty(context_output):
    return_value = context_output
    assert return_value["opsgenie"] == {
        "ops_team": "ops_team",
        "TeamName2": "TeamName2",
    }
