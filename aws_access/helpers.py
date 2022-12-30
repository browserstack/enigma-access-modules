import boto3
import json
import logging
import os
from django.template import Template, Context

from bootprocess.general import emailSES
from Access.aws_access import constants


logger = logging.getLogger(__name__)
send_approved_email_template_path = os.path.join(
    os.path.dirname(__file__), 'templates', 'approved_email_template.html.j2'
)


def aws_account_exists(account):
    if not get_aws_credentails(account):
        return False
    return True

def get_aws_credentails(account):
    with open('config.json') as data_file:
        data = json.load(data_file)
        return data.get("aws_accounts", {}).get(account) or dict()


def get_aws_client(account, resource):
    creds = get_aws_credentails(account=account)
    return boto3.client(resource, **creds)


def grant_aws_access(user, label):
    try:
        if label["action"] == constants.GROUP_ACCESS:
            client = get_aws_client(account=label["account"], resource=constants.IAM_RESOURCE)
            client.add_user_to_group(GroupName=label["group"], UserName=user.email)
    except Exception as e:
        logger.error(str(e))
        return False
    return True

def revoke_aws_access(user, label):
    try:
        if label["action"] == constants.GROUP_ACCESS:
            client = get_aws_client(account=label["account"], resource=constants.IAM_RESOURCE)
            client.remove_user_from_group(GroupName=label["group"], UserName=user.email)
    except Exception as e:
        logger.error(str(e))
        return False
    return True

def get_aws_groups(account):
    client = get_aws_client(account=account, resource=constants.IAM_RESOURCE)
    return client.list_groups()['Groups']


def send_approved_email(
    user, label_desc, label_meta, approver, request_id,auto_approve_rules = None
):
    template = Template(open(send_approved_email_template_path, "r").read())
    context = Context({
        "request_id": request_id,
        "approver": approver,
        "user_email": user.email,
        "access_desc": label_desc,
        "access_meta": label_meta
    })

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

    email_body = template.render(context)

    try:
        emailSES(email_targets, email_subject, email_body)
        return True
    except Exception as e:
        logger.error("Could not send email for error %s", str(e))
        return False
