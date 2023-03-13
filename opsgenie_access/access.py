from Access.access_modules.base_email_access.access import BaseEmailAccess
from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS
from Access.models import UserAccessMapping
from bootprocess.general import emailSES
from . import helper, constants
import logging
import json


logger = logging.getLogger(__name__)


class OpsgenieAccess(BaseEmailAccess):
    """Opsgenie Access module."""

    urlpatterns = []

    def __init__(self):
        try:
            self.teams_list = helper.teams_list()
            self.all_possible_accesses = {}
            self.all_possible_accesses.update({team: team for team in self.teams_list})
        except Exception as e:
            logger.error(e)
            self.teams_list = {}, {}, {}

    def can_auto_approve(self):
        """Checks if access can be auto approved or manual approval is needed.
        Returns:
            bool: True for auto access and False for manual approval.
        """
        return False

    def email_targets(self, user):
        """Returns email targets.
        Args:
            user (User): User whose access is being changed.
        Returns:
            array: Email address of the User and the module owners.
        """
        return [user.email] + self.grant_owner()

    def validate_request(self, access_labels_data, request_user, is_group=False):
        """Combines multiple access_labels.
        Args:
            access_labels_data (array): Array of access lables types.
            request_user (UserAccessMaping): Object of UserAccessMapping represents requested user.
        Returns:
            array (json objects): key value pair of access lable and it's access type.
        """
        valid_access_label_array = []
        for access_label_data in access_labels_data[0]["teams_list"]:
            valid_access_label = {
                "team": access_label_data,
                "usertype": access_labels_data[0]["UserType"],
            }
            valid_access_label_array.append(valid_access_label)
        return valid_access_label_array

    def combine_labels_desc(self, access_labels):
        return str(access_labels[0]["team"]) + " " + str(access_labels[0]["usertype"])

    def get_team_and_usertype(self, access_labels):
        return access_labels[0]["team"], access_labels[0]["usertype"]

    def approve(
        self,
        user_identity,
        labels,
        approver,
        request,
        is_group=False,
        auto_approve_rules=None,
    ):
        """Approves a users access request.
        Args:
            user_identity (User): User identity object represents user whose access is being approved.
            labels (str): Access Label that respesents the access to be approved.
            approver (User): User who is approving the access.
            request (UserAccessMapping): Access mapping that repesents the User Access.
            is_group (bool, optional): Whether the access is requested for a User or a Group.
                                       Defaults to False.
            auto_approve_rules (str, optional): Rules for auto approval. Defaults to None.
        Returns:
            bool: True if the access approval is success, False in case of failure with error string.
        """
        username = user_identity.identity["user_name"]
        user_email = user_identity.identity["user_email"]
        team, user_type = self.get_team_and_usertype(labels)
        email_targets = self.email_targets(user_identity.user)
        role = "user"
        if user_type == "team_admin":
            response = helper.create_team_admin_role(team)
            if "result" not in response.json():
                return False, "Failed to create TeamAdmin role" + str(response)
            role = "TeamAdmin"
        return_value = helper.add_user_to_team(username, user_email, team, role)
        if "result" not in return_value.json():
            return False, "Failed to add user to Team" + str(return_value)

        email_subject = (
            "[Enigma][Access Management] Access Granted: %s for access to %s for user %s"
            % (request.request_id, self.access_desc(), user_identity.user.email)
        )
        if auto_approve_rules:
            email_body = (
                "Access successfully granted for opsgenie:Team %s for %s to %s.<br>Request has been approved by %s. <br> Rules :- %s"
                % (
                    team,
                    self.access_desc(),
                    user_identity.user.email,
                    approver,
                    ", ".join(auto_approve_rules),
                )
            )
        else:
            email_body = (
                "Access successfully granted Opsgenie.<br>Request has been approved by %s"
                % (approver)
            )

        email_body += "<br>Please follow the instructions from step 1 on this page "

        try:
            emailSES(email_targets, email_subject, email_body)
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
        return True

    def revoke(self, user, user_identity, access_label, request):
        """Revoke access to Opsgenie.
        Args:
            user (User): User whose access is to be revoked.
            user_identity (UserIdentity): User Identity object represents identity of user.
            access_label (str): Access label representing the access to be revoked.
            request (UserAccessMapping): UserAccessMapping representing the access.
        Returns:
            bool: True if revoke succeed. False if revoke fails.
            response: (array): Array of user details.
        """
        if user.state in (2, 3):
            response = helper.delete_user(user_identity.identity["user_email"])
        else:
            response = ""
        if response is not None and "result" in response.json():
            usr_result = str(json.loads(response.text)["result"])
            if usr_result is not None and usr_result == "Deleted":
                return True, ""
        email_targets = self.email_targets(user_identity.user)
        email_subject = (
            "Opsgenie access revoke failed for user Name: "
            + user_identity.identity["user_name"]
            + " Email :"
            + user_identity.identity["user_email"]
        )
        email_body = response
        emailSES(email_targets, email_subject, email_body)
        return False, response

    def access_request_data(self, request, is_group=False):
        """Creates a dictionary of Opsgenie access.
        Args:
            request (dict): A request form representing the http form request.
            is_group (bool, optional): whether the access is requested
            for an Enigma Group. Defaults to False.
        Returns:
            dict: Dictionary of opsgenie access.
        """
        user_accesses = {}
        user_accesses["opsgenie"] = self.all_possible_accesses
        return user_accesses

    def get_label_desc(self, access_label):
        """Returns access lable descryption.
        Args:
            access_label: access lable whose access to be requested.
        Returns:
            string: Descryption of access lable.
        """
        if "team" in access_label:
            return access_label["team"]
        else:
            return access_label["data"]

    def verify_identity(self, request, email):
        """Verifying user Identity.
        Args:
            request (UserAccessMapping): UserAccessMapping representing the access.
            email: Email of user.
        Returns:
            json object: Empty if it fails to verify user identity or new email of user.
        """
        user_email = request["user_email"]
        user_name = request["user_name"]
        if not helper.is_email_valid(user_email, email):
            logger.error(constants.USER_IDENTITY_NOT_FOUND, user_email)
            return {}
        return {"user_email": user_email, "user_name": user_name}

    def get_label_meta(self, request_params):
        return {}

    def combine_labels_meta(self, access_labels):
        return {}

    def access_types(self):
        """Returns types of Opagenie access.
        Returns:
            array of json object: type of access type and descryption of access type.
        """
        return [{"type": "opsgenieStandardUser", "desc": "opsgenie - Standard User"}]

    def fetch_access_request_form_path(self):
        return "opsgenie_access/access_request_form.html"

    def get_identity_template(self):
        """Returns path to user identity form template"""
        return "opsgenie_access/identity_form.html"

    def access_desc(self):
        """Returns Opsgenie access descryption."""
        return "Opsgenie Access"

    def tag(self):
        """Returns opsgenie access tag."""
        return "opsgenie_access"

    def match_keywords(self):
        """Returns Opagenie access tag."""
        return ["opsgenie_access"]


def get_object():
    """Returns instance of Opsgenie access Module."""
    return OpsgenieAccess()
