"""SSH access module — OS command injection regression tests (GHSA-grpj-9ghj-xhv8).

These tests lock in the fix for the second-order OS command injection where a
requester-controlled SSH public key / username was interpolated verbatim into
remote shell commands. They cover both layers of the fix:

  * source-side validation (``is_valid_ssh_public_key`` / ``is_valid_username``
    and ``SSHAccess.verify_identity``), and
  * sink-side ``shlex.quote`` hardening in the ``connection.sudo`` calls.
"""

import shlex

import pytest

from . import helpers, access


BENIGN_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExampleBenignKeyDataXXXXXX user@laptop"
)
# Command-substitution payload embedded in the key / username fields.
MALICIOUS_KEY = "ssh-ed25519 AAAATEST$(touch /tmp/pwned)attacker@example.com"
MALICIOUS_USERNAME = "app;touch /tmp/pwned"


# --------------------------------------------------------------------------- #
# Pure validators
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "key",
    [
        BENIGN_KEY,
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgExampleRsaBody+/09 me@host",
        "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTY= me@host",
    ],
)
def test_valid_keys_accepted(key):
    assert helpers.is_valid_ssh_public_key(key) is True


@pytest.mark.parametrize(
    "key",
    [
        "",
        None,
        MALICIOUS_KEY,
        "ssh-ed25519 AAAA`whoami` c",
        "ssh-ed25519 AAAA; rm -rf / #",
        "ssh-ed25519 AAAA\ntouch /tmp/pwned",  # newline-smuggled second line
        "not-a-key-type AAAABBBB",
        "ssh-ed25519 AAAA$body more",  # '$' is not valid base64
    ],
)
def test_malicious_or_malformed_keys_rejected(key):
    assert helpers.is_valid_ssh_public_key(key) is False


@pytest.mark.parametrize("username", ["app", "svc_1", "build-agent", "_sys"])
def test_valid_usernames_accepted(username):
    assert helpers.is_valid_username(username) is True


@pytest.mark.parametrize(
    "username",
    ["", None, MALICIOUS_USERNAME, "app$(id)", "../root", "a b", "UPPER", "x" * 40],
)
def test_malicious_or_malformed_usernames_rejected(username):
    assert helpers.is_valid_username(username) is False


# --------------------------------------------------------------------------- #
# Source: verify_identity
# --------------------------------------------------------------------------- #
def test_verify_identity_rejects_malicious_key():
    result = access.SSHAccess().verify_identity({"ssh_pub_key": MALICIOUS_KEY}, "u@x.com")
    assert result == {}


def test_verify_identity_accepts_benign_key():
    result = access.SSHAccess().verify_identity({"ssh_pub_key": BENIGN_KEY}, "u@x.com")
    assert result == {"ssh_public_key": BENIGN_KEY}


# --------------------------------------------------------------------------- #
# Dispatcher: malicious input never reaches a shell
# --------------------------------------------------------------------------- #
def _identity(mocker, ssh_key):
    ident = mocker.MagicMock()
    ident.identity = {"ssh_public_key": ssh_key}
    return ident


def _user(mocker, username):
    user = mocker.MagicMock()
    user.user.username = username
    return user


def test_ssh_helper_rejects_malicious_key_without_connecting(mocker):
    conn = mocker.patch.object(helpers, "get_connection_to_host")
    labels = [{"access_level": "app", "machine": "h", "ip": "127.0.0.1"}]
    ok, msg = helpers.sshHelper(
        labels, _identity(mocker, MALICIOUS_KEY), _user(mocker, "app"), "grant"
    )
    assert ok is False
    assert msg == "Invalid SSH public key"
    conn.assert_not_called()


def test_ssh_helper_rejects_malicious_username_without_connecting(mocker):
    conn = mocker.patch.object(helpers, "get_connection_to_host")
    # access_level "sudo" makes get_username fall back to user.user.username
    labels = [{"access_level": "sudo", "machine": "h", "ip": "127.0.0.1"}]
    ok, msg = helpers.sshHelper(
        labels, _identity(mocker, BENIGN_KEY), _user(mocker, MALICIOUS_USERNAME), "grant"
    )
    assert ok is False
    assert msg == "Invalid username"
    conn.assert_not_called()


# --------------------------------------------------------------------------- #
# Sink hardening: even if validation is bypassed, payloads are shell-quoted
# --------------------------------------------------------------------------- #
def _sudo_commands(conn_mock):
    return [c.args[0] for c in conn_mock.sudo.call_args_list]


def test_add_key_existing_user_quotes_payload(mocker):
    conn = mocker.MagicMock()
    mocker.patch.object(helpers, "get_connection_to_host", return_value=conn)

    helpers.add_key_existing_user("127.0.0.1", MALICIOUS_KEY, "app", "app")

    cmd = _sudo_commands(conn)[0]
    # The raw command-substitution must NOT appear unquoted…
    assert "$(touch /tmp/pwned)" not in cmd.replace(shlex.quote(MALICIOUS_KEY), "")
    # …because the whole key is passed as one shell-quoted token.
    assert shlex.quote(MALICIOUS_KEY) in cmd


def test_add_user_quotes_username_and_key(mocker):
    conn = mocker.MagicMock()
    conn.sudo.return_value.failed = True  # "id <user>" -> user does not exist yet
    mocker.patch.object(helpers, "get_connection_to_host", return_value=conn)

    helpers.add_user("h", "127.0.0.1", MALICIOUS_KEY, MALICIOUS_USERNAME, "sudo")

    cmds = _sudo_commands(conn)
    assert cmds, "expected sudo commands to be issued"
    for cmd in cmds:
        assert "; touch" not in cmd  # bare metacharacter never reaches the shell
        assert "$(touch" not in cmd or shlex.quote(MALICIOUS_KEY) in cmd


def test_replace_user_key_quotes_sed_expression(mocker):
    conn = mocker.MagicMock()
    mocker.patch.object(helpers, "get_connection_to_host", return_value=conn)

    ok, _ = helpers.replace_user_key("h", "127.0.0.1", "", MALICIOUS_KEY, "app")

    cmd = _sudo_commands(conn)[0]
    assert cmd.startswith("sed -i ")
    # sed expression is a single shell-quoted token — no unquoted $()
    assert "$(touch /tmp/pwned)" not in cmd


def test_replace_user_key_rejects_bad_username(mocker):
    conn = mocker.patch.object(helpers, "get_connection_to_host")
    ok, msg = helpers.replace_user_key("h", "127.0.0.1", "", BENIGN_KEY, MALICIOUS_USERNAME)
    assert ok is False
    assert msg == "Invalid username"
