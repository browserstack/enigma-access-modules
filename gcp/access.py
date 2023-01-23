from Access.access_modules.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES
from . import helpers
import logging

logger = logging.getLogger(__name__)

class GCPAccess():
  GROUP_ACCESS = "GroupAccess"
  def email_targets(self, user):
    return [ user.email ] + self.grant_owner()

  def fetch_access_request_form_path(self):
    return 'gcp_access/accessRequest.html'

  def access_types(self):
    return []

  def get_label_desc(self, access_label):
    if access_label["action"] == self.GROUP_ACCESS:
      return access_label['action'] + ' for groups: ' + ", ".join(access_label['groups'])
    return ""
  
  def combine_labels_desc(self, access_labels):
    label_desc_array = [self.get_label_desc(access_label) for access_label in access_labels]
    return ", ".join(label_desc_array)
  
  def get_label_meta(self, access_label):
    return access_label

  
  def validate_request(self, access_labels_data, request_user, is_group=False):
    try:
      valid_access_label_array = []
      for access_label_data in access_labels_data:
        valid_access_label = {"action": access_label_data["action"], "domain": access_label_data["domain"], "groups": access_label_data["groups"]}
        valid_access_label_array.append(valid_access_label)
      
      return valid_access_label_array
    except:
      raise Exception("AccessLabel doesn't have required params for GCP access.")

  def approve(self, user, labels, approver, request, is_group=False, auto_approve_rules=None):
    label_desc = self.combine_labels_desc(labels)
    for label in labels:
      for group in label["groups"]:
        result, exception = helpers.grant_gcp_access(group, label["domain"], user.email)
        if(result == False):
          logger.error(f"Something went wrong while adding the {user.email} to group {group}: {str(exception)}")
          return False

    email_body = f"Access successfully granted for GCP Group: {label_desc} to {user.email}.<br>Request has been approved by {approver}."
    email_subject = f"Approved Access: {request.request_id} for access to {label_desc} for user {user.email}"

    email_targets = self.email_targets(user)
    
    try:
      emailSES(email_targets, email_subject, email_body)
      return True
    except Exception as e:
      logger.error("Could not send email for error %s", str(e))
      return False
  
  def revoke(self, user, label, request):
    for group in label["groups"]:
      result, exception = helpers.revoke_gcp_access(group, label["domain"], user.email)
      if not result:
        logger.error(f"Error while removing the user from the group {group}: {str(exception)}")
        return False
    
    label_desc = self.get_label_desc(label)
    email_targets = self.email_targets(user)
    email_subject = "Revoke Request: %s for %s" % ( label_desc, user.email )
    email_body = ""
    try:
      emailSES(email_targets, email_subject, email_body)
      return True
    except Exception as e:
      logger.error("Could not send email for error %s", str(e))
      return False
  
  def access_request_data(self, request, is_group=False):
    return {"domains": helpers.get_gcp_domains()}

  def access_desc(self):
    return "GCP Group Access"

  def tag(self):
    return 'gcp_access'

def get_object():
  return GCPAccess()
