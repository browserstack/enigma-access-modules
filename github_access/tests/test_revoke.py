"""GithubAccess Revoke feature tests."""

import pytest
from pytest_bdd import given, scenario, then

from .. import helpers


@scenario("features/revoke.feature",
          "Revoke User Access to a repository fails")
def test_revoke_user_access_to_a_repository_fails():
    """ Revoke User Access to a repository fails"""
    pass


@scenario("features/revoke.feature",
          "Revoke User Access to a repository success")
def test_revoke_user_access_to_a_repository_success():
    """ Revoke User Access to a repository success"""
    pass


@pytest.fixture
def user(mocker):
    """ Mock user object """
    user_mock = mocker.MagicMock()
    user_mock.gitusername = user_name()
    user_mock.email = "test_user@test.com"
    return user_mock


@pytest.fixture
def user_identity(mocker):
    """ Mock user identity object """
    identity_mock = mocker.MagicMock()
    identity_mock.identity = {
        "username": user_name(),
    }
    return identity_mock


@pytest.fixture
def labels():
    """ Mock labels object """
    return {
        "action": "repository_access",
        "repository": "test-repo",
        "access_level": "merge",
    }


@pytest.fixture(autouse=True)
def setup_test_config(mocker):
    """ Mock config """
    mocker.patch(
        "Access.access_modules.github_access.helpers._get_github_config",
        return_value={
            "GITHUB_TOKEN": "test-token",
            "GITHUB_BASE_URL": "https://test-base-url.com",
            "GITHUB_ORG": "test-org",
        }
    )


@given("A git username", target_fixture="user_name")
def user_name():
    """ Return a username """
    return "test-username"


@given("Access will be revoked", target_fixture="context_output")
def access_revoked(requests_mock):
    """ Ensure mocks for revoke is possible """
    api_url = (
        "https://test-base-url.com/repos/test-org/test-repo/collaborators/"
        + user_name()
    )
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.delete(
        api_url,
        headers=expected_headers,
        status_code=200,
    )

    return_value = helpers.revoke_access(
        username=user_name(), repo="test-repo")
    return return_value


@given("Access can not be revoked", target_fixture="context_output")
def access_not_revoked(requests_mock, mocker):
    """ Ensure mocks for revoke is not possible """
    api_url = (
        "https://test-base-url.com/repos/test-org/test-repo/collaborators/"
        + user_name()
    )
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.delete(
        api_url,
        headers=expected_headers,
        status_code=000,
    )
    mocker.patch(
        "Access.access_modules.github_access.access."
        "GithubAccess._GithubAccess__send_revoke_email",
        return_value=""
    )

    return_value = helpers.revoke_access(
        username=user_name(), repo="test-repo")
    return return_value


@then("Access is revoked")
def access_is_revoked(context_output):
    """ Ensure revoke function returns True """
    assert context_output is True


@then("Access is not revoked")
def access_is_not_revoked(context_output):
    """ Ensure revoke function returns False """
    assert context_output is False
