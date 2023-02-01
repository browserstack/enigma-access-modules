import logging

from Access.access_modules.base_email_access.access import BaseEmailAccess
from Access.access_modules.github_access.helpers import (get_org,
                                                         get_org_invite,
                                                         get_org_repo_list,
                                                         get_repo, get_user,
                                                         grant_access,
                                                         put_user,
                                                         revoke_access)
from bootprocess.general import emailSES
from BrowserStackAutomation.settings import ACCESS_APPROVE_EMAIL
from django.shortcuts import render

logger = logging.getLogger(__name__)

class GithubAccess(BaseEmailAccess):

    def email_targets(self, user):
      return [ user.email ] + self.grant_owner()

    def grant_owner(self):
      return [ ACCESS_APPROVE_EMAIL ]

    def revoke_owner(self):
      return [ ACCESS_APPROVE_EMAIL ]

    def access_mark_revoke_permission(self, access_type):
      return [ ACCESS_APPROVE_EMAIL ]

    def revoke(self, user, label, request):
      user_name = user.gitusername
      result = revoke_access(user_name, label["repository"])
      label_desc = self.get_label_desc(label)
      email_targets = self.email_targets(user)
      email_subject = ""
      email_body = ""

      if result:
          logger.debug("Revoked access for user "+user_name+" to repo "+label["repository"])
          email_subject = "Revoke Request: %s for %s" % (label_desc, user.email)
          email_body = "Successfully revoked access for %s to %s." % (user.email, label["repository"])
      else:
          logger.error("Failed revoking access for user "+user_name+" to repo "+label["repository"])
          email_subject = "Revoke Request: %s for %s" % (label_desc, user.email)
          email_body = "Failed revoking access for %s to %s." % (user.email, label["repository"])

      try:
          emailSES(email_targets, email_subject, email_body)
          return True
      except Exception as e:
          logger.error("Could not send email for error %s", str(e))
          return False

    def offboard_github(self, github_username):
        return revoke_access(github_username)

    available = True

    def approve(self, user, labels, approver, request_id, is_group=False, auto_approve_rules = None):
        return_value = True
        error_message = ""
        label = labels[0]
        user_name = user.gitusername
        if not get_user(user_name):
          logger.error("Username "+user_name+" not present on github!")
          error_message = "Username "+user_name+" not present on github!"
          return_value = False

        if return_value and not get_org(user_name):
            if not get_org_invite(user_name):
                if put_user(user_name):
                    logger.debug("Added "+user_name+" to github org")
                    error_message = "Invited "+user_name+" to join github org. Access can be granted post inivation acceptance."
                    return_value = False
                else:
                    logger.error("Failed adding user "+user_name+" to github org")
                    error_message ="Failed adding user "+user_name+" to github org"
                return_value = False
            else:
                error_message = "Already invited "+user_name+" to join github org. Please accept the invite first."
                return_value = False

        if return_value and label["action"] == "repository_access":
          if not get_repo(label["repository"]):
            logger.error("repository "+ label["repository"] +" does not exist")
            error_message ="repository "+ label["repository"] +" does not exist"
            return_value = False
          else:
            if return_value and grant_access(label["repository"], label["access_level"], user_name):
              logger.debug("Added "+label["access_level"]+"access for user "+user_name+" to repo "+label["repository"])
            else:
              logger.error("Failed adding access for user "+user_name+" to repo "+label["repository"])
              error_message ="Failed adding access for user "+user_name+" to repo "+label["repository"]
              return_value = False

        label_desc = self.combine_labels_desc(labels)
        email_targets = []
        email_targets = self.email_targets(user)
        email_subject = ""
        email_body = ""

        if return_value:
            email_subject = "Access Granted: %s for access to %s for user %s" % ( request_id, self.access_desc(), user.email )

            if auto_approve_rules:
                email_body = "Access successfully granted for %s for %s to %s.<br>Request has been approved by %s. <br> Rules :- %s" % (label_desc, self.access_desc(), user.email, approver, ", ".join(auto_approve_rules))
            else:
                email_body = "Access successfully granted for %s for %s to %s.<br>Request has been approved by %s.<br>No futher action needed" % ( label_desc, self.access_desc(), user.email, approver)
        else:
            email_subject = "Access Grant Failed: %s for access to %s for user %s" % ( request_id, self.access_desc(), user.email )
            email_body = "Access grant failed for %s for %s to %s.<br> Reason - %s" % ( label_desc, self.access_desc(), user.email, error_message)
        try:
            emailSES(email_targets, email_subject, email_body)
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
        return return_value, error_message

    def get_label_desc(self, access_label):
      if access_label["action"] == "repository_access":
          repository = access_label["repository"]
          access_level = access_label["access_level"]
          return access_level + ' access for github repo - ' + repository

      return ""

    def combine_labels_desc(self,access_labels):
        label_descriptions_set = set()
        for access_label in access_labels:
            label_desc = self.get_label_desc(access_label)
            label_descriptions_set.add(label_desc)

        return ", ".join(label_descriptions_set)

    def get_label_meta(self, access_label):
        return {}

    def combine_labels_meta(self, access_labels):
        return {}

    def access_types(self):
        return []

    def access_desc(self):
        return "Github Access"

    def tag(self):
        return 'github_access'

    def fetch_access_request_form_path(self):
        return 'github_access/access_request_form.html'

    def access_request_data(self, request, is_group=False):
        repo_data = [repo for repo in get_org_repo_list()]
        data = {'githubRepoList': repo_data}
        return data

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
        return str(render(request, 'base_email_access/accessApproveEmail.html', context_details))

    def validate_request(self, access_labels_data, request_user, is_group=False):
        valid_access_label_array = []

        valid_access_label = {}

        for repo_name in access_labels_data[0]["repoList"]:
            access_level = access_labels_data[0]["accessLevel"]

            if len(repo_name) == 0:
                raise Exception('Repo not found')
            valid_access_label = {}
            valid_access_label["action"] = "repository_access"
            valid_access_label['access_level'] = access_level

            valid_access_label['repository'] = repo_name
            valid_access_label_array.append(valid_access_label)

        return valid_access_label_array

    def match_keywords(self):
        return  ['github','git']


def get_object():
    return GithubAccess()
