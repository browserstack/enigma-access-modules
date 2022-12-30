import logging
import requests
from requests.auth import HTTPBasicAuth
from django.shortcuts import render
import json
from Access.helper import saveMetaData, getMetaData
from bootprocess.general import emailSES

# Need to import MAIL_APPROVER_GROUPS CONFLUENCE_BASE_URL ADMIN_EMAIL API_TOKEN etc variables

logger = logging.getLogger(__name__)

class Confluence():
  available = True
  group_access_allowed = True

  # Added this function as this class inherited from BaseEmailAccess
  def get_extra_fields(self):
    return []

  def grant_owner(self):
    return []

  def revoke_owner(self):
    return []
  
  def access_mark_revoke_permission(self, access_type):
    return []
  
  def fetch_access_request_form_path(self):
    return "confluence/access_request_form.html"

  def email_targets(self, user):
    return [ user.email ] + self.grant_owner() + MAIL_APPROVER_GROUPS
  
  def auto_grant_email_targets(self, user):
    return [ user.email ] + MAIL_APPROVER_GROUPS

  def validate_request(self, access_labels_data, request_user, is_group=False):
    access_workspace = access_labels_data[0]["accessWorkspace"]
    access_type = access_labels_data[0]["confluenceAccessType"]
    valid_access_label_array = []
    for access_label_data in access_labels_data:
        valid_access_label = {"data" : access_label_data}
        valid_access_label_array.append(valid_access_label)

    valid_access_label["access_workspace"] = access_workspace
    valid_access_label["access_type"] = access_type
    return valid_access_label_array

  def get_label_desc(self, access_label):
    access_workspace = access_label["access_workspace"]
    access_type = access_label["access_type"]
    return " Confluence access for Workspace: " + access_workspace + ". Access Type: " + access_type

  def combine_labels_desc(self,access_labels):
    label_descriptions_set = set()
    for access_label in access_labels:
      label_desc = self.get_label_desc(access_label)
      label_descriptions_set.add(label_desc)

    return ", ".join(label_descriptions_set)

  def access_types(self):
    return [ {
      "type": "View Access",
      "desc": "View Access"
    },{
      "type": "Edit Access",
      "desc": "Edit Access"
    },{
      "type": "Admin Access",
      "desc": "Admin Access"
    }]

  def approve_space_access(self, space_key, permission, subject_identifier, subject_type="user"):
    try:
      auth = HTTPBasicAuth(ADMIN_EMAIL, API_TOKEN)
      headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
      }
      payload = json.dumps({
        "subject": {
          "type": subject_type,
          "identifier": subject_identifier
        },
        "operation": permission
      })
      response = requests.request("POST", CONFLUENCE_BASE_URL+"/wiki/rest/api/space/"+space_key+"/permission", data=payload, headers=headers, auth=auth)

      if(response.status_code != 200 and response.status_code != 201):
        logger.error("Could not approve permission %s for response %s", (str(permission), response.text))
        return False
      return str(json.loads(response.text)["id"]) 
    except Exception as e:
      logger.error("Could not approve permission %s for error %s", (str(permission), str(e)))
      return False
  
  def revoke_space_access(self, space_key, permission_id):
    try:
      auth = HTTPBasicAuth(ADMIN_EMAIL, API_TOKEN)
      response = requests.request("DELETE", CONFLUENCE_BASE_URL+"/wiki/rest/api/space/"+space_key+"/permission/"+permission_id, auth=auth)
      if(response.status_code != 204):
        return False
      
      return True

    except Exception as e:
      return False

  
  def access_request_data(self, request, is_group=False):
    available_spaces = {}
    available_spaces["spaces"] = []
    auth = HTTPBasicAuth(ADMIN_EMAIL, API_TOKEN)
    start = 0
    limit = 25
    while(True):
      response = requests.request("GET", CONFLUENCE_BASE_URL+"/wiki/rest/api/space?type=global&start="+str(start)+"&limit="+str(limit)+"", auth=auth)
      spaces = json.loads(response.text)
      for space in spaces["results"]:
        available_spaces["spaces"].append({"key": space["key"], "name": space["name"]})
      start += spaces["size"]
      if(spaces["size"] < spaces["limit"]):
        break

    return available_spaces

  def get_accesses_with_type(self, access_type):
    permissions = [{"key": "read", "target": "space"}, {"key": "delete", "target": "space"}, {"key": "create", "target": "comment"}, {"key": "delete", "target": "comment"}]
    if(access_type == "Edit Access" or access_type == "Admin Access"):
      permissions.append({"key": "create", "target": "page"})
      permissions.append({"key": "create", "target": "blogpost"})
      permissions.append({"key": "create", "target": "attachment"})
      permissions.append({"key": "delete", "target": "page"})
      permissions.append({"key": "delete", "target": "blogpost"})
      permissions.append({"key": "delete", "target": "attachment"})
    
    if(access_type == "Admin Access"):
      permissions.append({"key": "export", "target": "space"})
      permissions.append({"key": "administer", "target": "space"})
      permissions.append({"key": "archive", "target": "page"})
      permissions.append({"key": "restrict_content", "target": "space"})
      
    return permissions

  
  def approve(self, user, labels, approver, requestId, is_group=False, auto_approve_rules = None):
    permissions = []
    access_type = ""
    if 'View Access' in labels["access_type"]:
      access_type = 'View Access'
      permissions = self.get_accesses_with_type('View Access')
    elif 'Edit Access' in labels["access_type"]:
      access_type = 'Edit Access'
      permissions = self.get_accesses_with_type("Edit Access")
    elif "Admin Access" in labels["access_type"]:
      access_type = "Admin Access"
      permissions = self.get_accesses_with_type["Admin Access"]
    
    approve_result = []

    for permission in permissions:
      response = self.approve_space_access(labels["access_workspace"], permission, user.confluenceId, subject_type="user")
      if((response is bool) and response == False):
        return False
      
      approve_result.append({"permission": permission, "permission_id": response})
      
    
    email_targets = self.auto_grant_email_targets(user)
    email_body = "Access successfully granted for confluence: %s for Confluence Access to %s.<br>Request has been approved by %s." % (access_type, user.email, approver)
    email_subject = "Approved Access: %s for access to %s for user %s" % ( requestId, self.access_desc(), user.email )

    try:
      emailSES(email_targets, email_subject, email_body)
      saveMetaData(user, labels, approve_result)
      return [True, approve_result]
    except Exception as e:
      logger.error("Could not send email for error %s", str(e))
      return False

  def revoke(self, user, label):
    permissions = getMetaData(user, label)

    for permission in permissions[::-1]:
      if(self.revoke_space_access(label["access_workspace"], permission["permission_id"]) == False):
        logger.error("could not revoke access for %s", str(permission))
        # Want to verify this if someone revoked access from UI of confluence when should we stop or continue
        return False
    
    label_desc = self.get_label_desc(label)
    email_targets = self.auto_grant_email_targets()
    email_subject = "Revoke Request: %s for %s" % ( label_desc, user.email )
    email_body = ""
    try:
      emailSES(email_targets, email_subject, email_body)
      return True
    except Exception as e:
      logger.error("Could not send email for error %s", str(e))
      return False
    

  def access_desc(self):
    return "Confluence Access"

  def tag(self):
    return 'confluence'

  # Added this function as this class inherited from BaseEmailAccess
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
    return str(render(request, 'base_email_access/accessApproveEmail.html', context_details).content.decode("utf-8"))

def get_object():
  return Confluence()
