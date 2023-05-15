"""access module for GCP"""
from django.template import loader
import logging
import json

from . import constants, helpers, urls
from Access.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES


logger = logging.getLogger(__name__)


class GCPModuleValidationError(Exception):
    """Validation Error Exception.

    Args:
        Exception (str): Validation error string.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class GCPAccess(BaseEmailAccess):
    """GCP Access module."""

    group_access = "GroupAccess"
    urlpatterns = urls.urlpatterns

    def email_targets(self, user):
        """Returns email targets.

        Args:
            user (User): User whose access is being changed.

        Returns:
            array: Email Address of the User and the module owners.
        """
        return [user.email] + self.grant_owner()

    def fetch_access_request_form_path(self):
        """Returns the html form template for filling access path.

        Returns:
            str: Path of the html template.
        """
        return "gcp_access/accessRequest.html"

    def access_types(self):
        """Not Implemented."""
        return []

    def get_label_desc(self, access_label):
        """Gets the access label descrption.

        Args:
            access_label (str): JSON string representing the access label.

        Returns:
            str: Access Label description.
        """
        if access_label["action"] == self.group_access:
            return access_label["action"] + " for group: " + (access_label["group"])
        return ""

    def combine_labels_desc(self, access_labels):
        """Combines multiple access_labels.

        Args:
            access_labels (array): Array of access labels.

        Returns:
            str: Comma seperated access labels.
        """
        label_desc_array = [
            self.get_label_desc(access_label) for access_label in access_labels
        ]
        return ", ".join(label_desc_array)

    def get_label_meta(self, access_label):
        """Returns metadata for the access label.

        Args:
            access_label (str): JSON string representing access label.

        Returns:
            str: Access label metadata.
        """
        return access_label

    def validate_request(self, access_request_form, request_user, is_group=False):
        """Validates the access request.

        Args:
            access_request_form (form): Access module request form.
            request_user (User): User requesting the access.
            is_group (bool, optional): Whether the access is being requested for a group.
            Defaults to False.

        Returns:
            arr: Array of the access labels for the request access.
        """
        if not access_request_form.get("gcp-domain"):
            raise GCPModuleValidationError(
                constants.VALID_DOMAIN_REQUIRED_ERROR
            )

        gcp_groups = json.loads(access_request_form.get("selected-gcp-groups"))
        gcp_domain = access_request_form.get("gcp-domain")

        if not access_request_form.get("selected-gcp-groups") or len(gcp_groups) <= 0:
            raise GCPModuleValidationError(
                constants.VALID_SELECT_GROUP_ERROR)

        if type(gcp_groups) != list:
            raise GCPModuleValidationError(
                constants.VALID_GROUP_REQUIRED_ERROR
            )

        valid_access_label_array = []
        for group in gcp_groups:

            valid_access_label = {
                "action": constants.GROUP_ACCESS,
                "domain": gcp_domain,
                "group": group,
            }
            valid_access_label_array.append(valid_access_label)
        print("ARRAY--->", valid_access_label_array)
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
            user (User): User whose access is being approved.
            labels (str): Access Label that respesents the access to be approved.
            approver (User): User who is approving the access.
            request (UserAccessMapping): Access mapping that repesents the User Access.
            is_group (bool, optional): Whether the access is requested for a User or a Group.
                                       Defaults to False.
            auto_approve_rules (str, optional): Rules for auto approval. Defaults to None.

        Returns:
            bool: True if the access approval is success, False in case of failure.
        """
        user = user_identity.user
        label_desc = self.combine_labels_desc(labels)
        for label in labels:
            result, exception = helpers.grant_gcp_access(
                label["group"], label["domain"], user.email
            )
            if result is False:
                logger.error(
                    "Something went wrong while adding the %s to group %s: %s"
                    % (user.email, label["group"], str(exception))
                )
                return False

        try:
            self.__send_approve_email(
                user, label_desc, request.request_id, approver)
            return True
        except Exception as e:
            logger.error("Could not send email for error %s" % str(e))
            return False

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

    def __generate_string_from_template(self, filename, **kwargs):
        template = loader.get_template(filename)
        vals = {}
        for key, value in kwargs.items():
            vals[key] = value
        return template.render(vals)

    def revoke(self, user, user_identity, label, request):
        """Revoke access to GCP Group.

        Args:
            user (User): User whose access is to be revoked.
            label (str): Access label representing the access to be revoked.
            request (UserAccessMapping): UserAccessMapping representing the access.

        Returns:
            bool: True is the revoke is success. False if the revoke Fails.
        """
        result, exception = helpers.revoke_gcp_access(
            label["group"], label["domain"], user.email
        )
        if not result:
            logger.error(
                f"Error while removing the user from the group {label['group']}:"
                f" {str(exception)}"
            )
            return False

        label_desc = self.get_label_desc(label)
        try:
            self.__send_revoke_email(user, label_desc, request.request_id)
            return True
        except Exception as e:
            logger.error("Could not send email for error %s" % str(e))
            return False

    def access_request_data(self, request, is_group=False):
        """Creates a dictionary of GCP accounts.

        Args:
            request (dict): A request form representing the http form request.
            is_group (bool, optional): whether the access is requested
            for an Enigma Group. Defaults to False.

        Returns:
            dict: Dictionary of GCP accounts.
        """
        return {"domains": helpers.get_gcp_domains()}

    def access_desc(self):
        """Description of the access module.

        Returns:
            str: Description of the GCP access module.
        """

        return "GCP Group Access"

    def get_identity_template(self):
        return ""

    def verify_identity(self, request, email):
        return {}

    def can_auto_approve(self):
        return False

    def tag(self):
        """Returns gcp access tag."""
        return constants.GCP_ACCESS_TAG


def get_object():
    """Returns instance of GCP Access Module."""
    return GCPAccess()
