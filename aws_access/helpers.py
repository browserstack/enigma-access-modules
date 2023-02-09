"""aws helpers functions"""
import logging
import boto3

from BrowserStackAutomation.settings import ACCESS_MODULES
from . import constants


logger = logging.getLogger(__name__)


def aws_account_exists(account):
    """checks if aws account exists

    Args:
        account (str): accountname

    Returns:
        bool: True if account exists.
              False if account does not exist
    """
    if not _get_aws_credentails(account):
        return False
    return True


def aws_group_exists(account, group):
    """checks if aws group exists

    Args:
        account (str): account name
        group (str): aws group name

    Returns:
        str: True if AWS Group exists.
             False if AWS Group does not exists
    """
    client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
    try:
        client.get_group(group_name=group)
    except Exception as ex:
        logger.error(str(ex))
        return False
    return True


def _get_aws_credentails(account):
    """get aws API credentials"""
    accounts = ACCESS_MODULES["aws_access"].get("aws_accounts", [])
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
    """gets aws client for api access

    Args:
        account (str): account name
        resource (str): resource name

    Returns:
        client: aws session client
    """
    creds = _get_aws_credentails(account=account)
    return boto3.client(resource, **creds)


def grant_aws_access(user, account, group):
    """make aws api call to grant access to user to a group

    Args:
        user (str): aws user name
        account (str): aws account name
        group (str): aws group name

    Returns:
        bool: True if access grant succeeds. False if access grant fails
    """
    try:
        client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
        client.add_user_to_group(group_name=group, user_name=user.email)
    except Exception as ex:
        logger.error(str(ex))
        return False, str(ex)
    return True, ""


def revoke_aws_access(user, account, group):
    """make aws api call to revoke access to a user to a group

    Args:
        user (str): aws user name
        account (str): aws account name
        group (str): aws group name

    Returns:
        bool: True if the revoke succeeds. False if the revoke fails
    """
    try:
        client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
        client.remove_user_from_group(group_name=group, user_name=user.email)
    except Exception as ex:
        logger.error(str(ex))
        return False, str(ex)
    return True, ""


def get_aws_accounts():
    """gets the list of aws accounts

    Returns:
        list: returns list of account names
    """
    accounts = ACCESS_MODULES["aws_access"].get("aws_accounts", [])
    account_names = []
    for account in accounts:
        account_names.append(account["account"])
    return account_names


def get_aws_groups(account, marker):
    """gets the list of aws groups

    Args:
        account (str): account name
        marker (str): aws marker

    Returns:
        list: returns list of aws groups
    """
    client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
    if marker:
        return client.list_groups(Marker=marker)
    return client.list_groups()
