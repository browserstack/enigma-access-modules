import logging

from googleapiclient.discovery import build
from google.oauth2 import service_account

from enigma_automation.settings import ACCESS_MODULES
from . import constants

logger = logging.getLogger(__name__)


def get_gcp_domain_details(domain_id):
    """Gets the GCP domains details.

    Args:
        domain_id (str): Domain ID of the GCP account.

    Returns:
        dict: GCP Domain.
    """
    for domain in ACCESS_MODULES[constants.GCP_ACCESS_TAG]["domains"]:
        if domain["domain_id"] == domain_id:
            return domain

    return {}


def get_gcp_client(domain_id):
    """Gets GCP client for api access.

    Args:
        domain_id (str): GCP Domain ID.

    Returns:
        client: GCP Session client.
    """
    domain = get_gcp_domain_details(domain_id)
    SCOPES = ["https://www.googleapis.com/auth/admin.directory.group"]

    credentials = service_account.Credentials.from_service_account_file(
        domain["service_account_path"], scopes=SCOPES, subject=domain["admin_id"]
    )

    return build("admin", "directory_v1", credentials=credentials)


def grant_gcp_access(group_id, domain_id, user_email):
    """Make GCP API call to grant access to user to a group.

    Args:
        group_id (str): GroupID of the GCP group.
        domain_id (str): Domain ID of the GCP domain.
        user_email (str): Email Address of the user.

    Returns:
        bool: True if access grant succeeds. False if access grant fails.
    """
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
        logger.exception("Exception while adding user to a GCP group: " + str(e))
        if hasattr(e, "reason") and "Member already exists" in e.reason:
            return (True, "")
        return (False, str(e))


def revoke_gcp_access(group_id, domain_id, user_email):
    """Make GCP API call to revoke access to a user to a group.

    Args:
        group_id (str): GroupID of the GCP group.
        domain_id (str): Domain ID of the GCP domain.
        user_email (str): Email Address of the user.

    Returns:
        bool: True if the revoke succeeds. False if the revoke fails
    """
    try:
        client = get_gcp_client(domain_id)
        client.members().delete(groupKey=group_id, memberKey=user_email).execute()

        return (True, "")
    except Exception as e:
        logger.exception("Exception while removing group from GCP group: " + str(e))
        return (False, str(e))


def get_gcp_groups(domain_id, page_token=None):
    """Gets the list of GCP Groups.

    Args:
        domain_id (str): Domain ID of the GCP domain.
        page_token (str, optional): Page Token. Defaults to None.

    Returns:
        list: List of the GCP groups.
    """
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
        return None, False


def gcp_group_exists(domain_id, group_id):
    """Checks if the GCP group exists.

    Args:
        domain_id (str): GCP Domain ID.
        group_id (str): GCP Group ID.

    Returns:
        bool: Returns True if the Group exists, False if the Group does not exists.
    """
    client = get_gcp_client(domain_id)
    try:
        client.groups().get(groupKey=group_id).execute()
    except Exception as e:
        logger.exception(f"Couldnt find the Group with group_id: {group_id}")
        logger.exception(str(e))
        return False
    return True


def get_gcp_domains():
    """Get the list of GCP domains.

    Returns:
        dict: Gets the list of GCP domains.
    """
    domains = []
    for account in ACCESS_MODULES[constants.GCP_ACCESS_TAG]["domains"]:
        domains.append(account["domain_id"])

    return domains
