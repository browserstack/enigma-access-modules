"""GithubAccess User feature tests."""

import pytest
from pytest_bdd import given, scenario, then, when
from .. import access
from .. import helpers


@pytest.fixture(autouse=True)
def setup_test_config():
    helpers.GITHUB_TOKEN = "test-token"
    helpers.GITHUB_BASE_URL = "https://test-base-url.com"
    helpers.GITHUB_ORG = "test-org"


@scenario("features/user.feature", "User does not exist on github")
def test_user_does_not_exist_on_github():
    pass


@scenario("features/user.feature", "Invite user to organisation fails")
def test_invite_user_to_organisation_fails():
    pass


@scenario("features/user.feature", "Invite user to organisation is success")
def test_invite_user_to_organisation_is_success():
    pass


@scenario("features/user.feature", "User is already invited to organisation")
def test_user_is_already_invited_to_organisation():
    pass


@scenario("features/user.feature", "Repository does not exist on github")
def test_repository_does_not_exist_on_github():
    pass


@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.gitusername = "test-username"
    user.email = "test_user@test.com"
    return user


@pytest.fixture(scope="function")
def context():
    return {}


@pytest.fixture
def labels():
    form_label = [
        {
            "action": "repository_access",
            "repository": "test-repo",
            "access_level": "merge",
        }
    ]
    return form_label


@given("A git username", target_fixture="user_name")
def user_name():
    return "test-username"


@given("User exists on github")
def user_already_exists(requests_mock):
    API_URL = "https://test-base-url.com/users/test-username"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=200,
    )

    return_value = helpers.get_user(username=user_name())
    assert return_value is True


@given("User does not exist on github")
def user_does_not_exist(requests_mock, context):
    API_URL = "https://test-base-url.com/users/test-username"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=404,
    )

    return_value = helpers.get_user(username=user_name())
    assert return_value is False
    context["expected_message"] = "User test-username not present on github."


@given("User does not exist in git org")
def user_does_not_exist_in_org(requests_mock):
    API_URL = "https://test-base-url.com/orgs/test-org/members/test-username"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=200,
    )

    return_value = helpers.get_org(username=user_name())
    assert return_value is False


@given("User exists in git org")
def user_exists_in_org(requests_mock):
    API_URL = "https://test-base-url.com/orgs/test-org/members/test-username"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=204,
    )

    return_value = helpers.get_org(username=user_name())
    assert return_value is True


@given("User is invited to org")
def user_invited(requests_mock, context):
    API_URL = "https://test-base-url.com/orgs/test-org/invitations"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=200,
        json=[{"login": "test-username"}],
    )

    return_value = helpers.get_org_invite(username=user_name())
    assert return_value is True
    context["expected_message"] = (
        "User test-username has already been invited to join github org."
        " Accept invite to continue.."
    )


@given("User is not invited to org")
def user_not_invited(requests_mock):
    API_URL = "https://test-base-url.com/orgs/test-org/invitations"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=200,
        json=[{"login": ""}],
    )

    return_value = helpers.get_org_invite(username=user_name())
    assert return_value is False


@given("User cannot be added to the org")
def cannot_add_user_to_org(requests_mock, context):
    API_URL = "https://test-base-url.com/orgs/test-org/memberships/test-username"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.put(
        API_URL,
        headers=expected_headers,
        status_code=404,
    )

    return_value = helpers.put_user(username=user_name())
    assert return_value is False
    context["expected_message"] = "Failed to add user test-username to github org"


@given("User can be added to the org")
def add_user_to_org(requests_mock, context):
    API_URL = "https://test-base-url.com/orgs/test-org/memberships/test-username"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.put(
        API_URL,
        headers=expected_headers,
        status_code=200,
    )

    return_value = helpers.put_user(username=user_name())
    assert return_value is True
    context["expected_message"] = (
        "Invited user test-username to join github org."
        " Access can be granted post inivation acceptance."
    )


@given("Repository does not exist on github")
def repo_does_not_exist(requests_mock, context):
    API_URL = "https://test-base-url.com/repos/test-repo"
    expected_headers = {"Authorization": "token test-token"}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=404,
    )

    return_value = helpers.get_repo("test-repo")
    assert return_value is False
    context["expected_message"] = "Repository test-repo does not exist"


@when("I pass approval request", target_fixture="context_output")
def add_user_approve(user, labels):
    github_access = access.get_object()
    return github_access.approve(user, labels, "test-approver", "123")


@then("return value should be False")
def false_output(context_output, context):
    return_value = context_output[0]
    message = context_output[1]
    assert return_value is False
    assert message == context["expected_message"]
