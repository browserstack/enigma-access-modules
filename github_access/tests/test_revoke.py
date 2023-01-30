"""GithubAccess Revoke feature tests."""

import pytest
from pytest_bdd import given, scenario, then, when
from BrowserStackAutomation.settings import ACCESS_MODULES

from .. import access
from .. import helpers

@scenario('features/revoke.feature', 'Revoke User Access to a repository fails')
def test_revoke_user_access_to_a_repository_fails():
    pass

@scenario('features/revoke.feature', 'Revoke User Access to a repository success')
def test_revoke_user_access_to_a_repository_success():
    pass

@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.gitusername = "test-username"
    user.email = "test_user@test.com"
    return user

@pytest.fixture
def labels():
    form_label = {
            "action": "repository_access",
            "repository": "test-repo",
            "access_level": "merge",
        }
    return form_label

@pytest.fixture(autouse=True)
def setup_test_config():
  ACCESS_MODULES["github_module"]["GITHUB_TOKEN"] = "test-token"
  ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"] = "https://test-base-url.com"
  ACCESS_MODULES["github_module"]["GITHUB_ORG"] = "test-org"

@given('A git username', target_fixture="user_name")
def user_name():
    return "test-username"

@given('Access will be revoked')
def access_revoked(requests_mock):
    API_URL = f'https://test-base-url.com/repos/test-org/test-repo/collaborators/test-username'
    expected_headers = {'Authorization': 'token test-token'}

    requests_mock.delete(
        API_URL,
        headers=expected_headers,
        status_code=200,
    )

    return_value = helpers.revoke_access(username=user_name(), repo="test-repo")
    assert return_value == True

@given('Access can not be revoked')
def access_not_revoked(requests_mock):
    API_URL = f'https://test-base-url.com/repos/test-org/test-repo/collaborators/test-username'
    expected_headers = {'Authorization': 'token test-token'}

    requests_mock.delete(
        API_URL,
        headers=expected_headers,
        status_code=000,
    )

    return_value = helpers.revoke_access(username=user_name(), repo="test-repo")
    assert return_value == False

@when('I pass revoke request', target_fixture="context_output")
def revoke_request(user, labels, mocker):
    github_access = access.get_object()
    return github_access.revoke(user, labels, mocker.Mock())

@then('Email will be sent')
def success_message(context_output):
    return_value = context_output
    assert return_value == True
