from Access.access_modules.base_email_access.access import BaseEmailAccess
from . import helper, constants
import logging
import json
from django.template import loader
from bootprocess.general import emailSES

logger = logging.getLogger(__name__)


class OpsgenieAccess(BaseEmailAccess):
    """Opsgenie Access module."""

    urlpatterns = []

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

        total_teams_list = helper.teams_list()

        for access_label_data in access_labels_data[0]["teams_list"]:
            if access_label_data not in total_teams_list:
                raise Exception(constants.VALID_TEAM_REQUIRED_ERROR)

            if access_labels_data[0]["UserType"] not in ("user", "team_admin"):
                raise Exception(constants.VALID_USER_TYPE_REQUIRED_ERROR)

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

        user = user_identity.user
        username = user.name
        user_email = user.email
        team, user_type = self.get_team_and_usertype(labels)
        email_targets = self.email_targets(user_identity.user)
        value = True
        role = "user"
        if user_type == "team_admin":
            response_return_value, response_message = helper.create_team_admin_role(
                team
            )
            if response_return_value is False:
                value = False
                return False, "Failed to create TeamAdmin role" + str(response_message)
            role = "TeamAdmin"

        return_value, error_message = helper.add_user_to_team(
            username, user_email, team, role
        )
        if return_value is False:
            value = False
            return False, "Failed to add user to Team" + str(error_message)

        access_description = self.access_desc()
        try:
            self.__send_approve_email(
                user_identity.user,
                access_description,
                request.request_id,
                approver,
                value,
                auto_approve_rules,
            )
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
        return True

    def __generate_string_from_template(self, filename, **kwargs):
        template = loader.get_template(filename)
        vals = {}
        for key, value in kwargs.items():
            vals[key] = value
        return template.render(vals)

    def __send_approve_email(
        self, user, label_desc, request_id, approver, grant_status, auto_approve_rules
    ):
        email_targets = self.email_targets(user)
        email_subject = constants.GRANT_REQUEST % (
            request_id,
            self.access_desc(),
            user.email,
        )
        email_body = self.__generate_string_from_template(
            filename="access_email.html",
            status=grant_status,
            auto_approve=auto_approve_rules,
            request_id=request_id,
            user_email=user.email,
            access_desc=self.access_desc(),
            access_meta=label_desc,
            approver=approver,
        )

        emailSES(email_targets, email_subject, email_body)

    def __send_revoke_email(self, user, request_id, label_desc):
        """Generates and sends email in for access revoke."""
        email_targets = self.email_targets(user)
        email_subject = f"""Revoke Request: {request_id}
        for access to {label_desc} for user {user.email}"""
        emailSES(email_targets, email_subject, "")

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
        return_value = False
        if user.state in (2, 3):
            response = helper.delete_user(user.email)
            if response is not None and response.status_code not in (200, 201):
                response = None
        else:
            response = None
        if response is not None and "result" in response.json():
            usr_result = str(json.loads(response.text)["result"])
            if usr_result is not None and usr_result == "Deleted":
                return_value = True
        else:
            logger.error("Something went wrong while removing %s from %s: %s", ())
            return False

        access_description = self.access_desc()
        try:
            self.__send_revoke_email(user, request.request_id, access_description)
        except Exception as ex:
            logger.error("Could not send email for error %s", str(ex))
        return return_value, response

    def all_possible_accesses(self):
        try:
            self.teams_list = helper.teams_list()
            self.all_possible_access = {}
            self.all_possible_access.update({team: team for team in self.teams_list})
            return self.all_possible_access
        except Exception as e:
            logger.error(e)
            self.teams_list = {}, {}, {}

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
        user_accesses["opsgenie"] = self.all_possible_accesses()
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
        return {}

    def get_label_meta(self, request_params):
        return {}

    def combine_labels_meta(self, access_labels):
        return {}

    def access_types(self):
        """Returns types of zoom access.
        Returns:
            array of json object: type of access type and descryption of access type.
        """
        return []

    def fetch_access_request_form_path(self):
        return "opsgenie_access/access_request_form.html"

    def get_identity_template(self):
        """Returns path to user identity form template"""
        return ""

    def access_desc(self):
        """Returns Opsgenie access descryption."""
        return "Opsgenie Access"

    def tag(self):
        """Returns opsgenie access tag."""
        return "opsgenie_access"

    def match_keywords(self):
        """Returns opsgenie access tag."""
        return ["opsgenie_access"]


def get_object():
    """Returns instance of Opsgenie access Module."""
    return OpsgenieAccess()
