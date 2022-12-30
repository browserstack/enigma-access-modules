import json
from django.shortcuts import render
from BrowserStackAutomation.settings import ACCESS_APPROVE_EMAIL
from . import helpers, constants
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AWSAccess(object):
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
        for label in labels:
            return_value, exception = helpers.grant_aws_access(user, label["account"], label["group"])

        helpers.send_approved_email(
            user=user,
            label_desc=self.combine_labels_desc(labels),
            label_meta=self.combine_labels_meta(labels),
            approver=approver,
            request_id=request_id,
            auto_approve_rules=auto_approve_rules
        )
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
        request_data = {}

        with open('config.json') as data_file:
            data = json.load(data_file)
            request_data["accounts"] = list(data.get("aws_accounts", {}).keys())

        return request_data

    def revoke(self, user, label):
        logger.info(f'[{datetime.now().strftime("%Y-%m-%d")}] [aws] Revoke Started({user.email}) : {label}')
        is_revoked = helpers.revoke_aws_access(user.user, label)
        logger.info(f'[{datetime.now().strftime("%Y-%m-%d")}] [aws] Revoke Result({user.email}) : {is_revoked}')
        return is_revoked, ""
    
    def get_extra_fields(self):
        return []
    
    def validate_request(self, access_labels_data, request_user, is_group=False):
        return access_labels_data
    
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
        return "AWS Access"

    def match_keywords(self):
        return  ['aws','amazon','web','services','console','cloud']

    def tag(self):
        return 'aws_access'

def get_object():
    return AWSAccess()
