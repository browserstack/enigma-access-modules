from googleapiclient.discovery import build
from google.oauth2 import service_account
from BrowserStackAutomation.settings import ACCESS_MODULES


def get_gcp_domain_details(domain_id):
    for domain in ACCESS_MODULES["gcp_module"]["domains"]:
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
        if hasattr(e, "reason") and "Member already exists" in e.reason:
            return (True, "")
        return (False, str(e))


def revoke_gcp_access(group_id, domain_id, user_email):
    try:
        client = get_gcp_client(domain_id)
        client.members().delete(groupKey=group_id, memberKey=user_email).execute()

        return (True, "")
    except Exception as e:
        return (False, str(e))


def get_gcp_groups(domain_id):
    client = get_gcp_client(domain_id)
    groups = []
    pageToken = None
    while True:

        result = client.groups().list(domain=domain_id, pageToken=pageToken).execute()

        if "groups" not in result:
            break

        groups = groups + result["groups"]
        if "nextPageToken" not in result:
            break

        pageToken = result["nextPageToken"]

    return groups


def get_gcp_domains():
    domains = []
    for account in ACCESS_MODULES["gcp_module"]["domains"]:
        domains.append(account["domain_id"])

    return domains
