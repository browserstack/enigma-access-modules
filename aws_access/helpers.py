import boto3
import logging

from BrowserStackAutomation.settings import data as CONFIG
from . import constants


logger = logging.getLogger(__name__)


def aws_account_exists(account):
    if not _get_aws_credentails(account):
        return False
    return True

def aws_group_exists(account, group):
    client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
    try:
        client.get_group(GroupName=group)
    except Exception as e:
        logger.error(str(e))
        return False
    return True

def _get_aws_credentails(account):
    accounts = CONFIG.get("aws_accounts", [])
    for account_data in accounts:
        if account_data["account"] == account:
            return dict(
                {
                    "access_key_id": account_data["access_key_id"],
                    "access_secret_key": account_data["access_secret_key"]
                }
            )
    return dict()


def get_aws_client(account, resource):
    creds = _get_aws_credentails(account=account)
    return boto3.client(resource, **creds)


def grant_aws_access(user, label):
    try:
        if label["action"] == constants.GROUP_ACCESS:
            client = get_aws_client(account=label["account"], resource=constants.IAM_RESOURCE)
            client.add_user_to_group(GroupName=label["group"], UserName=user.email)
        else:
            return False
    except Exception as e:
        logger.error(str(e))
        return False, str(e)
    return True, ""

def revoke_aws_access(user, label):
    try:
        if label["action"] == constants.GROUP_ACCESS:
            client = get_aws_client(account=label["account"], resource=constants.IAM_RESOURCE)
            client.remove_user_from_group(GroupName=label["group"], UserName=user.email)
        else:
            return False
    except Exception as e:
        logger.error(str(e))
        return False, str(e)
    return True, ""

def get_aws_accounts():
    accounts = CONFIG.get("aws_accounts", [])
    account_names = []
    for account in accounts:
        account_names.append(account["account"])
    return account_names

def get_aws_groups(account, marker):
    client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
    return client.list_groups(Marker=marker)
