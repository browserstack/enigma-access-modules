import logging

from bootprocess.general import emailSES
from Access.access_modules.base_email_access.access import BaseEmailAccess
from BrowserStackAutomation.settings import ACCESS_APPROVE_EMAIL
from helpers import (
  get_info,
  invite_user,
  remove_user,
  get_workspace_list
)

logger = logging.getLogger(__name__)

class Slack(BaseEmailAccess):
    available = False

    def grant_owner(self):
        return [ ACCESS_APPROVE_EMAIL ]

    def revoke_owner(self):
        return [ ACCESS_APPROVE_EMAIL ]

    def access_mark_revoke_permission(self, access_type):
        return [ ACCESS_APPROVE_EMAIL ]

    def email_targets(self, user):
        return [ user.email ] + self.grant_owner()

    def approve(self, user, access_labels, approver, requestId, is_group=False, auto_approve_rules = None):

        label = access_labels[0]
        access_workspace = label["access_workspace"]
        team_info_list, error_message = get_info(access_workspace)
        if not team_info_list:
          logger.error(f"Error ocurred while gathering information for requested workspace {access_workspace}: {error_message}")
          return False
        if not invite_user(user.email, team_info_list['channel_id'], team_info_list['team_id'], access_workspace):
          logger.error(f"Could not invite user to requested workspace {access_workspace}. Please contact Admin.")
          return False

        email_targets = self.email_targets(user)
        email_subject = "Approved Access: %s for access to Slack Access for user %s" % ( requestId, user.email )
        email_body = "Access successfully granted for slack: Standard Access for Slack Access to %s.<br>Request has been approved by %s." % (user.email, approver)
        try:
            emailSES(email_targets, email_subject, email_body)
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
        return True

    def revoke(self, user, label):

        access_workspace = label["access_workspace"]
        response, error_message = remove_user(user.email, access_workspace)
        if not response:
          logger.error(f"Could not remove user from requested workspace {access_workspace} : {error_message}")
          return False

        label_desc = self.combine_labels_desc(label)
        email_targets = self.email_targets(user)
        email_subject = "Revoke Request: %s for %s" % (label_desc, user.email)
        email_body = ""
        try:
            emailSES(email_targets, email_subject, email_body)
            return True
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
            return False

    def get_label_desc(self, access_label):
        access_workspace = access_label["access_workspace"]
        access_type = access_label["access_type"]
        return (
            "Slack access for Workspace: "
            + access_workspace
            + ". Access Type: "
            + access_type
        )

    def combine_labels_desc(self, access_labels):
        label_descriptions_set = set()
        for access_label in access_labels:
            label_desc = self.get_label_desc(access_label)
            label_descriptions_set.add(label_desc)

        return ", ".join(label_descriptions_set)

    def validate_request(self, labels, user, is_group=False):

        valid_access_label_array = []
        for label in labels:
            valid_access_label = {
                "access_workspace": label["slackAccessWorkspace"],
                "access_type": label["slackAccessType"],
            }
            valid_access_label_array.append(valid_access_label)

        return valid_access_label_array

    def access_request_data(self, request, is_group=False):
        workspace_data = [workspace for workspace in get_workspace_list()]
        data = {'slackWorkspaceList': workspace_data}
        return data

    def access_types(self):
        return [{
            "type": "StandardAccess",
            "desc": "Standard Access"
        }]

    def access_desc(self):
        return "Slack Access"

    def tag(self):
        return 'slack'

def get_object():
    return Slack()
