"""aws helpers functions"""
import logging
import boto3

from enigma_automation.settings import ACCESS_MODULES
from . import constants

logger = logging.getLogger(__name__)


def aws_account_exists(account):
    """Checks if AWS Account exists.

    Args:
        account (str): AWS Account Name.

    Returns:
        bool: True if account exists.
              False if account does not exist.
    """
    if not _get_aws_credentails(account):
        return False
    return True


def aws_group_exists(account, group):
    """Checks if aws group exists.

    Args:
        account (str): AWS Account name.
        group (str): AWS Group name.

    Returns:
        str: True if AWS Group exists.
             False if AWS Group does not exists.
    """
    client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
    try:
        client.get_group(GroupName=group)
    except Exception as ex:
        logger.error(str(ex))
        return False
    return True


def _get_aws_config():
    """ Gets AWS config. """

    return ACCESS_MODULES.get("aws_access", {})


def _get_aws_credentails(account):
    """Get AWS API credentials."""
    aws_access_config = _get_aws_config()
    accounts = aws_access_config.get("aws_accounts", [])
    for account_data in accounts:
        if account_data["account"] == account:
            return dict(
                {
                    "aws_access_key_id": account_data["access_key_id"],
                    "aws_secret_access_key": account_data["secret_access_key"],
                }
            )
    return {}


def get_aws_client(account, resource):
    """Gets AWS client for api access.

    Args:
        account (str): AWS Account Name.
        resource (str): Resource Name.

    Returns:
        client: AWS Session client.
    """
    creds = _get_aws_credentails(account=account)
    return boto3.client(resource, **creds)


def __get_username(email):
    return email.split("@")[0]


def grant_aws_access(user, account, group):
    """Make AWS API call to grant access to user to a group.

    Args:
        user (str): AWS User name.
        account (str): AWS Account name.
        group (str): AWS Group name.

    Returns:
        bool: True if access grant succeeds. False if access grant fails.
    """
    try:
        client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
        client.add_user_to_group(GroupName=group, UserName=__get_username(user.email))
    except Exception as ex:
        logger.exception("Exception while adding user to AWS group: " + str(ex))
        return False, str(ex)
    return True, ""


def revoke_aws_access(user, account, group):
    """Make AWS API call to revoke access to a user to a group.

    Args:
        user (str): AWS User name.
        account (str): AWS Account name.
        group (str): AWS Group name.

    Returns:
        bool: True if the revoke succeeds. False if the revoke fails.
    """
    try:
        client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
        client.remove_user_from_group(
            GroupName=group, UserName=__get_username(user.email)
        )
    except Exception as ex:
        logger.error("Exception while removing user from AWS group: " + str(ex))
        return False, str(ex)
    return True, ""


def get_aws_accounts():
    """Gets the list of AWS Accounts.

    Returns:
        list: Returns list of Account Names.
    """
    accounts = _get_aws_config().get("aws_accounts", [])
    account_names = []
    for account in accounts:
        account_names.append(account["account"])
    return account_names


def get_aws_groups(account, marker):
    """Gets the list of AWS Groups.

    Args:
        account (str): AWS Account name.
        marker (str): AWS API marker.

    Returns:
        list: Returns list of AWS Groups.
    """
    client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
    if marker:
        return client.list_groups(Marker=marker)
    return client.list_groups()
