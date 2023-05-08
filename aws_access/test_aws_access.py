"""aws access module unit tests"""
import pytest

from . import constants, helpers, access


class MockBoto3:
    """Mock for boto3"""

    # Follows boto3 signature
    def add_user_to_group(self, GroupName, UserName):
        """mock method"""

    def remove_user_from_group(self, GroupName, UserName):
        """mock method"""

    def list_groups(self, marker=None):
        """mock method returns group list"""
        return {
            "Groups": [
                {
                    "Path": "/",
                    "GroupName": "Group 1",
                    "GroupId": "1",
                    "Arn": "Group1",
                    "CreateDate": "2023-01-01",
                },
                {
                    "Path": "/",
                    "GroupName": "Group 2",
                    "GroupId": "2",
                    "Arn": "Group2",
                    "CreateDate": "2023-01-01",
                },
            ],
            "IsTruncated": False,
            "Marker": None,
        }


class MockBoto3withException(MockBoto3):
    """Mock for Boto3 exception"""

    # Follows boto3 signature
    def add_user_to_group(self, GroupName, UserName):
        """mock method raises exception"""
        raise Exception

    def remove_user_from_group(self, GroupName, UserName):
        """mock method raises exception"""
        raise Exception


def test_get_aws_credentails(*args, **kwargs):
    """mock function raises exception"""
    value = helpers._get_aws_credentails("test")
    assert isinstance(value, dict)


@pytest.mark.parametrize(
    """test_name, user_email, label, expected_return_value, boto3_client""",
    [
        (
            "Grant AWS access - Success",
            "test@example.com",
            {"action": constants.GROUP_ACCESS, "account": "test", "group": "test"},
            True,
            MockBoto3(),
        ),
        (
            "Grant AWS access - Failure",
            "test@example.com",
            {"action": constants.GROUP_ACCESS, "account": "test", "group": "test"},
            False,
            MockBoto3withException(),
        ),
    ],
)
def test_grant_aws_access(
    mocker, test_name, user_email, label, expected_return_value, boto3_client
):
    """unit test for grant_aws_access"""
    user_mock = mocker.MagicMock()
    user_mock.email = user_email

    mocker.patch(
        "Access.access_modules.aws_access.helpers.get_aws_client",
        return_value=boto3_client,
    )
    mocker.patch("bootprocess.general.emailSES", return_value="")

    return_value, _ = helpers.grant_aws_access(
        user_mock, label["account"], label["group"]
    )
    assert return_value == expected_return_value


@pytest.mark.parametrize(
    """test_name, user_email, label, expected_return_value, boto3_client""",
    [
        (
            "Revoke AWS access - Success",
            "test@example.com",
            {"action": constants.GROUP_ACCESS, "account": "test", "group": "test"},
            True,
            MockBoto3(),
        ),
        (
            "Revoke AWS access - Failure",
            "test@example.com",
            {"action": constants.GROUP_ACCESS, "account": "test", "group": "test"},
            False,
            MockBoto3withException(),
        ),
    ],
)
def test_revoke_aws_access(
    mocker, test_name, user_email, label, expected_return_value, boto3_client
):
    """unit test for revoke_aws_access"""
    user_mock = mocker.MagicMock()
    user_mock.email = user_email

    request = mocker.MagicMock()
    request.request_id = "123"

    mocker.patch(
        "Access.access_modules.aws_access.helpers.get_aws_client",
        return_value=boto3_client,
    )

    return_value, _ = helpers.revoke_aws_access(
        user_mock, label["account"], label["group"]
    )
    assert return_value == expected_return_value


def test_aws_access(mocker):
    """unit test for aws access module methods"""
    user_mock = mocker.MagicMock()
    user_mock.email = "test@example.com"
    user_mock.username = "user"

    request_mock = mocker.MagicMock()
    request_mock.user = user_mock

    mocker.patch("Access.access_modules.aws_access.access.AWSAccess._AWSAccess__send_approve_email", return_value="")
    mocker.patch("Access.access_modules.aws_access.access.AWSAccess._AWSAccess__send_revoke_email", return_value="")
    mocker.patch(
            "Access.access_modules.aws_access.helpers.grant_aws_access",
            return_value=(True, ""))
    mocker.patch(
            "Access.access_modules.aws_access.helpers.revoke_aws_access",
            return_value=(True, ""))
    aws_access = access.AWSAccess()

    label_1 = {
        "action": constants.GROUP_ACCESS,
        "account": "test 1",
        "group": "test 1",
    }
    label_2 = {
        "action": constants.GROUP_ACCESS,
        "account": "test 2",
        "group": "test 2",
    }
    label_desc = aws_access.get_label_desc(access_label=label_1)
    assert label_desc == "GroupAccess for group: test 1"

    combined_label_desc = aws_access.combine_labels_desc(
        access_labels=[label_1, label_2]
    )
    assert (
        combined_label_desc
        == "GroupAccess for group: test 1, GroupAccess for group: test 2"
    )

    label_meta = aws_access.get_label_meta(access_label=label_1)
    assert label_meta == label_1

    expected_combined_meta = {
        "action": label_1["action"] + ", " + label_2["action"],
        "account": label_1["account"] + ", " + label_2["account"],
        "group": str(label_1["group"]) + ", " + str(label_2["group"]),
    }
    combined_label_meta = aws_access.combine_labels_meta(
        access_labels=[label_1, label_2]
    )
    assert combined_label_meta == expected_combined_meta

    assert isinstance(aws_access.access_request_data("test"), dict)
    assert aws_access.validate_request([label_1], None) == [label_1]

    return_value = aws_access.approve(user_mock, [label_1], None, request_mock)
    assert return_value is True

    return_value = aws_access.revoke(
            user_mock, mocker.MagicMock(), label_1, request_mock)
    assert return_value is True


def test_get_aws_accounts():
    """unit test for get_aws_accounts"""
    accounts = helpers.get_aws_accounts()
    assert isinstance(accounts, list)


def test_get_aws_groups(mocker):
    """unit test for get_aws_groups"""
    mocker.patch(
        "Access.access_modules.aws_access.helpers.get_aws_client",
        return_value=MockBoto3(),
    )
    group_data = helpers.get_aws_groups(account="test", marker=None)
    assert "Groups" in group_data
    assert len(group_data["Groups"]) == 2
