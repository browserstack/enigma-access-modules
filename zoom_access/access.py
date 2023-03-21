"""access module for zoom"""
import logging
from django.template import loader
from Access.access_modules.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES
from . import helper, constants

logger = logging.getLogger(__name__)


class Zoom(BaseEmailAccess):
    """Zoom Access module."""

    urlpatterns = []
    ACCESS_LABEL = "zoom_access"

    def fetch_access_request_form_path(self):
        """Returns path to zoom module access request form."""
        return "zoom_access/access_request_form.html"

    def email_targets(self, user):
        """Returns email targets.
        Args:
            user (User): User whose access is being changed.
        Returns:
            array: Email address of the User and the module owners.
        """
        return [user.email] + self.grant_owner()

    def access_types(self):
        """Returns types of zoom access.
        Returns:
            array of json object: type of access type and description of access type.
        """
        return [
            {"type": "Standard License", "desc": "Standard License"},
            {"type": "Pro License", "desc": "Pro License"},
        ]

    def get_label_desc(self, access_label):
        """Returns access label description.
        Args:
            access_label: access label whose access to be requested.
        Returns:
            string: Description of access label.
        """
        if access_label["action"] == self.ACCESS_LABEL:
            access_type = access_label["access_type"]
            return " Zoom access for Meeting.  Access Type : " + access_type
        return ""

    def combine_labels_desc(self, access_labels):
        """Combines multiple access_labels.
        Args:
            access_labels (array): Array of access labels.
        Returns:
            str: Comma seperated access labels.
        """
        label_descriptions_set = set()
        for access_label in access_labels:
            label_desc = self.get_label_desc(access_label)
            label_descriptions_set.add(label_desc)
        return ", ".join(label_descriptions_set)

    def validate_request(self, access_labels_data, request_user, is_group=False):
        """Combines multiple access_labels.
        Args:
            access_labels_data (array): Array of access lables types.
            request_user (UserAccessMaping): Object of UserAccessMapping represents requested user.
        Returns:
            array (json objects): key value pair of access lable and it's access type.
        """
        valid_access_label_array = []
        for access_label_data in access_labels_data:
            if access_label_data not in ("Standard License", "Pro License"):
                raise Exception(constants.ERROR_MESSAGES["invalid_type"])
            valid_access_label = {}
            valid_access_label["action"] = self.ACCESS_LABEL
            valid_access_label["access_type"] = access_label_data
            valid_access_label_array.append(valid_access_label)
        return valid_access_label_array

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

        label_desc = self.combine_labels_desc(labels)
        user = user_identity.user
        type = 1
        if "Pro License" in label_desc:
            type = 2
        elif "Standard License" in label_desc:
            type = 1

        try:
            user_details = helper.get_user(user.email)
            if user_details[0] == 200:
                response = helper.update_user(
                    user.email, type
                )
                if response[0] != 204:
                    return False, "User updation failed" + str(response)
            else:
                response = helper.create_user(
                    user.email, type
                )
                if response[0] != 200 or response[0] != 201:
                    return False, "User creation failed" + str(response)
            self.__send_approve_email(user, label_desc, request.request_id, approver)
            return True, ""
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
            return False, str(e)
    
    def __send_approve_email(self, user, label_desc, request_id, approver):
        """Generates and sends email in access grant."""
        email_targets = self.email_targets(user)
        email_subject = "Approved Access: %s for access to %s for user %s" % (
            request_id,
            label_desc,
            user.email,
        )
        body = self.__generate_string_from_template(
            filename="approve_email.html",
            label_desc=label_desc,
            user_email=user.email,
            approver=approver,
        )

        emailSES(email_targets, email_subject, body)
    
    def __generate_string_from_template(self, filename, **kwargs):
        template = loader.get_template(filename)
        vals = {}
        for key, value in kwargs.items():
            vals[key] = value
        return template.render(vals)

    def __send_revoke_email(self, user, label_desc, request_id):
        """Generates and sends email in for access revoke."""
        email_targets = self.email_targets(user)
        email_subject = "Revoke Request: %s for access to %s for user %s" % (
            request_id,
            label_desc,
            user.email,
        )
        email_body = ""

        emailSES(email_targets, email_subject, email_body)
    

    def revoke(self, user, user_identity, label, request):
        """Revoke access to Zoom.
        Args:
            user (User): User whose access is to be revoked.
            user_identity (UserIdentity): User Identity object represents identity of user.
            access_label (str): Access label representing the access to be revoked.
            request (UserAccessMapping): UserAccessMapping representing the access.
        Returns:
            bool: True if revoke succeed. False if revoke fails.
            response: (array): Array of user details.
        """
        if user.state == 1:
            response = helper.update_user(user.email, 1)
        else:
            response = helper.delete_user(user.email)
        if response[0] != 204:
            return False, response
        
        label_desc = self.get_label_desc(label)
        try:
            self.__send_revoke_email(user, label_desc, request.request_id)
            return True, ""
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
            return False, str(e)

    def can_auto_approve(self):
        """Checks if access can be auto approved or manual approval is needed.
        Returns:
            bool: True for auto access and False for manual approval.
        """
        return False

    def get_identity_template(self):
        """Returns path to user identity form template"""
        return ""

    def verify_identity(self, request, email):
        """Verifying user Identity.
        Args:
            request (UserAccessMapping): UserAccessMapping representing the access.
            email: Email of user.
        Returns:
            json object: Empty if it fails to verify user identity or new email of user.
        """
        return {}

    def access_desc(self):
        """Returns zoom access description."""
        return "Zoom Meeting Access"

    def tag(self):
        """Returns zoom access tag."""
        return "zoom_access"


def get_object():
    """Returns instance of Zoom access Module."""
    return Zoom()
