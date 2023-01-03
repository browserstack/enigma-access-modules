from BrowserStackAutomation.settings import ACCESS_MODULES
import pytest
from . import access


def test_Confluence(mocker, requests_mock):
  confluence_access = access.Confluence(True)

  userMock = mocker.MagicMock()
  userMock.email = "test@example.com"
  userMock.username = "user"
  userMock.confluenceId = "123"
  
  assert type(confluence_access.get_extra_fields()) == list
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
  mocker.patch("Access.helpers.save_meta_data", return_value="")
  permission = {"key": "read", "target": "space"}
  mocker.patch("Access.helpers.get_meta_data", return_value=[{"permission": permission, "permission_id": "1234"}])
  resp = confluence_access.approve(userMock, label1, "test", "123123")
  assert resp == True

  resp = confluence_access.revoke(userMock, label1)

