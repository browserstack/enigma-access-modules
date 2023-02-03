from django.template import loader
from . import helpers, constants
from Access.access_modules.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES
import logging

logger = logging.getLogger(__name__)


class AWSAccess(BaseEmailAccess):
    def email_targets(self, user):
        return [user.email] + self.grant_owner()

    def approve(
        self,
        user,
        labels,
        approver,
        request,
        is_group=False,
        auto_approve_rules=None,
    ):
        label_desc = self.combine_labels_desc(labels)
        label_meta = self.combine_labels_meta(labels)
        for label in labels:
            granted_access, exception = helpers.grant_aws_access(
                user, label["account"], label["group"]
            )

            if not granted_access:
                logger.error(
                    "Something when wrong while adding %s to group %s: %s"
                    % (user.email, label["group"], str(exception))
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
        except Exception as e:
            logger.error(f"{self.tag()} Could not send email for error {str(e)}")
            return False

        return True

    def __send_approve_email(
        self, auto_approve_rules, request_id, label_desc, user, approver, label_meta
    ):
        if auto_approve_rules:
            email_subject = """
                Access Granted: %s for access to %s for user %s. Rules :- %s""" % (
                request_id,
                label_desc,
                user.email,
                " ,".join(auto_approve_rules),
            )
        else:
            email_subject = "Access Granted: %s for access to %s for user %s." % (
                request_id,
                label_desc,
                user.email,
            )

        email_body = self._generateStringFromTemplate(
            "aws_access/approved_email_template.html.j2",
            request_id=request_id,
            approver=approver,
            user_email=user.email,
            access_desc=label_desc,
            access_meta=label_meta,
        )
        email_targets = self.email_targets(user)
        emailSES(email_targets, email_subject, email_body)

    def __send_revoke_email(self, user, request_id, label_desc):
        email_targets = self.email_targets(user)
        email_subject = "Revoke Request: %s for access to %s for user %s" % (
            request_id,
            label_desc,
            user.email,
        )
        email_body = ""

        emailSES(email_targets, email_subject, email_body)

    def get_label_desc(self, access_label):
        if access_label["action"] == constants.GROUP_ACCESS:
            return access_label["action"] + " for group: " + access_label["group"]
        return ""

    def combine_labels_desc(self, access_labels):
        label_desc_array = [
            self.get_label_desc(access_label) for access_label in access_labels
        ]
        return ", ".join(label_desc_array)

    def get_label_meta(self, access_label):
        return access_label

    def combine_labels_meta(self, access_labels):
        if access_labels:
            combined_meta = {"action": "", "account": "", "group": ""}
            for label in access_labels:
                for key, value in label.items():
                    combined_meta[key] = str(combined_meta[key]) + f", {str(value)}"
            return combined_meta
        return dict()

    def access_request_data(self, request, is_group=False):
        return dict({"accounts": helpers.get_aws_accounts()})

    def revoke(self, user, label, request):
        is_revoked, exception = helpers.revoke_aws_access(
            user, label["account"], label["group"]
        )

        if not is_revoked:
            logger.error(
                "Something went wrong while removing %s from %s: %s"
                % (user.email, label["group"], str(exception))
            )
            return False

        label_desc = self.get_label_desc(label)
        try:
            self.__send_revoke_email(user, request.request_id, label_desc)
            return True
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
            return False

    def validate_request(self, access_labels_data, request_user, is_group=False):
        valid_access_label_array = list()
        for access_label_data in access_labels_data:
            if (
                not access_label_data.get("action")
                and access_label_data["action"] != constants.GROUP_ACCESS
            ):
                raise Exception(constants.ERROR_MESSAGES["valid_action_required"])
            if not access_label_data.get("account") and not helpers.aws_account_exists(
                access_label_data.get("account")
            ):
                raise Exception(constants.ERROR_MESSAGES["valid_account_required"])
            if not access_label_data.get("group") and not helpers.aws_group_exists(
                access_label_data["account"], access_label_data.get("group")
            ):
                raise Exception(constants.ERROR_MESSAGES["valid_group_required"])
            valid_access_label = {
                "action": access_label_data.get("action"),
                "account": access_label_data.get("account"),
                "group": access_label_data.get("group"),
            }
            valid_access_label_array.append(valid_access_label)
        return valid_access_label_array

    def fetch_access_request_form_path(self):
        return "aws_access/accessRequest.html"

    def access_desc(self):
        return "AWS Group Access"

    def match_keywords(self):
        return ["aws", "amazon", "web", "services", "console", "cloud"]

    def tag(self):
        return "aws_access"

    def _generateStringFromTemplate(self, filename, **kwargs):
        template = loader.get_template(filename)
        vals = {}
        for key, value in kwargs.items():
            vals[key] = value
        return template.render(vals)

    def access_types(self):
        return {}


def get_object():
    return AWSAccess()
