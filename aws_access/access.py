"""access module for AWS"""
from . import helpers, constants, urls
from Access.base_email_access.access import BaseEmailAccess

import logging
from django.template import loader
import json

logger = logging.getLogger(__name__)


class AWSModuleValidationError(Exception):
    """Validation Error Exception.

    Args:
        Exception (str): Validation error string.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AWSAccess(BaseEmailAccess):
    """AWS Access module."""

    account_groups = {}

    urlpatterns = urls.urlpatterns

    @staticmethod
    def get_account_groups(account):
        if AWSAccess.account_groups.get(account):
            return AWSAccess.account_groups.get(account)

        groups = []
        found_marker = True
        marker = None
        while found_marker:
            account_groups = helpers.get_aws_groups(account, marker)
            groups += account_groups["Groups"]
            if account_groups.get("IsTruncated"):
                marker = account_groups["Marker"]
            else:
                found_marker = False

        AWSAccess.account_groups[account] = groups
        return AWSAccess.account_groups.get(account)

    def can_auto_approve(self):
        return False

    def email_targets(self, user):
        """Returns email targets.

        Args:
            user (User): User whose access is being changed.

        Returns:
            array: Email address of the User and the module owners.
        """
        return [user.email] + self.grant_owner()

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
        label_meta = self.combine_labels_meta(labels)
        for label in labels:
            granted_access, exception = helpers.grant_aws_access(
                user, label["account"], label["group"]
            )

            if not granted_access:
                logger.error(
                    "Something when wrong while adding %s to group %s: %s",
                    user.email,
                    label["group"],
                    str(exception)
                )
                return False

        try:
            self.__send_approve_email(
                auto_approve_rules,
                request.request_id,
                label_desc,
                user,
                approver,
                label_meta,
            )
        except Exception as ex:
            logger.exception("%s Could not send email for error %s", self.tag(), str(ex))
            return False

        return True

    def __send_approve_email(
        self, auto_approve_rules, request_id, label_desc, user, approver, label_meta
    ):
        """Generates and sends email in access grant."""
        if auto_approve_rules:
            rules = " ,".join(auto_approve_rules)
            email_subject = (f"Access Granted: {request_id}"
            f" for access to {label_desc} for user {user.email}. Rules :- {rules}")
        else:
            email_subject = (f"Access Granted: {request_id}"
            f" for access to {label_desc} for user {user.email}.")

        email_body = self._generate_string_from_template(
            "aws_access/approved_email_template.html.j2",
            request_id=request_id,
            approver=approver,
            user_email=user.email,
            access_desc=label_desc,
            access_meta=label_meta,
        )
        email_targets = self.email_targets(user)
        self.email_via_smtp(email_targets, email_subject, email_body)

    def __send_revoke_email(self, user, request_id, label_desc):
        """Generates and sends email in for access revoke."""
        email_targets = self.email_targets(user)
        email_subject = (f"Revoke Request: {request_id}"
        f"for access to {label_desc} for user {user.email}")
        self.email_via_smtp(email_targets, email_subject, "")

    def get_label_desc(self, access_label):
        """Gets the access label descrption

        Args:
            access_label (str): JSON string representing the access label.

        Returns:
            str: Access Label description.
        """
        if access_label["action"] == constants.GROUP_ACCESS:
            return access_label["action"] + " for group: " + access_label["group"]
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
            str: Access Label metadata.
        """
        return access_label

    def combine_labels_meta(self, access_labels):
        """Combines the metadata for multiple access labels.

        Args:
            access_labels (str): Array of access labels.

        Returns:
            dict: Dictionary of access label keys and values.
        """
        if access_labels:
            combined_meta = {"action": "", "account": "", "group": ""}
            for label in access_labels:
                for key, value in label.items():
                    if str(combined_meta[key]) != "":
                        combined_meta[key] = ", ".join(
                            [str(combined_meta[key]), str(value)]
                        )
                    else:
                        combined_meta[key] = str(value)
            return combined_meta
        return {}

    def access_request_data(self, request, is_group=False):
        """Creates a dictionary of aws accounts.

        Args:
            request (dict): A request form representing the http form request.
            is_group (bool, optional): Whether the access is requested
            for an Enigma Group. Defaults to False.

        Returns:
            dict: Dictionary of AWS accounts.
        """
        return dict({"accounts": helpers.get_aws_accounts()})

    def revoke(self, user, user_identity, label, request):
        """Revoke access to AWS Group.

        Args:
            user (User): User whose access is to be revoked.
            user_identity (UserIdentity): UserIdentity representing the user.
            label (str): Access label representing the access to be revoked.
            request (UserAccessMapping): UserAccessMapping representing the access.

        Returns:
            bool: True is the revoke is success. False if the revoke Fails.
        """
        is_revoked, exception = helpers.revoke_aws_access(
            user, label["account"], label["group"]
        )

        if not is_revoked:
            logger.error(
                "Something went wrong while removing %s from %s: %s",
                user.email, label["group"], str(exception)
            )
            return False

        label_desc = self.get_label_desc(label)
        try:
            self.__send_revoke_email(user, request.request_id, label_desc)
            return True
        except Exception as ex:
            logger.exception("Could not send email for error %s", str(ex))
            return False

    def validate_request(self, access_request_form, request_user, is_group=False):
        """Validates the access request.

        Args:
            access_labels_data (str): Access Label representing the access requested.
            request_user (User): User requesting the access.
            is_group (bool, optional): Whether the access is being requested for a group.
            Defaults to False.

        Raises:
            AWSModuleValidationError: If the access label validation fails.

        Returns:
            arr: Array of the access labels for the request access.
        """
        if not access_request_form.get(
            "aws-account"
        ) and not helpers.aws_account_exists(access_request_form.get("aws-account")):
            raise AWSModuleValidationError(
                constants.ERROR_MESSAGES["valid_account_required"]
            )
        if not access_request_form.get("selected-aws-groups"):
            raise AWSModuleValidationError(constants.ERROR_MESSAGES["select_group"])

        aws_groups = json.loads(access_request_form.get("selected-aws-groups"))
        aws_account = access_request_form.get("aws-account")

        if type(aws_groups) != list:
            raise AWSModuleValidationError(
                constants.ERROR_MESSAGES["valid_groups_required"]
            )

        valid_access_label_array = []

        for group in aws_groups:
            if not helpers.aws_group_exists(aws_account, group):
                raise AWSModuleValidationError(
                    constants.ERROR_MESSAGES["valid_group_required"]
                )

            valid_access_label = {
                "action": constants.GROUP_ACCESS,
                "account": aws_account,
                "group": group,
            }
            valid_access_label_array.append(valid_access_label)
        return valid_access_label_array

    def fetch_access_request_form_path(self):
        """Returns the html form template for filling access path.

        Returns:
            str: Path of the html template.
        """
        return "aws_access/accessRequest.html"

    def access_desc(self):
        """Description of the access module.

        Returns:
            str: Description of the aws access module.
        """
        return "AWS Group Access"

    def match_keywords(self):
        """Keywords specific to aws requests.

        Returns:
            arr: Returns array of AWS module keywords.
        """
        return ["aws", "amazon", "web", "services", "console", "cloud"]

    def tag(self):
        """Returns aws access tag."""
        return "aws_access"

    def _generate_string_from_template(self, filename, **kwargs):
        template = loader.get_template(filename)
        vals = {}
        for key, value in kwargs.items():
            vals[key] = value
        return template.render(vals)

    def access_types(self):
        """Not Implemented."""
        return {}

    def get_identity_template(self):
        return ""

    def verify_identity(self, request, email):
        return {}


def get_object():
    """Returns instance of AWS Access Module."""
    return AWSAccess()
