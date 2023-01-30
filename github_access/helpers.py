import json,requests
import logging
from BrowserStackAutomation.settings import ACCESS_MODULES

logger = logging.getLogger(__name__)
default_branch = [f"master",f"main"]

def get_user(username):
  if not _get_user(username):
      return False
  return True

def _get_user(username):
  headers = {'Authorization' : 'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"]}
  GET_USER_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/users/{username}'
  response = requests.get(GET_USER_URL, headers=headers)
  if response.status_code==200:
      return True
  return False

def get_repo(repo):
  if not _get_repo(repo):
      return False
  return True

def _get_repo(repo):
  headers = {'Authorization' : 'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"]}
  GET_REPO_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/repos/{repo}'
  response = requests.get(GET_REPO_URL,headers=headers)
  if response.status_code==200:
      return True
  return False

def get_org(username):
  if not _get_org(username):
    return False
  return True

def _get_org(username):
  headers = {'Authorization' : 'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"]}
  GET_ORG_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/orgs/{(ACCESS_MODULES["github_module"]["GITHUB_ORG"]).lower()}/members/{username}'
  response = str(requests.get(GET_ORG_URL, headers=headers))
  if '204' not in response:
      return False
  else:
      return True

def get_org_invite(username):
  if not _get_org_invite(username):
    return False
  return True

def _get_org_invite(username):
  headers = {'Authorization' : 'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"]}
  GET_ORG_INVITE_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/orgs/{(ACCESS_MODULES["github_module"]["GITHUB_ORG"]).lower()}/invitations'
  response = requests.get(GET_ORG_INVITE_URL, headers=headers)
  return username in [member['login'] for member in response.json()]

def put_user(username):
  if not _put_user(username):
    return False
  return True

def _put_user(username):
  headers = {'Authorization' : 'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"]}
  PUT_USER_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/orgs/{(ACCESS_MODULES["github_module"]["GITHUB_ORG"]).lower()}/memberships/{username}'
  response = str(requests.put(PUT_USER_URL, headers=headers))
  if '200' not in response:
      return False
  else:
      return True

def _get_branch_protection_enabled(repo, branch):
    headers = {'Authorization': f'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"],'Accept': f'application/vnd.github.v3+json' }
    GET_BRANCH_PTOTECTION_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/repos/{repo}/branches/{branch}/protection'
    response = requests.get(GET_BRANCH_PTOTECTION_URL, headers=headers)
    protected_branch_data = response.json()
    if 'restrictions' in protected_branch_data and 'required_pull_request_reviews' in protected_branch_data:
      return True
    return False

def grant_access(repo, access_level, username):
  response = ""
  try:
    headers = {'Authorization' : 'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"]}
    repo = repo.strip()
    if get_repo(repo) == False:
      logger.debug('Skipping git access for '+repo+' for user '+username+' because repo does not exist anymore')
      return True
    if access_level == 'merge':
      headers = {'Authorization': f'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"],'Accept': f'application/vnd.github.v3+json','Content-Type': f'application/json' }
      for branch in default_branch:
        response = ""
        GET_USERS_ACCESS_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/repos/{repo}/branches/{branch}/protection/restrictions/users'
        res = requests.get(GET_USERS_ACCESS_URL, headers=headers)
        protected_branch_data = res.json()
        if _get_branch_protection_enabled(repo, branch):
          logger.debug(protected_branch_data)
          data = [username]
          POST_USERS_ACCESS_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/repos/{repo}/branches/{branch}/protection/restrictions/users'
          res = requests.post(POST_USERS_ACCESS_URL,headers=headers, data=json.dumps(data))
          response = res.json()
          logger.debug(response)
          if "Response [200]" in response:
            logger.debug(response)
            return True
        elif "message" in protected_branch_data and protected_branch_data["message"] ==  "Push restrictions not enabled":
          response += f"404 - Push Restriction is not enabled for {repo} Repo. Please contact Github Admin to enable branch protection for this repo"
    else:
      payload = {'permission': access_level}
      PUT_COLLABORATOR_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/repos/{repo}/collaborators/{username}'
      res = requests.put(PUT_COLLABORATOR_URL,headers=headers, data=json.dumps(payload))
      response += str(res)
      response +="\n"
      logger.debug(response)

    if '404' in response:
        return False
    return True
  except Exception as e:
      logger.error("Error while granting repo access to user "+username)
      logger.error(str(e))
      return False

def get_org_repo_list():
    repoList=[]
    headers = {'Authorization': f'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"],'Accept': f'application/vnd.github.v3+json' }
    GET_ORG_REPOS_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/orgs/{ACCESS_MODULES["github_module"]["GITHUB_ORG"].lower()}/repos'
    response = requests.get(GET_ORG_REPOS_URL, headers=headers)
    if response.status_code==200:
      user_orgs_data = response.json()
      for orgs in user_orgs_data:
        if "full_name" in orgs:
          repoList.append(orgs["full_name"])
      logger.debug('Collected All Repos')
      return repoList
    return []

def revoke_access(username, repo = None):
  if not _revoke_github_user(username, repo):
    return False
  return True

def _revoke_github_user(username, repo):
  headers = {'Authorization' : 'token %s' % ACCESS_MODULES["github_module"]["GITHUB_TOKEN"]}
  DELETE_ACCESS_URL = ""
  if repo is None:
    DELETE_ACCESS_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/orgs/{ACCESS_MODULES["github_module"]["GITHUB_ORG"].lower()}/memberships/{username}'
  else:
    DELETE_ACCESS_URL = f'{ACCESS_MODULES["github_module"]["GITHUB_BASE_URL"]}/repos/{ACCESS_MODULES["github_module"]["GITHUB_ORG"].lower()}/{repo}/collaborators/{username}'

  response = requests.delete(DELETE_ACCESS_URL, headers=headers)
  if response.status_code not in [200, 404, 204]:
    return False
  else:
    return True
