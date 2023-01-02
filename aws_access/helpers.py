import boto3
import logging
import os

from bootprocess.general import emailSES
from BrowserStackAutomation.settings import data as CONFIG
from aws_access import constants
from Access.helpers import generateStringFromTemplate


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
    return CONFIG.get("aws_accounts", {}).get(account) or dict()


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
        return False
    return True

def revoke_aws_access(user, label):
    try:
        if label["action"] == constants.GROUP_ACCESS:
            client = get_aws_client(account=label["account"], resource=constants.IAM_RESOURCE)
            client.remove_user_from_group(GroupName=label["group"], UserName=user.email)
        else:
            return False
    except Exception as e:
        logger.error(str(e))
        return False
    return True

def get_aws_groups(account, marker):
    client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
    return client.list_groups()


def send_approved_email(
    user, label_desc, label_meta, approver, request_id,auto_approve_rules = None
):
    email_targets = [ user.email ]
    if auto_approve_rules:
        email_subject = (
            "Access Granted: %s for access to %s for user %s.<br>Request has been approved by %s. <br> Rules :- %s" % ( 
                request_id, label_desc, user.email, approver, " ,".join(auto_approve_rules)
            )
        )
    else:
        email_subject = (
            "Access Granted: %s for access to %s for user %s.<br>Request has been approved by %s." % ( 
                request_id, label_desc, user.email, approver
            )
        )
    email_body = generateStringFromTemplate("approved_email_template.html.j2", {
        "request_id": request_id,
        "approver": approver,
        "user_email": user.email,
        "access_desc": label_desc,
        "access_meta": label_meta
    })

    try:
        emailSES(email_targets, email_subject, email_body)
        return True
    except Exception as e:
        logger.error("Could not send email for error %s", str(e))
        return False
