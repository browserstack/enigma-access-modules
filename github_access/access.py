import logging

from Access.base_email_access.access import BaseEmailAccess
from Access.access_modules.github_access.helpers import (
    get_org,
    get_org_invite,
    get_org_repo_list,
    get_repo,
    get_user,
    grant_access,
    put_user,
    revoke_access,
    is_email_valid,
)
from . import constants
from bootprocess.general import emailSES
from django.template import loader
from django.shortcuts import render

logger = logging.getLogger(__name__)


class GithubAccess(BaseEmailAccess):
    ACCESS_LABEL = "repository_access"
    urlpatterns = []

    def email_targets(self, user):
        return [user.email] + self.grant_owner()

    def revoke(self, user, user_identity, label, request):
        user_name = user_identity.identity["username"]
        result = revoke_access(user_name, label["repository"])

        self.__send_revoke_email(user, label)
        return result


    def offboard_github(self, github_username):
        return revoke_access(github_username)

    available = True

    def approve(
        self,
        user_identity,
        labels,
        approver,
        request,
        is_group=False,
        auto_approve_rules=None,
    ):
        return_value = True
        error_message = ""
        label = labels[0]
        user_name = user_identity.identity["username"]
        if not get_user(user_name):
            logger.error(constants.USER_NOT_FOUND % user_name)
            error_message = constants.USER_NOT_FOUND % user_name
            return_value = False

        if return_value and not get_org(user_name):
            if not get_org_invite(user_name):
                if put_user(user_name):
                    logger.debug("Invited %s to join github organisation" % user_name)
                    error_message = constants.INVITE_USER_SUCCESS % user_name
                    return_value = False
                else:
                    logger.error(constants.INVITE_USER_FAILED % user_name)
                    error_message = constants.INVITE_USER_FAILED % user_name
                return_value = False
            else:
                error_message = constants.ALREADY_INVITED_ERROR.format(user_name)
                return_value = False

        if return_value and label["action"] == self.ACCESS_LABEL:
            if not get_repo(label["repository"]):
                logger.error(constants.REPO_NOT_FOUND % label["repository"])
                error_message = constants.REPO_NOT_FOUND % label["repository"]
                return_value = False
            else:
                if return_value and grant_access(
                    label["repository"], label["access_level"], user_name
                ):
                    logger.debug(
                        "Added %s access to user %s for repo %s"
                        % (label["access_level"], user_name, label["repository"])
                    )
                else:
                    logger.error(
                        constants.GRANT_ACCESS_FAILED % (user_name, label["repository"])
                    )
                    error_message = constants.GRANT_ACCESS_FAILED % (
                        user_name,
                        label["repository"],
                    )
                    return_value = False

        label_desc = self.combine_labels_desc(labels)

        try:
            self.__send_approve_email(
                user_identity.user,
                label_desc,
                request.request_id,
                approver,
                return_value,
                auto_approve_rules,
            )
        except Exception as e:
            logger.error("Could not send email for error %s" % str(e))
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
        email_subject = constants.GRANT_REQUEST % (
            request_id,
            self.access_desc(),
            user.email,
        )
        email_body = self.__generate_string_from_template(
            filename="access_email_template.html",
            status=grant_status,
            auto_approve=auto_approve_rules,
            request_id=request_id,
            user_email=user.email,
            access_desc=self.access_desc(),
            access_meta=label_desc,
            approver=approver,
        )

        emailSES(email_targets, email_subject, email_body)


    def __send_revoke_email(
        self, user, label,
    ):
        email_targets = self.email_targets(user)

        label_desc = self.get_label_desc(label)
        email_subject = constants.REVOKE_REQUEST % (label_desc, user.email)

        email_body = ""

        if result:
            logger.debug(constants.REVOKE_SUCCESS % (user.email, label["repository"]))
            email_body = constants.REVOKE_SUCCESS % (user.email, label["repository"])
        else:
            logger.error(constants.REVOKE_FAILED % (user.email, label["repository"]))
            email_body = constants.REVOKE_FAILED % (user.email, label["repository"])

        try:
            emailSES(email_targets, email_subject, email_body)
            return True
        except Exception as e:
            logger.exception("Could not send email for error %s" % str(e))
            return False

    def get_label_desc(self, access_label):
        if access_label["action"] == self.ACCESS_LABEL:
            repository = access_label["repository"]
            access_level = access_label["access_level"]
            return access_level + " access for github repo - " + repository

        return ""

    def combine_labels_desc(self, access_labels):
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
        return "github_access"

    def fetch_access_request_form_path(self):
        return "github_access/access_request_form.html"

    def access_request_data(self, request, is_group=False):
        repo_data = [repo for repo in get_org_repo_list()]
        data = {"githubRepoList": repo_data}
        return data

    def fetch_access_approve_email(self, request, data):
        context_details = {
            "approvers": {
                "primary": data["approvers"]["primary"],
                "other": data["approvers"]["other"],
            },
            "requestId": data["requestId"],
            "user": request.user,
            "requestData": data["request_data"],
            "accessType": self.tag(),
            "accessDesc": self.access_desc(),
            "isGroup": data["is_group"],
        }
        return str(
            render(
                request, "base_email_access/accessApproveEmail.html", context_details
            )
        )

    def validate_request(self, access_labels_data, request_user, is_group=False):
        valid_access_label_array = []
        valid_access_label = {}
        for repo_name in access_labels_data[0]["repoList"]:
            access_level = access_labels_data[0]["accessLevel"]

            if len(repo_name) == 0:
                raise Exception("Repo not found")
            valid_access_label = {}
            valid_access_label["action"] = self.ACCESS_LABEL
            valid_access_label["access_level"] = access_level

            valid_access_label["repository"] = repo_name
            valid_access_label_array.append(valid_access_label)

        return valid_access_label_array

    def get_identity_template(self):
        return "github_access/identity_form.html"

    def verify_identity(self, request, email):
        user_name = request["name"]
        if not is_email_valid(user_name, email):
            logger.error(constants.USER_IDENTITY_NOT_FOUND % user_name)
            return {}

        return {"username": user_name}

    def match_keywords(self):
        return ["github", "git"]


def get_object():
    return GithubAccess()
