"""GithubAccess Grant feature tests."""

import pytest
from BrowserStackAutomation.settings import ACCESS_MODULES
from pytest_bdd import given, scenario, then, when
from .. import access
from .. import helpers
import json

@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.gitusername = "test-username"
    user.email = "test_user@test.com"
    return user

@pytest.fixture(scope='function')
def context():
    return {}

@pytest.fixture(autouse=True)
def setup_test_config():
  ACCESS_MODULES["github_module"]["GITHUB_TOKEN"] = "test-token"
  ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"] = "https://test-base-url.com"
  ACCESS_MODULES["github_module"]["GITHUB_ORG"] = "test-org"

@scenario('features/approve.feature', 'Grant Merge Access Success')
def test_grant_merge_access_success():
    pass

@scenario('features/approve.feature', 'Grant Push Access Success')
def test_grant_push_access_success():
    pass

@scenario('features/approve.feature', 'Grant Access Fails')
def test_grant_access_fails():
    pass

@given('A git username', target_fixture="user_name")
def user_name():
    return "test-username"

@given('User exists on github')
def user_already_exists(requests_mock):

    API_URL = f'https://test-base-url.com/users/test-username'
    expected_headers = {'Authorization': 'token test-token'}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=200,
    )

    return_value = helpers.get_user(username=user_name())
    assert return_value == True

@given('User exists in git org')
def user_exists_in_org(requests_mock):
    API_URL = f'https://test-base-url.com/orgs/test-org/members/test-username'
    expected_headers = {'Authorization': 'token test-token'}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=204,
    )

    return_value = helpers.get_org(username=user_name())
    assert return_value == True

@given('Repository exists on github')
def repo_exists(requests_mock):
    API_URL = f'https://test-base-url.com/repos/test-repo'
    expected_headers = {'Authorization': 'token test-token'}

    requests_mock.get(
        API_URL,
        headers=expected_headers,
        status_code=200,
    )

    return_value = helpers.get_repo('test-repo')
    assert return_value == True

@given('Access cannot be granted to user for push')
def access_grant_push_fail(requests_mock, context):
    requests_mock.put(
        f'https://test-base-url.com/repos/test-repo/collaborators/test-username',
        headers={'Authorization': 'token test-token'},
        status_code=404,
    )
    return_value = helpers.grant_access('test-repo', 'push', user_name())
    assert return_value == False
    context['expected_message'] = "Failed adding access for user test-username to repo test-repo"

@given('Access can be granted to user for push')
def access_grant_push(requests_mock):
    requests_mock.put(
        f'https://test-base-url.com/repos/test-repo/collaborators/test-username',
        headers={'Authorization': 'token test-token'},
        json=json.dumps({'permission': "push"}),
    )
    return_value = helpers.grant_access('test-repo', 'push', user_name())
    assert return_value == True

@given('Access can be granted to user for merge')
def access_grant_merge(requests_mock):

    requests_mock.get(
        f'https://test-base-url.com/repos/test-repo/branches/master/protection/restrictions/users',
        headers={'Authorization': 'token test-token',
                 'Accept': 'application/vnd.github.v3+json',
                 'Content-Type': 'application/json'},
        status_code=200,
        json=[
          {
            "login": "test-username",
            "type": "User",
          }
        ],
    )

    requests_mock.get(
        f'https://test-base-url.com/repos/test-repo/branches/master/protection',
        headers={'Authorization': 'token test-token',
                 'Accept': 'application/vnd.github.v3+json'},
        status_code=200,
        json={
            "required_pull_request_reviews": {
              "url": "test-url-1",
              "require_code_owner_reviews": True,
              "required_approving_review_count": 2,
              "require_last_push_approval": True
            },
            "restrictions": {
              "url": "test-url-2",
            },
        },
    )

    requests_mock.post(
        f'https://test-base-url.com/repos/test-repo/branches/master/protection/restrictions/users',
        headers={'Authorization': 'token test-token','Accept': 'application/vnd.github.v3+json','Content-Type': 'application/json'},
        json=json.dumps(["Response [200]"]),
    )

    return_value = helpers.grant_access('test-repo', 'merge', user_name())
    assert return_value == True

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

@when('I pass approval request', target_fixture="context_output")
def add_user_approve(user, labels):
    github_access = access.get_object()
    return github_access.approve(user, labels, "test-approver", "123")

@pytest.fixture
def push_labels():
    form_label = [
        {
            "action": "repository_access",
            "repository": "test-repo",
            "access_level": "push",
        }
    ]
    return form_label

@when('I pass approval request for push', target_fixture="context_output")
def push_approve(user, push_labels):
    github_access = access.get_object()
    return github_access.approve(user, push_labels, "test-approver", "123")

@then('return value should be False')
def false_output(context_output, context):
    return_value = context_output[0]
    message = context_output[1]
    assert return_value == False
    assert message == context['expected_message']

@then('return value should be True')
def true_output(context_output):
    return_value = context_output[0]
    assert return_value == True