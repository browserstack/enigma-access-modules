"""Github Module Display Repos feature tests."""

import pytest
from pytest_bdd import given, scenario, then, when
from .. import access
from .. import helpers


@scenario("features/views.feature", "View Requests Data returns data")
def test_view_requests_data_returns_data():
    pass


@scenario("features/views.feature", "View Requests Data returns empty")
def test_view_requests_data_returns_empty():
    pass


@scenario("features/views.feature", "View Validates Request")
def test_view_validates_request():
    pass


@pytest.fixture(autouse=True)
def setup_test_config():
    helpers.GITHUB_TOKEN = "test-token"
    helpers.GITHUB_BASE_URL = "https://test-base-url.com"
    helpers.GITHUB_ORG = "test-org"


@given("Orgs repo list exists")
def get_org_repo_list_success(requests_mock):
    API_URL = "https://test-base-url.com/orgs/test-org/repos"
    expected_headers = {
        "Authorization": "token test-token",
        "Accept": "application/vnd.github.v3+json",
    }

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=200,
        json=[
            {
                "id": "001",
                "full_name": "org/repo1",
            },
            {
                "id": "002",
                "full_name": "org/repo2",
            },
        ],
    )

    return_value = helpers.get_org_repo_list()
    assert return_value == ["org/repo1", "org/repo2"]


@given("Orgs repo list does not exist")
def get_org_repo_list_fail(requests_mock):
    API_URL = "https://test-base-url.com/orgs/test-org/repos"
    expected_headers = {
        "Authorization": "token test-token",
        "Accept": "application/vnd.github.v3+json",
    }

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=404,
    )

    return_value = helpers.get_org_repo_list()
    assert return_value == []


@when("View requests data", target_fixture="context_output")
def access_request_data(mocker):
    github_access = access.get_object()
    return github_access.access_request_data(mocker.Mock())


@then("githubRepoList is not empty")
def list_not_empty(context_output):
    return_value = context_output
    assert return_value == {"githubRepoList": ["org/repo1", "org/repo2"]}


@then("githubRepoList is empty")
def list_empty(context_output):
    return_value = context_output
    assert return_value == {"githubRepoList": []}


@pytest.fixture
def labels():
    access_labels_data = [
        {
            "repoList": [
                "org/repo1",
                "org/repo2",
            ],
            "accessLevel": "merge",
        }
    ]
    return access_labels_data


@when("View requests validation", target_fixture="context_output")
def validate_request(mocker, labels):
    github_access = access.get_object()
    return github_access.validate_request(labels, mocker.Mock())


@then("validated request is returned")
def validate_output(context_output):
    return_value = context_output
    assert return_value == [
        {
            "action": "repository_access",
            "access_level": "merge",
            "repository": "org/repo1",
        },
        {
            "action": "repository_access",
            "access_level": "merge",
            "repository": "org/repo2",
        },
    ]
