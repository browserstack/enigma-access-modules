import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
from access import logger


def get_gcp_client(path):
  SCOPES = ["https://www.googleapis.com/auth/admin.directory.group"]

  credentials = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)

  return build("admin", "directory_v1", credentials=credentials)


PATH = './client_secret.json'
def grant_gcp_access(groupId, userEmail):
  try:
    client = get_gcp_client(PATH)
    client.members().insert(
      groupKey=groupId,
      body={
        "kind": "admin#directory#member",
        "email": userEmail,
        "role": "MEMBER"
      }
    ).execute()
    return True
  except Exception as e:
    logger.error("Error while adding user to group: %s", str(e))
    return False

def revoke_gcp_access(groupId, userEmail):
  try:
    client = get_gcp_client(PATH)
    client.members().delete(
      groupKey=groupId,
      memberKey=userEmail
    ).execute()

    return True
  except Exception as e:
    logger.error("Error while removing the user from the group: %s", str(e))
    return False

def get_gcp_groups():
  client = get_gcp_client(PATH)
  client.groups().list()
  return True
