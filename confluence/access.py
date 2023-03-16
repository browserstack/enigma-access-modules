"""Confluence Access Module"""
import json
import logging
from django.template import loader
from requests.auth import HTTPBasicAuth
import requests

from Access.access_modules.base_email_access.access import BaseEmailAccess
from BrowserStackAutomation.settings import ACCESS_MODULES
from bootprocess.general import emailSES

logger = logging.getLogger(__name__)


class Confluence(BaseEmailAccess):
    """Class representing the Confluence access module."""

    urlpatterns = []

    def fetch_access_request_form_path(self):
        """Returns the html form template for filling access path.

        Returns:
            str: Path of the html template.
        """
        return "confluence/access_request_form.html"

    def email_targets(self, user):
        """Returns email targets.

        Args:
            user (User): User whose access is being changed.

        Returns:
            arr: Email address of the User and the module owners.
        """
        return [user.email] + self.grant_owner()

    def validate_request(self, access_labels_data, request_user, is_group=False):
        """Validates the access request.

        Args:
            access_labels_data (str): Access label representing the access requested.
            request_user (User): User requesting the access
            is_group (bool, optional): Whether the access is being requested for a group.
            Defaults to False.

        Returns:
            arr: Array of the access labels for the request access.
        """
        access_workspace = access_labels_data[0]["accessWorkspace"]
        access_type = access_labels_data[0]["confluenceAccessType"]
        valid_access_label_array = []
        for access_label_data in access_labels_data:
            valid_access_label = {"data": access_label_data}
            valid_access_label_array.append(valid_access_label)

        valid_access_label["access_workspace"] = access_workspace
        valid_access_label["access_type"] = access_type
        return valid_access_label_array

    def get_label_desc(self, access_label):
        """Gets the access label descrption.

        Args:
            access_label (str): JSON string representing the access label.

        Returns:
            str: Access label description.
        """
        access_workspace = access_label["access_workspace"]
        access_type = access_label["access_type"]
        return (
            "Confluence access for Workspace: "
            + access_workspace
            + ". Access Type: "
            + access_type
        )

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

    def access_types(self):
        """Returns different types of access for a workspace."""
        return [
            {"type": "View Access", "desc": "View Access"},
            {"type": "Edit Access", "desc": "Edit Access"},
            {"type": "Admin Access", "desc": "Admin Access"},
        ]

    def __approve_space_access(
        self, space_key, permission, subject_identifier, subject_type="user"
    ):
        """Makes confluence API calls and approves access to a confluence space."""
        try:
            auth = HTTPBasicAuth(
                ACCESS_MODULES["confluence_module"]["ADMIN_EMAIL"],
                ACCESS_MODULES["confluence_module"]["API_TOKEN"],
            )
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            payload = json.dumps(
                {
                    "subject": {"type": subject_type, "identifier": subject_identifier},
                    "operation": permission,
                }
            )
            base_url = ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]
            grant_url = f"{base_url}/wiki/rest/api/space/{space_key}/permission"
            response = requests.request(
                "POST", grant_url, data=payload, headers=headers, auth=auth
            )

            if response.status_code == 200:
                return str(json.loads(response.text)["id"])
            if response.status_code == 400:
                return json.loads(response.text)["message"].split(" ")[-1]
            logger.error(
                "Could not approve permission %s for response %s",
                {str(permission)},
                {str(response.text)},
            )
            return False
        except Exception as ex:
            logger.error(
                "Could not approve permission %s for error %s",
                {str(permission)},
                {str(ex)},
            )
            return False

    def __revoke_space_access(self, space_key, permission_id):
        """Makes confluence API calls and revokes access to a confluence space."""
        try:
            auth = HTTPBasicAuth(
                ACCESS_MODULES["confluence_module"]["ADMIN_EMAIL"],
                ACCESS_MODULES["confluence_module"]["API_TOKEN"],
            )
            base_url = ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]
            revoke_url = (
                f"{base_url}/wiki/rest/api/space/{space_key}/permission/{permission_id}"
            )
            response = requests.request("DELETE", revoke_url, auth=auth)
            if response.status_code != 204:
                return False

            return True

        except Exception as ex:
            logger.error(
                "Could not approve permission %s for error %s",
                {str(permission_id)},
                {str(ex)},
            )
            return False

    def access_request_data(self, request, is_group=False):
        """Creates a dictionary of confluence workspaces.

        Args:
            request (dict): A request form representing the http form request.
            is_group (bool, optional): Whether the access is requested.
            for an Enigma Group. Defaults to False.

        Returns:
            dict: Dictionary of enigma workspace
        """
        available_spaces = {}
        available_spaces["spaces"] = []
        auth = HTTPBasicAuth(
            ACCESS_MODULES["confluence_module"]["ADMIN_EMAIL"],
            ACCESS_MODULES["confluence_module"]["API_TOKEN"],
        )
        start = 0
        limit = 25
        while True:
            response = requests.request(
                "GET",
                ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]
                + "/wiki/rest/api/space?type=global&start="
                + str(start)
                + "&limit="
                + str(limit)
                + "",
                auth=auth,
            )
            if response.status_code == 404:
                logger.error(
                    """Error Occured while featching confluence spaces,
                     please check values in config.json"""
                )
                return {"spaces": []}
            spaces = json.loads(response.text)
            for space in spaces["results"]:
                available_spaces["spaces"].append(
                    {"key": space["key"], "name": space["name"]}
                )
            start += spaces["size"]
            if spaces["size"] < spaces["limit"]:
                break

        return available_spaces

    def __get_accesses_with_type(self, access_type):
        view_permissions = [
            {"key": "read", "target": "space"},
            {"key": "delete", "target": "space"},
            {"key": "create", "target": "comment"},
            {"key": "delete", "target": "comment"},
        ]
        edit_permissions = view_permissions + [
            {"key": "create", "target": "page"},
            {"key": "create", "target": "blogpost"},
            {"key": "create", "target": "attachment"},
            {"key": "delete", "target": "page"},
            {"key": "delete", "target": "blogpost"},
            {"key": "delete", "target": "attachment"},
        ]
        admin_permissions = edit_permissions + [
            {"key": "export", "target": "space"},
            {"key": "administer", "target": "space"},
            {"key": "archive", "target": "page"},
            {"key": "restrict_content", "target": "space"},
        ]
        if access_type == "Admin Access":
            return admin_permissions
        if access_type == "Edit Access":
            return edit_permissions
        return view_permissions

    def approve(
        self, user, labels, approver, request, is_group=False, auto_approve_rules=None
    ):
        """Approves a users access request.

        Args:
            user (User): User whose access is being approved
            labels (str): Access Label that respesents the access to be approved
            approver (User): User who is approving the access
            request (UserAccessMapping): Access mapping that repesents the User Access
            is_group (bool, optional): Whether the access is requested for a User or a Group.
                                       Defaults to False.
            auto_approve_rules (str, optional): Rules for auto approval. Defaults to None.

        Returns:
            bool: True if the access approval is success, False in case of failure
        """
        permissions = []
        access_type = ""
        for label in labels:
            if "View Access" in label["access_type"]:
                access_type = "View Access"
                permissions = self.__get_accesses_with_type("View Access")
            elif "Edit Access" in label["access_type"]:
                access_type = "Edit Access"
                permissions = self.__get_accesses_with_type("Edit Access")
            elif "Admin Access" in label["access_type"]:
                access_type = "Admin Access"
                permissions = self.__get_accesses_with_type("Admin Access")

            approve_result = []

            for permission in permissions:
                response = self.__approve_space_access(
                    label["access_workspace"],
                    permission,
                    user.confluenceId,
                    subject_type="user",
                )
                if response is False:
                    return False

                approve_result.append(
                    {"permission": permission, "permission_id": response}
                )

            request.update_meta_data("confluence", approve_result)

        try:
            self.__send_approve_email(user, request.request_id, access_type, approver)
            return True
        except Exception as ex:
            logger.error("Could not send email for error %s", str(ex))
            return False

    def __send_approve_email(self, user, request_id, access_type, approver):
        """Generates and sends email in access grant."""
        targets = self.email_targets(user)
        subject = f"""Approved Access: {request_id} for access to
        {self.access_desc()} for user {user.email}"""

        body = self.__generate_string_from_template(
            filename="approve_email.html",
            access_type=access_type,
            user_email=user.email,
            approver=approver,
        )
        emailSES(targets, subject, body)

    def __generate_string_from_template(self, filename, **kwargs):
        template = loader.get_template(filename)
        vals = {}
        for key, value in kwargs.items():
            vals[key] = value
        return template.render(vals)

    def __send_revoke_email(self, user, label_desc):
        """Generates and sends email in for access revoke."""
        email_targets = self.email_targets(user)
        email_subject = f"Revoke Request: {label_desc} for {user.email}"
        email_body = ""
        emailSES(email_targets, email_subject, email_body)

    def revoke(self, user, label, request):
        """Revoke confluence workspace access

        Args:
            user (User): User whose access is to be revoked.
            label (str): Access label representing the access to be revoked.
            request (UserAccessMapping): UserAccessMapping representing the access.

        Returns:
            bool: True is the revoke is success. False if the revoke Fails.
        """
        permissions = request.meta_data["confluence"]

        for permission in permissions[::-1]:
            response = self.__revoke_space_access(
                label["access_workspace"], permission["permission_id"]
            )
            if response is False:
                logger.error("could not revoke access for %s", str(permission))
                return False

        label_desc = self.get_label_desc(label)
        try:
            self.__send_revoke_email(user, label_desc)
            return True
        except Exception as ex:
            logger.error("Could not send email for error %s", str(ex))
            return False

    def access_desc(self):
        """Description of the access module.

        Returns:
            str: Description of the confluence access module.
        """
        return "Confluence Access Module"

    def tag(self):
        """Returns confluence access tag."""
        return "confluence_module"


def get_object():
    """Returns instance Confluence Access Module."""
    return Confluence()
