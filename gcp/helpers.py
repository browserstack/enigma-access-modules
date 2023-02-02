from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging
from BrowserStackAutomation.settings import ACCESS_MODULES

logger = logging.getLogger(__name__)


def get_gcp_domain_details(domain_id):
    for domain in ACCESS_MODULES["gcp_access"]["domains"]:
        if domain["domain_id"] == domain_id:
            return domain

    return {}


def get_gcp_client(domain_id):
    domain = get_gcp_domain_details(domain_id)
    SCOPES = ["https://www.googleapis.com/auth/admin.directory.group"]

    credentials = service_account.Credentials.from_service_account_file(
        domain["service_account_path"], scopes=SCOPES, subject=domain["admin_id"]
    )

    return build("admin", "directory_v1", credentials=credentials)


def grant_gcp_access(group_id, domain_id, user_email):
    try:
        client = get_gcp_client(domain_id)
        client.members().insert(
            groupKey=group_id,
            body={
                "kind": "admin#directory#member",
                "email": user_email,
                "role": "MEMBER",
            },
        ).execute()
        return (True, "")
    except Exception as e:
        logger.exception("Exception while adding user to a GCP group" + str(e))
        if hasattr(e, "reason") and "Member already exists" in e.reason:
            return (True, "")
        return (False, str(e))


def revoke_gcp_access(group_id, domain_id, user_email):
    try:
        client = get_gcp_client(domain_id)
        client.members().delete(groupKey=group_id, memberKey=user_email).execute()

        return (True, "")
    except Exception as e:
        logger.exception("Exception while removing group from GCP group" + str(e))
        return (False, str(e))


def get_gcp_groups(domain_id, page_token=None):
    client = get_gcp_client(domain_id)
    try:
        result = (
            client.groups()
            .list(domain=domain_id, pageToken=page_token, maxResults=200)
            .execute()
        )

        return (result.get("groups"), result.get("nextPageToken"))
    except Exception as e:
        logger.exception(
            "Something went wrong while fetching the GCP groups: " + str(e)
        )
        return False, False


def gcp_group_exists(domain_id, group_id):
    client = get_gcp_client(domain_id)
    try:
        client.groups().get(groupKey=group_id).execute()
    except Exception as e:
        logger.exception(f"Couldnt find the Group with group_id: {group_id}")
        logger.exception(str(e))
        return False
    return True


def get_gcp_domains():
    domains = []
    for account in ACCESS_MODULES["gcp_access"]["domains"]:
        domains.append(account["domain_id"])

    return domains
