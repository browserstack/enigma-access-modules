import pytest
from . import helpers
from . import access


class MockGoogleClient:
    def groups(self):
        return MockGroups()

    def members(self):
        return MockMembers()


class MockGoogleClientWithException:
    def groups(self):
        raise Exception

    def members(self):
        raise Exception


class MockMembers:
    def delete(self, groupKey, memberKey):
        return MockExecute()

    def insert(self, groupKey, body):
        return MockExecute()


class MockGroups:
    def list(self, domain, pageToken):
        return ""


class MockExecute:
    def execute(self):
        return ""


@pytest.mark.parametrize(
    """test_name, user_email, group_id, domain_id, expected_return_value, google_client""",
    [
        (
            "Grant GCP access - Success",
            "test@example.com",
            "group@example.com",
            "example.com",
            True,
            MockGoogleClient(),
        ),
        (
            "Grant GCP access - Failure",
            "test@example.com",
            "group@example.com",
            "example.com",
            False,
            MockGoogleClientWithException(),
        ),
    ],
)
def test_grant_gcp_access(
    mocker,
    test_name,
    user_email,
    group_id,
    domain_id,
    expected_return_value,
    google_client,
):
    mocker.patch("gcp.helpers.get_gcp_client", return_value=google_client)
    result, _ = helpers.grant_gcp_access(group_id, domain_id, user_email)
    assert result == expected_return_value


@pytest.mark.parametrize(
    """test_name, user_email, group_id, domain_id, expected_return_value, google_client""",
    [
        (
            "Grant GCP access - Success",
            "test@example.com",
            "group@example.com",
            "example.com",
            True,
            MockGoogleClient(),
        ),
        (
            "Grant GCP access - Failure",
            "test@example.com",
            "group@example.com",
            "example.com",
            False,
            MockGoogleClientWithException(),
        ),
    ],
)
def test_revoke_gcp_access(
    mocker,
    test_name,
    user_email,
    group_id,
    domain_id,
    expected_return_value,
    google_client,
):
    mocker.patch("gcp.helpers.get_gcp_client", return_value=google_client)
    result, _ = helpers.revoke_gcp_access(group_id, domain_id, user_email)
    assert result == expected_return_value


def test_GCPAccess(mocker):
    userMock = mocker.MagicMock()
    userMock.email = "test@example.com"
    userMock.username = "user"

    request = mocker.MagicMock()
    request.request_id = "123"

    gcp_access = access.get_object()

    # assert type(gcp_access.email_targets(userMock)) == list

    form_label = [
        {
            "action": "GroupAccess",
            "domain": "example.com",
            "group": "group@example.com",
        }
    ]

    label = gcp_access.validate_request(form_label, userMock)

    assert label == [form_label[0]]

    label_desc = gcp_access.get_label_desc(label[0])
    assert label_desc == "GroupAccess for group: " + form_label[0]["group"]

    combine_label_desc = gcp_access.combine_labels_desc(label)
    assert combine_label_desc == "GroupAccess for group: " + form_label[0]["group"]

    mocker.patch("gcp.helpers.get_gcp_client", return_value=MockGoogleClient())
    result = gcp_access.approve(userMock, label, "test", request)
    assert result is True

    result = gcp_access.revoke(userMock, label[0], request)
    assert result is True
