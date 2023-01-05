from BrowserStackAutomation.settings import ACCESS_MODULES
import pytest
from . import access


class MockRequest():
  def __init__(self):
    self.request_id = ""
    self.meta_data = {"confluence": [{'permission': {'key': 'read', 'target': 'space'}, 'permission_id': '1409026'}, {'permission': {'key': 'delete', 'target': 'space'}, 'permission_id': '2326529'}, {'permission': {'key': 'create', 'target': 'comment'}, 'permission_id': '1802241'}, 
  {'permission': {'key': 'delete', 'target': 'comment'}, 'permission_id': '2359297'}, {'permission': {'key': 'create', 'target': 'page'}, 'permission_id': '2392065'}, {'permission': {'key': 'create', 'target': 'blogpost'}, 'permission_id': '2424833'}, 
  {'permission': {'key': 'create', 'target': 'attachment'}, 'permission_id': '2359303'}, {'permission': {'key': 'delete', 'target': 'page'}, 'permission_id': '2457601'}, {'permission': {'key': 'delete', 'target': 'blogpost'}, 'permission_id': '2490369'},
  {'permission': {'key': 'delete', 'target': 'attachment'}, 'permission_id': '2523137'}, {'permission': {'key': 'export', 'target': 'space'}, 'permission_id': '2686977'}, {'permission': {'key': 'administer', 'target': 'space'}, 'permission_id': '2392075'}, 
  {'permission': {'key': 'archive', 'target': 'page'}, 'permission_id': '2424845'}, {'permission': {'key': 'restrict_content', 'target': 'space'}, 'permission_id': '2719745'}]}
  
  def updateMetaData(self, a, b):
    return True

def test_Confluence(mocker, requests_mock):
  confluence_access = access.Confluence()

  userMock = mocker.MagicMock()
  userMock.email = "test@example.com"
  userMock.username = "user"
  userMock.confluenceId = "123"

  request = MockRequest()
  
  assert type(confluence_access.grant_owner()) == list
  assert type(confluence_access.revoke_owner()) == list
  assert type(confluence_access.access_mark_revoke_permission("")) == list
  assert type(confluence_access.email_targets(userMock)) == list
  assert type(confluence_access.auto_grant_email_targets(userMock)) == list


  form_label_1 = [{
    "accessWorkspace": "test",
    "confluenceAccessType": "View Access",
  }]
  form_label_2 = [{
    "accessWorkspace": "test 2",
    "confluenceAccessType": "Edit Access",
  }]

  label1 = confluence_access.validate_request(form_label_1, userMock, False)
  label2 = confluence_access.validate_request(form_label_2, userMock, False)

  assert label1[0] == {"data": {"accessWorkspace": "test", "confluenceAccessType": "View Access"}, "access_workspace": "test", "access_type": "View Access"}
  assert label2[0] == {"data": {"accessWorkspace": "test 2", "confluenceAccessType": "Edit Access"}, "access_workspace": "test 2", "access_type": "Edit Access"}

  label_desc = confluence_access.get_label_desc(label1[0])

  assert label_desc == "Confluence access for Workspace: test. Access Type: View Access"

  combine_label_desc = confluence_access.combine_labels_desc(label1)

  assert combine_label_desc == "Confluence access for Workspace: test. Access Type: View Access"

  access_types = confluence_access.access_types()

  assert type(access_types) == list
  assert access_types == [ {
      "type": "View Access",
      "desc": "View Access"
    },{
      "type": "Edit Access",
      "desc": "Edit Access"
    },{
      "type": "Admin Access",
      "desc": "Admin Access"
    }]

  requests_mock.post(f'{ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]}/wiki/rest/api/space/test/permission', status_code=200, json={'id': 1234})
  requests_mock.delete(f'{ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]}/wiki/rest/api/space/test/permission/1234', status_code=204)

  mocker.patch("bootprocess.general.emailSES", return_value="")
  resp = confluence_access.approve(userMock, label1, "1234", request)
  assert resp == True

  resp = confluence_access.revoke(userMock, label1[0], request)

