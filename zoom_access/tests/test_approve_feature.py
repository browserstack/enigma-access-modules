"""ZoomAccess Grant feature tests."""

import json
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from .. import access
from .. import helper


@pytest.fixture(autouse=True)
def setup_test_config(mocker):
    mocker.patch(
        "Access.access_modules.zoom_access.helper._get_api_key",
        return_value="test-token"
    )
    mocker.patch(
        "Access.access_modules.zoom_access.helper._get_zoom_api_base_url",
        return_value="https://test-base-url.com/"
    )
    mocker.patch(
        "Access.access_modules.zoom_access.helper._get_zoom_client_secret",
        return_value="test-org"
    )


@scenario("features/approve.feature", "Grant Access Fails")
def test_zoom_grant_access_fails():
    """Grant Access Fails."""
    pass


@scenario("features/approve.feature", "Grant Pro License Access Success")
def test_zoom_grant_pro_license_access_success():
    """Grant Pro License Access Success."""
    pass


@scenario("features/approve.feature", "Grant Standard Access Success")
def test_zoom_grant_standard_access_success():
    """Grant Standard Access Success."""
    pass


@given("Access can be granted to user for Pro access")
def access_grant_standard_access(requests_mock, mocker):
    mocker.patch(
        'Access.access_modules.zoom_access.helper.get_token',
        return_value="test-token"
    )
    requests_mock.get(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
        status_code=200,
    )

    requests_mock.patch(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
        json=json.dumps({"type": 2}),
        status_code=204,
    )
    return_value = helper.update_user(user_email(), 2)
    assert return_value[0] == 204


@given("Access can be granted to user for Standard access")
def access_grant_standard_access(requests_mock, mocker):
    mocker.patch(
        'Access.access_modules.zoom_access.helper.get_token',
        return_value="test-token"
    )
    requests_mock.get(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
        status_code=200,
    )

    requests_mock.patch(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
        json=json.dumps({"type": 1}),
        status_code=204,
    )
    return_value = helper.update_user(user_email(), 1)
    assert return_value[0] == 204


@given("User exists on zoom")
def user_already_exists(requests_mock, mocker):
    mocker.patch(
        'Access.access_modules.zoom_access.helper.get_token',
        return_value="test-token"
    )
    api_url = "https://test-base-url.com/users/" + user_email()
    expected_headers = {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json",
    }

    requests_mock.get(
        api_url,
        headers=expected_headers,
        status_code=200,
    )

    return_value = helper.get_user(user_email())
    assert return_value[0] == 200


@given("Access cannot be granted to user for Standard access")
def access_grant_standard_access_fail(requests_mock, mocker):
    mocker.patch(
        'Access.access_modules.zoom_access.helper.get_token',
        return_value="test-token"
    )
    requests_mock.get(
        "https://test-base-url.com/users/" + user_email(),
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
        status_code=404,
    )

    requests_mock.post(
        "https://test-base-url.com/users/",
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        },
        json=json.dumps({
            'action': 'create',
            'user_info': {
                'email': user_email(),
                'first_name': user_name(),
                'type': 1
            }
        }),
        status_code=404,
    )
    return_value = helper.create_user(user_email(), 1, user_name())
    assert return_value[0] == 404


@given("an user email", target_fixture="user_email")
def user_email():
    """an user email."""
    return "invalid@nonexistent.com"


def user_name():
    """user name mock value"""
    return "invalid_username"


@pytest.fixture
def standard_labels():
    form_label = [
        {
            "action": "zoom_access",
            "access_type": "Standard License",
        }
    ]
    return form_label


@pytest.fixture
def pro_labels():
    form_label = [
        {
            "action": "zoom_access",
            "access_type": "Pro License",
        }
    ]
    return form_label


@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.email = user_email()
    return user


@pytest.fixture
def user_identity_1(mocker):
    user_identity_1 = mocker.MagicMock()
    user_1 = mocker.MagicMock()
    user_1.email = user_email()
    user_1.name = user_name()
    user_1.access.access_tag = "zoom_access"
    user_1.access.access_label = {"access_type": "Pro License"}
    user_identity_1.user = user_1
    return user_identity_1


@pytest.fixture
def user_identity_2(mocker):
    user_identity_2 = mocker.MagicMock()
    user_2 = mocker.MagicMock()
    user_2.email = user_email()
    user_2.name = user_name()
    user_2.access.access_tag = "zoom_access"
    user_2.access.access_label = {"access_type": "Standard Licence"}
    user_identity_2.user = user_2
    return user_identity_2


@when("I pass approval request for Pro access", target_fixture="context_output")
def pro_approve(user_identity_1, standard_labels, user, mocker):
    mocker.patch(
        "Access.access_modules.zoom_access.access.Zoom._Zoom__send_approve_email",
        return_value=True
    )
    zoom_access = access.get_object()
    return zoom_access.approve(user_identity_1, standard_labels, "test-approver", user)


@when("I pass approval request for Standard access", target_fixture="context_output")
def standard_approve(user_identity_2, pro_labels, user, mocker):
    mocker.patch(
        "Access.access_modules.zoom_access.access.Zoom._Zoom__send_approve_email",
        return_value=True
    )
    zoom_access = access.get_object()
    return zoom_access.approve(user_identity_2, pro_labels, "test-approver", user)


@then("return value should be False")
def false_output(context_output):
    return_value = context_output[0]
    assert return_value is False


@then("return value should be True")
def true_output(context_output):
    return_value = context_output[0]
    assert return_value is True
