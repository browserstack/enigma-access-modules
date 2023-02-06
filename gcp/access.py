from Access.access_modules.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES
from django.template import loader
from . import helpers
from . import constants
import logging

logger = logging.getLogger(__name__)


class GCPAccess(BaseEmailAccess):
    GROUP_ACCESS = "GroupAccess"

    def email_targets(self, user):
        return [user.email] + self.grant_owner()

    def fetch_access_request_form_path(self):
        return "gcp_access/accessRequest.html"

    def access_types(self):
        return []

    def get_label_desc(self, access_label):
        if access_label["action"] == self.GROUP_ACCESS:
            return access_label["action"] + " for group: " + (access_label["group"])
        return ""

    def combine_labels_desc(self, access_labels):
        label_desc_array = [
            self.get_label_desc(access_label) for access_label in access_labels
        ]
        return ", ".join(label_desc_array)

    def get_label_meta(self, access_label):
        return access_label

    def validate_request(self, access_labels_data, request_user, is_group=False):
        # try:
        valid_access_label_array = []
        for access_label_data in access_labels_data:
            if (
                not access_label_data.get("action")
                and access_label_data["action"] != constants.GROUP_ACCESS
            ):
                raise Exception(constants.VALID_ACTION_REQUIRED_ERROR)
            if not access_label_data.get(
                "domain"
            ) and not helpers.get_gcp_domain_details(access_label_data["domain"]):
                raise Exception(constants.VALID_DOMAIN_REQUIRED_ERROR)
            if not access_label_data.get("group") and not helpers.gcp_group_exists(
                access_label_data["domain"], access_label_data["group"]
            ):
                raise Exception(constants.VALID_GROUP_REQUIRED_ERROR)
            valid_access_label = {
                "action": access_label_data["action"],
                "domain": access_label_data["domain"],
                "group": access_label_data["group"],
            }
            valid_access_label_array.append(valid_access_label)

        return valid_access_label_array

    def approve(
        self, user, labels, approver, request, is_group=False, auto_approve_rules=None
    ):
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
            self.__send_approve_email(user, label_desc, request.request_id, approver)
            return True
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
            return False

    def __send_approve_email(self, user, label_desc, request_id, approver):
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

    def revoke(self, user, label, request):
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
            logger.error("Could not send email for error %s", str(e))
            return False

    def access_request_data(self, request, is_group=False):
        return {"domains": helpers.get_gcp_domains()}

    def access_desc(self):
        return "GCP Group Access"

    def tag(self):
        return constants.GCP_ACCESS_TAG


def get_object():
    return GCPAccess()
