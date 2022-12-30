import pytest

from Access.aws_access import constants, helpers, access

class MockBoto3:
    def add_user_to_group(self, GroupName, UserName):
        pass

    def remove_user_to_group(self, GroupName, UserName):
        pass


class MockBoto3withException:
    def add_user_to_group(GroupName, UserName):
        raise Exception

    def remove_user_to_group(GroupName, UserName):
        raise Exception


def test_get_aws_credentails(*args, **kwargs):
    value = helpers.get_aws_credentails("test")
    assert value == {}

@pytest.mark.parametrize(
    """test_name, user_email, label, expected_return_value, boto3_client""",
    [
        (
            "Grant AWS access - Success",
            "test@example.com",
            {
                "action": constants.AWS_ACCESS,
                "account": "test",
                "group": "test"
            },
            True,
            MockBoto3(),
        ),
        (
            "Grant AWS access - Failure",
            "test@example.com",
            {
                "action": constants.AWS_ACCESS,
                "account": "test",
                "group": "test"
            },
            False,
            MockBoto3withException(),
        ),
    ],
)
def test_grant_aws_access(
    mocker, test_name, user_email, label, expected_return_value, boto3_client
):
    
    userMock = mocker.MagicMock()
    userMock.email = user_email

    mockAccessModule = mocker.MagicMock()
    mockAccessModule.get_aws_client.return_value = boto3_client
    
    mocker.patch("bootprocess.general.emailSES", return_value="")

    return_value = helpers.grant_aws_access(user=userMock, label=label)
    assert return_value == expected_return_value


@pytest.mark.parametrize(
    """test_name, user_email, label, expected_return_value, boto3_client""",
    [
        (
            "Revoke AWS access - Success",
            "test@example.com",
            {
                "action": constants.AWS_ACCESS,
                "account": "test",
                "group": "test"
            },
            True,
            MockBoto3(),
        ),
        (
            "Revoke AWS access - Failure",
            "test@example.com",
            {
                "action": constants.AWS_ACCESS,
                "account": "test",
                "group": "test"
            },
            False,
            MockBoto3withException(),
        ),
    ],
)
def test_revoke_aws_access(
    mocker, test_name, user_email, label, expected_return_value, boto3_client
):
    
    userMock = mocker.MagicMock()
    userMock.email = user_email

    mockAccessModule = mocker.MagicMock()
    mockAccessModule.get_aws_client.return_value = boto3_client
    
    mocker.patch("bootprocess.general.emailSES", return_value="")
    
    return_value = helpers.revoke_aws_access(user=userMock, label=label)
    assert return_value == expected_return_value



@pytest.mark.parametrize(
    """test_name, user_email, label_desc, label_meta, approver_email, request_id, expected_return_value""",
    [
        (
            "Send Approved Email",
            "user@example.com",
            "label_desc",
            "label_meta",
            "approver@example.com",
            "request_id",
            True,
        ),
    ],
)
def test_send_approved_email(
    mocker,
    test_name,
    user_email,
    label_desc,
    label_meta,
    approver_email,
    request_id,
    expected_return_value,
):
    
    userMock = mocker.MagicMock()
    userMock.email = user_email
    
    approverMock = mocker.MagicMock()
    approverMock.email = approver_email
    
    mocker.patch("bootprocess.general.emailSES", return_value="")
    
    return_value = helpers.send_approved_email(
        userMock, label_desc, label_meta, approverMock, request_id, auto_approve_rules = None
    )
    assert return_value == expected_return_value


def test_AWSAccess(mocker):
    aws_access = access.AWSAccess()

    assert type(aws_access.grant_owner()) == list
    assert type(aws_access.revoke_owner()) == list
    assert type(aws_access.access_mark_revoke_permission()) == list
    assert type(aws_access.email_targets()) == list

    userMock = mocker.MagicMock()
    userMock.email = "test@example.com"
    userMock.username = "user"

    requestMock = mocker.MagicMock()
    requestMock.user = userMock


    label_1 = {
        "action": constants.GROUP_ACCESS,
        "account": "test 1",
        "group": "test 1"
    }
    label_2 = {
        "action": constants.GROUP_ACCESS,
        "account": "test 2",
        "group": "test 2"
    }
    label_desc = aws_access.get_label_desc(access_label=label_1)
    assert label_desc == "GroupAccess for group: test 1"

    combined_label_desc = aws_access.combine_labels_desc(access_labels=[label_1, label_2])
    assert combined_label_desc == "GroupAccess for group: test 1, GroupAccess for group: test 2"

    label_meta = aws_access.get_label_meta(access_label=label_1)
    assert label_meta == label_1
    
    expected_combined_meta = {
        "action": constants.GROUP_ACCESS,
        "account": label_1["account"] + ", " + label_2["account"],
        "group": label_1["group"] + ", " + label_2["group"],
    }
    combined_label_meta = aws_access.combine_labels_meta(access_labels=[label_1, label_2])
    assert combined_label_meta == expected_combined_meta

    assert type(aws_access.access_request_data("test")) == dict
    assert aws_access.get_extra_fields() == []
    assert aws_access.validate_request(label_1, None) == label_1

    mocker.patch("aws_access.helpers.grant_aws_access", return_value=(True, ""))
    mocker.patch("aws_access.helpers.revoke_aws_access", return_value=(True, ""))
    mocker.patch("aws_access.helpers.send_approved_email", return_value=True)

    return_value, error = aws_access.approve(
        user=None, labels=[label_1], approver=None, request_id="request_id"
    )
    assert return_value == True
    assert error == ""

    return_value, error = aws_access.revoke(
        user=None, labels=[label_1]
    )
    assert return_value == True
    assert error == ""

    data = {
        "approvers": {
            "primary": "primary",
            "others": "other"
        },
        "requestId": "requestId",
        "request_data": {},
        "is_group": False,
    }
    response = aws_access.fetch_access_approve_email(request=requestMock, data=data)
    assert type(response) == str
