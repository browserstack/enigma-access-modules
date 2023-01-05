import logging
import requests
from requests.auth import HTTPBasicAuth
import json

from bootprocess.general import emailSES
from Access.access_modules.base_email_access.access import BaseEmailAccess
from BrowserStackAutomation.settings import ACCESS_APPROVE_EMAIL, ACCESS_MODULES
from bootprocess.general import emailSES

logger = logging.getLogger(__name__)

class Confluence(BaseEmailAccess):
  def grant_owner(self):
    return [ ACCESS_APPROVE_EMAIL ]

  def revoke_owner(self):
    return [ ACCESS_APPROVE_EMAIL ]
  
  def access_mark_revoke_permission(self, access_type):
    return [ ACCESS_APPROVE_EMAIL ]
  
  def fetch_access_request_form_path(self):
    return "confluence/access_request_form.html"

  def email_targets(self, user):
    return [ user.email ] + self.grant_owner()
  
  def auto_grant_email_targets(self, user):
    return [ user.email ] + self.grant_owner()

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
    return "Confluence access for Workspace: " + access_workspace + ". Access Type: " + access_type

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

  def __approve_space_access(self, space_key, permission, subject_identifier, subject_type="user"):
    try:
      auth = HTTPBasicAuth(ACCESS_MODULES["confluence_module"]["ADMIN_EMAIL"], ACCESS_MODULES["confluence_module"]["API_TOKEN"])
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
      response = requests.request("POST", ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]+"/wiki/rest/api/space/"+space_key+"/permission", data=payload, headers=headers, auth=auth)

      if(response.status_code != 200 and response.status_code != 400):
        logger.error(f"Could not approve permission {str(permission)} for response {str(response.text)}")
        return False
      if(response.status_code == 400):
        return json.loads(response.text)["message"].split(" ")[-1]
      return str(json.loads(response.text)["id"]) 
    except Exception as e:
      logger.error(f"Could not approve permission {str(permission)} for error {str(e)}")
      return False
  
  def __revoke_space_access(self, space_key, permission_id):
    try:
      auth = HTTPBasicAuth(ACCESS_MODULES["confluence_module"]["ADMIN_EMAIL"], ACCESS_MODULES["confluence_module"]["API_TOKEN"])
      response = requests.request("DELETE", ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]+"/wiki/rest/api/space/"+space_key+"/permission/"+permission_id, auth=auth)
      if(response.status_code != 204):
        return False
      
      return True

    except Exception as e:
      logger.error(f"Could not approve permission {str(permission_id)} for error {str(e)}")
      return False

  
  def access_request_data(self, request, is_group=False):
    available_spaces = {}
    available_spaces["spaces"] = []
    auth = HTTPBasicAuth(ACCESS_MODULES["confluence_module"]["ADMIN_EMAIL"], ACCESS_MODULES["confluence_module"]["API_TOKEN"])
    start = 0
    limit = 25
    while(True):
      response = requests.request("GET", ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]+"/wiki/rest/api/space?type=global&start="+str(start)+"&limit="+str(limit)+"", auth=auth)
      spaces = json.loads(response.text)
      for space in spaces["results"]:
        available_spaces["spaces"].append({"key": space["key"], "name": space["name"]})
      start += spaces["size"]
      if(spaces["size"] < spaces["limit"]):
        break

    return available_spaces

  def __get_accesses_with_type(self, access_type):
    permissions = [{"key": "read", "target": "space"}, {"key": "delete", "target": "space"}, {"key": "create", "target": "comment"}, {"key": "delete", "target": "comment"}]
    if(access_type == "Edit Access" or access_type == "Admin Access"):
      permissions = permissions + [{"key": "create", "target": "page"}, {"key": "create", "target": "blogpost"}, {"key": "create", "target": "attachment"}, {"key": "delete", "target": "page"}, {"key": "delete", "target": "blogpost"}, {"key": "delete", "target": "attachment"}]
    
    if(access_type == "Admin Access"):
      permissions = permissions + [{"key": "export", "target": "space"}, {"key": "administer", "target": "space"}, {"key": "archive", "target": "page"}, {"key": "restrict_content", "target": "space"}]
      
    return permissions

  
  def approve(self, user, labels, approver, request, is_group=False, auto_approve_rules = None):
    permissions = []
    access_type = ""
    for label in labels:
      if 'View Access' in label['access_type']:
        access_type = 'View Access'
        permissions = self.__get_accesses_with_type('View Access')
      elif 'Edit Access' in label['access_type']:
        access_type = 'Edit Access'
        permissions = self.__get_accesses_with_type("Edit Access")
      elif "Admin Access" in label['access_type']:
        access_type = "Admin Access"
        permissions = self.__get_accesses_with_type("Admin Access")
      
      approve_result = []

      for permission in permissions:
        response = self.__approve_space_access(label["access_workspace"], permission, user.confluenceId, subject_type="user")
        if(response == False):
          return False
      
        approve_result.append({"permission": permission, "permission_id": response})
      
      request.updateMetaData("confluence", approve_result)
    
    email_targets = self.auto_grant_email_targets(user)
    email_body = f"Access successfully granted for confluence: {access_type} for Confluence Access to {user.email}.<br>Request has been approved by {approver}."
    email_subject = f"Approved Access: {request.request_id} for access to {self.access_desc()} for user {user.email}"

    try:
      emailSES(email_targets, email_subject, email_body)
      return True
    except Exception as e:
      logger.error("Could not send email for error %s", str(e))
      return False

  def revoke(self, user, label, request):
    permissions = request.meta_data["confluence"]

    for permission in permissions[::-1]:
      response = self.__revoke_space_access(label["access_workspace"], permission["permission_id"])
      if(response == False):
        logger.error("could not revoke access for %s", str(permission))
        return False
    
    label_desc = self.get_label_desc(label)
    email_targets = self.auto_grant_email_targets(user)
    email_subject = "Revoke Request: %s for %s" % ( label_desc, user.email )
    email_body = ""
    try:
      emailSES(email_targets, email_subject, email_body)
      return True
    except Exception as e:
      logger.error("Could not send email for error %s", str(e))
      return False
    

  def access_desc(self):
    return "Confluence Access Module"

  def tag(self):
    return 'confluence_module'

def get_object():
  return Confluence()
