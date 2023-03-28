import logging

from Access.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES
from . import helpers, urls

from django.template import loader

logger = logging.getLogger(__name__)


class SSHAccess(BaseEmailAccess):
    """SSH Access Module"""
    available = True
    urlpatterns = urls.urlpatterns

    def email_targets(self, user):
        """returns email targets

        Args:
            user (User): User whose access is being changed

        Returns:
            array: email address of the User and the module owners
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
        """
        Approves the request for the user to access the resource specified in the label and
        sends an email to the user and the module owners with the details of the access.
        If the user already has access to the resource, the request is rejected.

        Args:
            user (User): User whose access is being changed
            labels (array): Labels of the request
            approver (User): User who approved the request
            request (UserAccessMapping): Access mapping that repesents the User Access
            is_group (bool, optional): Whether the request is for a group. Defaults to False.
            auto_approve_rules (array, optional): Rules for auto approval. Defaults to None.

        Returns:
            bool: True if the request is approved, False otherwise
        """
        label_desc = self.combine_labels_desc(labels)
        user = user_identity.user

        return_value, error_message = helpers.sshHelper(labels, user_identity, user, "grant")

        if not return_value:
            logger.error(
                "Something went wrong while adding the %s to group %s: %s"
                % (user.email, labels, str(error_message))
            )

        try:
            self.__send_approve_email(
                user, label_desc, request.request_id, approver, return_value, auto_approve_rules
            )
        except Exception as e:
            logger.error(
                "%s: Could not send email for error %s", {self.tag()}, {str(e)}
            )
            return_value = False

        return return_value, error_message

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
        email_subject = (
            "[Enigma][Access Management] Access Granted: %s for access to %s for"
            " user %s" % (request_id, self.access_desc(), user.email)
        )

        if auto_approve_rules:
            email_body = (
                "Access successfully granted for %s for %s to %s.<br>Request has been"
                " approved by %s. <br> Rules :- %s"
                % (
                    label_desc,
                    self.access_desc(),
                    user.email,
                    approver,
                    ", ".join(auto_approve_rules),
                )
            )
        else:
            email_body = (
                "Access successfully granted for %s for %s to %s.<br>Request has been"
                " approved by %s.<br>No futher action needed"
                % (label_desc, self.access_desc(), user.email, approver)
            )

        emailSES(email_targets, email_subject, email_body)

    def __send_revoke_email(self, user, request_id, label_desc):
        """generates and sends email in for access revoke"""
        email_targets = self.email_targets(user)
        email_subject = (
            "[Enigma][Access Management] Access Revoked: %s for access to %s for"
            " user %s" % (request_id, self.access_desc(), user.email)
        )
        email_body = (
            "Access successfully revoked for %s for %s to %s.<br>No futher action"
            " needed" % (label_desc, self.access_desc(), user.email)
        )
        emailSES(email_targets, email_subject, email_body)

    def get_label_desc(self, access_label):
        """gets the access label description

        Args:
            access_label (str): json string representing the access label

        Returns:
            str: access label description
        """

        machine = ""
        if "machine" in access_label:
            machine = access_label["machine"]
        else:
            machine = access_label["ip"]
        access_level = access_label["access_level"]
        return access_level + " ssh access for " + machine

    def combine_labels_desc(self, access_labels):
        """combines multiple access_labels

        Args:
            access_labels (array): array of access labels

        Returns:
            str: comma seperated access labels
        """
        label_descriptions_set = set()
        for access_label in access_labels:
            label_desc = self.get_label_desc(access_label)
            label_descriptions_set.add(label_desc)

        return ", ".join(label_descriptions_set)

    def get_label_meta(self, access_label):
        return {}

    def combine_labels_meta(self, access_labels):
        return {}

    def access_request_data(self, request, is_group=False):
        machineList = []
        for key, value in helpers.ssh_machine_list.items():
            if key == "hostname" and value == "ip":
                continue
            machineList.append({"name": key, "tagname": key, "ip": value})
        data = {'machineList': machineList}
        return data

    def revoke(self, user, user_identity, label, request):
        """revokes the access for the user to the resource specified in the label and
        sends an email to the user and the module owners with the details of the access.
        If the user does not have access to the resource, the request is rejected.

        Args:
            user (User): User whose access is being changed
            label (str): Label of the request
            request (UserAccessMapping): Access mapping that repesents the User Access

        Returns:
            bool: True if the request is approved, False otherwise
        """
        is_revoked, error_message = helpers.sshHelper([label], user_identity, user, "revoke")

        if not is_revoked:
            logger.error(
                "Something went wrong while revoking the %s from group %s: %s"
                % (user.email, label, str(error_message))
            )
            return False

        label_desc = self.get_label_desc(label)
        try:
            self.__send_revoke_email(user, request.request_id, label_desc)
            return True
        except Exception as e:
            logger.error(
                "%s: Could not send email for error %s", {self.tag()}, {str(e)}
            )
            return False

    def validate_request(self, access_labels_data, request_user, is_group=False):
        """validates the access request for the user to the resource specified in the label
        and sends an email to the user and the module owners with the details of the access.
        If the user does not have access to the resource, the request is rejected.

        Args:
            access_labels_data (array): Array of access labels
            request_user (User): User whose access is being changed
            is_group (bool, optional): If the request is for a group. Defaults to False.

        Returns:
            bool: True if the request is approved, False otherwise
        """
        valid_access_label_array = []

        for label_data in access_labels_data:
            for machine in label_data["selected_machines"]:
                hostname = machine.split(",", 1)[0]
                ip = machine.split(",", 1)[1]
                label = {
                    "machine": hostname,
                    "access_level": label_data["accessLevel"],
                    "ip": ip
                }
                valid_access_label_array.append(label)
            
            if label_data["other_machines"]:
                label_data["other_machines"] = label_data["other_machines"].split(",")
            
            for other_machine in label_data["other_machines"]:
                label = {
                    "machine": "other",
                    "access_level": label_data["accessLevel"],
                    "ip": other_machine
                }
                valid_access_label_array.append(label)

        return valid_access_label_array

    def fetch_access_request_form_path(self):
        """returns the html form template for filling access path

        Returns:
            str: path of the html template
        """
        return "ssh/access_request_form.html"

    def access_desc(self):
        """description of the access module

        Returns:
            str: description of the aws access module
        """
        return "SSH Machine Access"

    def match_keywords(self):
        """keywords that can be used to search for this module

        Returns:
            list: list of keywords
        """
        return ["ssh", "machine", "access"]

    def tag(self):
        """tag for the SSH access module

        Returns:
            str: tag for the SSH access module
        """
        return "ssh"
    
    def get_identity_template(self):
        return 'ssh/identity_form.html'

    def verify_identity(self, request, email):
        ssh_public_key = request["ssh_pub_key"]
        return {"ssh_public_key": ssh_public_key}
    
    def can_auto_approve(self):
        return False

    def access_types(self):
        return []


def get_object():
    """returns SSH access module object

    Returns:
        object: SSH access module object
    """
    return SSHAccess()
