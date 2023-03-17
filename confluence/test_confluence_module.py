"""unit tests for the confluence acces module"""
from . import access
from EnigmaAutomation.settings import ACCESS_MODULES


class MockRequest:
    """Mock HTTP Request for confluence"""
    def __init__(self):
        self.request_id = ""
        self.meta_data = {
            "confluence": [
                {
                    "permission": {"key": "read", "target": "space"},
                    "permission_id": "1409026",
                },
                {
                    "permission": {"key": "delete", "target": "space"},
                    "permission_id": "2326529",
                },
                {
                    "permission": {"key": "create", "target": "comment"},
                    "permission_id": "1802241",
                },
                {
                    "permission": {"key": "delete", "target": "comment"},
                    "permission_id": "2359297",
                },
                {
                    "permission": {"key": "create", "target": "page"},
                    "permission_id": "2392065",
                },
                {
                    "permission": {"key": "create", "target": "blogpost"},
                    "permission_id": "2424833",
                },
                {
                    "permission": {"key": "create", "target": "attachment"},
                    "permission_id": "2359303",
                },
                {
                    "permission": {"key": "delete", "target": "page"},
                    "permission_id": "2457601",
                },
                {
                    "permission": {"key": "delete", "target": "blogpost"},
                    "permission_id": "2490369",
                },
                {
                    "permission": {"key": "delete", "target": "attachment"},
                    "permission_id": "2523137",
                },
                {
                    "permission": {"key": "export", "target": "space"},
                    "permission_id": "2686977",
                },
                {
                    "permission": {"key": "administer", "target": "space"},
                    "permission_id": "2392075",
                },
                {
                    "permission": {"key": "archive", "target": "page"},
                    "permission_id": "2424845",
                },
                {
                    "permission": {"key": "restrict_content", "target": "space"},
                    "permission_id": "2719745",
                },
            ]
        }

    def update_meta_data(self, param1, param2):
        """mock method that defaults to True"""
        return True


def test_confluence(mocker, requests_mock):
    """unit test for the confluence access module methods"""
    confluence_access = access.Confluence()

    user_mock = mocker.MagicMock()
    user_mock.email = "test@example.com"
    user_mock.username = "user"
    user_mock.confluenceId = "123"

    request = MockRequest()

    assert isinstance(confluence_access.email_targets(user_mock)) == list
    assert isinstance(confluence_access.auto_grant_email_targets(user_mock)) == list

    form_label_1 = [
        {
            "accessWorkspace": "test",
            "confluenceAccessType": "View Access",
        }
    ]
    form_label_2 = [
        {
            "accessWorkspace": "test 2",
            "confluenceAccessType": "Edit Access",
        }
    ]

    label1 = confluence_access.validate_request(form_label_1, user_mock, False)
    label2 = confluence_access.validate_request(form_label_2, user_mock, False)

    assert label1[0] == {
        "data": {"accessWorkspace": "test", "confluenceAccessType": "View Access"},
        "access_workspace": "test",
        "access_type": "View Access",
    }
    assert label2[0] == {
        "data": {"accessWorkspace": "test 2", "confluenceAccessType": "Edit Access"},
        "access_workspace": "test 2",
        "access_type": "Edit Access",
    }

    label_desc = confluence_access.get_label_desc(label1[0])

    assert (
        label_desc == "Confluence access for Workspace: test. Access Type: View Access"
    )

    combine_label_desc = confluence_access.combine_labels_desc(label1)

    assert (
        combine_label_desc
        == "Confluence access for Workspace: test. Access Type: View Access"
    )

    access_types = confluence_access.access_types()

    assert isinstance(access_types) == list
    assert access_types == [
        {"type": "View Access", "desc": "View Access"},
        {"type": "Edit Access", "desc": "Edit Access"},
        {"type": "Admin Access", "desc": "Admin Access"},
    ]

    base_url = ACCESS_MODULES["confluence_module"]["CONFLUENCE_BASE_URL"]

    grant_url = f"{base_url}/wiki/rest/api/space/test/permission"

    requests_mock.post(
        grant_url,
        status_code=200,
        json={"id": 1234},
    )
    revoke_url = f"{base_url}/wiki/rest/api/space/test/permission/1234"
    requests_mock.delete(
        revoke_url,
        status_code=204,
    )

    mocker.patch("bootprocess.general.emailSES", return_value="")
    resp = confluence_access.approve(user_mock, label1, "1234", request)
    assert resp is True

    resp = confluence_access.revoke(user_mock, label1[0], request)

    assert resp is True
