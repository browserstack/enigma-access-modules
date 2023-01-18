from Access.access_modules.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES
from gcp import helper
import logging

logger = logging.getLogger(__name__)

class GCPAccess(BaseEmailAccess):
  GROUP_ACCESS = "GroupAccess"
  def email_targets(self, user):
    return [ user.email ] + self.grant_owner()

  def fetch_access_request_form_path():
    return 'gcp_access/accessRequest.html'

  def get_label_desc(self, access_label):
    if access_label["action"] == self.GROUP_ACCESS:
      return access_label['action'] + ' for group: ' + access_label['group']
    return ""
  
  def combine_labels_desc(self, access_labels):
    label_desc_array = [self.get_label_desc(access_label) for access_label in access_labels]
    return ", ".join(label_desc_array)
  
  def get_label_meta(self, access_label):
    return access_label

  
  def validate_request(self, access_labels_data, request_user, is_group=False):
    valid_access_label_array = []
    for access_label_data in access_labels_data:
      valid_access_label = {"data": access_label_data, "account": access_label_data["account"], "group": access_label_data["group"]}
      valid_access_label_array.append(valid_access_label)
    
    return valid_access_label_array

  def approve(self, user, labels, approver, request, is_group=False, auto_approve_rules=None):
    label_desc = self.combine_labels_desc(labels)
    for label in labels:
      result = helper.grant_gcp_access(label["group"], user.email)
      if(result == False):
        return False

    email_body = f"Access successfully granted for GCP Group: {label_desc} to {user.email}.<br>Request has been approved by {approver}."
    email_subject = f"Approved Access: {request.request_id} for access to {label_desc} for user {user.email}"

    email_targets = self.email_targets()
    
    try:
      emailSES(email_targets, email_subject, email_body)
    except Exception as e:
      logger.error("Could not send email for error %s", str(e))
      return False
    
    return True
  
  def revoke(self, user, label, request):
    result = helper.revoke_gcp_access(label["group"], user.email)
    return result

  def access_desc(self):
    return "GCP Group Access"

  def tag(self):
    return 'gcp_access'
