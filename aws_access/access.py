import json
from django.shortcuts import render
from django.template import loader
from BrowserStackAutomation.settings import ACCESS_APPROVE_EMAIL
from . import helpers, constants
from Access.access_modules.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AWSAccess(BaseEmailAccess):
    def grant_owner(self):
        return [ ACCESS_APPROVE_EMAIL ]

    def revoke_owner(self):
        return [ ACCESS_APPROVE_EMAIL ]

    def access_mark_revoke_permission(self, access_type):
        return [ ACCESS_APPROVE_EMAIL ]

    def email_targets(self, user):
        return [ user.email ] + self.grant_owner()

    def approve(self, user, labels, approver, request_id, is_group=False, auto_approve_rules = None):
        return_value = False
        exception = ""
        label_desc = self.combine_labels_desc(labels)
        label_meta = self.combine_labels_meta(labels)
        for label in labels:
            return_value, exception = helpers.grant_aws_access(user, label["account"], label["group"])

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
        email_body = self._generateStringFromTemplate("aws_access/approved_email_template.html.j2", **{
            "request_id": request_id,
            "approver": approver,
            "user_email": user.email,
            "access_desc": label_desc,
            "access_meta": label_meta
        })
        email_targets = [ user.email ]
        try:
            emailSES(email_targets, email_subject, email_body)
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))

        return return_value, exception
    
    def get_label_desc(self, access_label):
        desc = ""
        if access_label["action"] == constants.GROUP_ACCESS:
            desc = access_label['action'] + ' for group: ' + access_label['group']
        return desc

    def combine_labels_desc(self, access_labels):
        label_desc_array = [self.get_label_desc(access_label) for access_label in access_labels]
        return ", ".join(label_desc_array)

    def get_label_meta(self, access_label):
        return access_label

    def combine_labels_meta(self, access_labels):
        combined_meta = {}
        if access_labels:
            combined_meta = access_labels[0]
            for label in access_labels[1:]:
                for key, value in label.items():
                    combined_meta[key] += f", {value}"
        return combined_meta
    
    def access_request_data(self, request, is_group=False):
        request_data = {"accounts": helpers.get_aws_accounts()}
        print(request_data)
        return request_data

    def revoke(self, user, label):
        logger.info(f'[{datetime.now().strftime("%Y-%m-%d")}] [aws] Revoke Started({user.email}) : {label}')
        is_revoked, exception = helpers.revoke_aws_access(user.user, label)
        logger.info(f'[{datetime.now().strftime("%Y-%m-%d")}] [aws] Revoke Result({user.email}) : {is_revoked}')
        return is_revoked, exception
    
    def get_extra_fields(self):
        return []
    
    def validate_request(self, access_labels_data, request_user, is_group=False):
        valid_access_label_array = list()
        for access_label_data in access_labels_data:
            if not access_label_data.get("action"):
                raise Exception(constants.ERROR_MESSAGES["valid_action_required"])
            if access_label_data["action"] == constants.GROUP_ACCESS:
                if not helpers.aws_account_exists(access_label_data.get("account")):
                    raise Exception(constants.ERROR_MESSAGES["valid_account_required"])
                if not helpers.aws_group_exists(access_label_data.get("group")):
                    raise Exception(constants.ERROR_MESSAGES["valid_group_required"])
            valid_access_label = {"data" : access_label_data}
            valid_access_label_array.append(valid_access_label)
        return valid_access_label_array
    
    def fetch_access_approve_email(self, request, data):
        context_details = {
            'approvers': {
                'primary': data['approvers']['primary'],
                'other': data['approvers']['other']
            },
            'requestId': data['requestId'],
            'user': request.user,
            'requestData': data['request_data'],
            'accessType': self.tag(),
            'accessDesc': self.access_desc(),
            'isGroup': data['is_group']
        }
        return str(render(request, 'aws_access/accessApproveEmail.html', context_details).content.decode("utf-8"))

    def fetch_access_request_form_path(self):
        return 'aws_access/accessRequest.html'

    def access_desc(self):
        return "AWS Group Access"

    def match_keywords(self):
        return  ['aws','amazon','web','services','console','cloud']
    
    def tag(self):
        return 'aws_access'

    def _generateStringFromTemplate(self, filename, **kwargs):
        template = loader.get_template(filename)
        vals = {}
        for key, value in kwargs.items():
            vals[key] = value
        return template.render(vals)
    
    def access_types(self):
        return {}

def get_object():
    return AWSAccess()
