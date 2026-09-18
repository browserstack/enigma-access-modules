""" Helper methods for ssh module """

import re
import shlex
import traceback
import logging
from fabric import Connection

from EnigmaAutomation.settings import ACCESS_MODULES

logger = logging.getLogger(__name__)

global ssh_machine_list
ssh_machine_list = {}

# A POSIX/Linux login name: starts with a lowercase letter or underscore,
# followed by lowercase letters, digits, underscores or hyphens, optionally
# ending with a trailing '$'. Max 32 chars (useradd limit). This is an
# allow-list so that no shell metacharacter (``$(`` , backticks, ``;`` , ``/`` ,
# spaces, ...) can ever reach a remote command via the username.
_USERNAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}\$?$")


class SSHModuleError(Exception):
    """ Custom error class """

    def __init__(self, message):
        self.message = message


def is_valid_username(username):
    """Return True only for a well-formed Linux login name.

    Usernames flow into remote shell commands and filesystem paths
    (``/home/<username>/...``); restricting them to a strict allow-list
    prevents both command injection and path traversal.
    """
    return bool(username) and bool(_USERNAME_RE.match(username))


# An OpenSSH public key line: "<type> <base64-blob>[ optional comment]".
# The key type and base64 body are drawn from fixed character sets, so a valid
# key can never contain shell metacharacters. The optional comment is validated
# separately (below) to keep it free of newlines and shell metacharacters.
_SSH_KEY_TYPE_RE = (
    r"(?:ssh-ed25519|ssh-rsa|ssh-dss|"
    r"ecdsa-sha2-nistp(?:256|384|521)|"
    r"sk-ssh-ed25519@openssh\.com|sk-ecdsa-sha2-nistp256@openssh\.com)"
)
_SSH_KEY_RE = re.compile(
    r"^" + _SSH_KEY_TYPE_RE + r" [A-Za-z0-9+/]+={0,3}( [\x20-\x7e]*)?$"
)


def is_valid_ssh_public_key(ssh_key):
    """Return True only for a single, well-formed OpenSSH public key line.

    Rejects empty values, multi-line input, and anything carrying characters
    outside the ``<type> <base64> <comment>`` grammar. This is the source-side
    guard against OS command injection through the ``ssh_public_key`` field; the
    remote commands additionally ``shlex.quote`` the value as defence in depth.
    """
    if not ssh_key or not isinstance(ssh_key, str):
        return False
    # Reject any newline/carriage-return so a payload cannot smuggle a second
    # authorized_keys line or shell command.
    if "\n" in ssh_key or "\r" in ssh_key:
        return False
    return bool(_SSH_KEY_RE.match(ssh_key.strip()))


def _get_inventory_file_path():
    if "ssh" in ACCESS_MODULES:
        if "inventory_file_path" in ACCESS_MODULES["ssh"]:
            return ACCESS_MODULES["ssh"]["inventory_file_path"]
    raise SSHModuleError("Inventory file path not initialized")


def init():
    """ Initialize the ssh machine list """
    inventory_path = ""
    try:
        inventory_path = _get_inventory_file_path()
    except SSHModuleError as error:
        logger.info(
            "SSHModule: Inventory file path not initialized: %s",
            error,
        )
        return

    with open(inventory_path, mode="r", encoding="utf-8") as file:
        # convert inventory.csv file to dictionary
        # with hostname as key and ip as value
        for line in file.readlines():
            ssh_machine_list[line.split(",")[0]] = line.split(",")[1].strip()


def get_ip_from_hostname(hostname):
    return ssh_machine_list[hostname]


def get_connection_to_host(ip):
    # Connect to the remote machine
    connection = Connection(
        user=ACCESS_MODULES["ssh"]["engima_root_user"],
        host=ip,
        connect_kwargs={
            "key_filename": ACCESS_MODULES["ssh"]["private_key_path"]
        },
    )
    logger.info(f"Connection to then remove machine with ip: {ip} has been formed")

    # check whether authentication is successful or not
    try:
        connection.open()
        return connection
    except Exception as e:
        logger.exception(f"Authentication failed: {e}")
        traceback.print_exc()
        return False


def get_username(access_level, user):
    username = user.user.username
    if access_level not in ["sudo", "nonsudo"]:
        username = access_level
        if access_level == "app":
            username = ACCESS_MODULES["ssh"]["app_user"]

    return username


def sshHelper(labels, user_identity, user, action):
    for label in labels:
        access_level = label["access_level"]
        hostname = label["machine"]
        ip = label["ip"]
        username = get_username(access_level, user)
        ssh_key = user_identity.identity["ssh_public_key"]

        if not is_valid_username(username):
            logger.error("SSHModule: rejected malformed username %r", username)
            return False, "Invalid username"

        if not is_valid_ssh_public_key(ssh_key):
            logger.error("SSHModule: rejected malformed ssh public key")
            return False, "Invalid SSH public key"

        if action == "grant":
            if access_level in ["sudo", "nonsudo"]:
                return add_user(hostname, ip, ssh_key, username, access_level)
            else:
                return add_key_existing_user(ip, ssh_key, access_level, username)
        elif action == "revoke":
            return revoke_user_access(hostname, ip, ssh_key, username)


def add_key_existing_user(ip, ssh_key, access_level, username):

    connection = get_connection_to_host(ip)
    if not connection:
        return False, "Authentication failed to machine."

    try:
        authorized_keys = "/home/{}/.ssh/authorized_keys".format(username)
        connection.sudo(
            "echo {} | sudo tee -a {} > /dev/null".format(
                shlex.quote(ssh_key), shlex.quote(authorized_keys)
            )
        )
    except Exception as e:
        logger.exception(
            "Exception while adding ssh key to {}: {}".format(username, str(e))
        )
        return False, "Failed to add ssh to user"

    connection.close()
    return True, ""


def add_user(hostname, ip, ssh_key, username, access_level):
    connection = get_connection_to_host(ip)

    if not connection:
        return False, "Authentication failed to machine."

    # Check if the user already exists, if so, return and do nothing
    quoted_username = shlex.quote(username)
    if not connection.sudo("id {}".format(quoted_username), warn=True).failed:
        logger.info("User already exists")
        return False, "User already exists"

    try:
        ssh_dir = "/home/{}/.ssh".format(username)
        authorized_keys = "{}/authorized_keys".format(ssh_dir)

        # Create the user
        connection.sudo("useradd -m {}".format(quoted_username))
        # Set the password to nothing
        connection.sudo("passwd -d {}".format(quoted_username))

        # Check if the user should be a root user or a basic user
        if access_level == "sudo":
            connection.sudo(
                "usermod -aG {} {}".format(
                    shlex.quote(ACCESS_MODULES["ssh"]["common_sudo_group"]),
                    quoted_username,
                )
            )

        # Create the .ssh directory
        connection.sudo("mkdir {}".format(shlex.quote(ssh_dir)))
        # Create the authorized_keys file
        connection.sudo("touch {}".format(shlex.quote(authorized_keys)))

        # Add the user's SSH key to the authorized_keys file on the remote machine
        connection.sudo(
            "echo {} | sudo tee -a {} > /dev/null".format(
                shlex.quote(ssh_key), shlex.quote(authorized_keys)
            )
        )

        # Change the permissions of the authorized_keys file to 600
        # (only the user can read and write)
        connection.sudo("chmod 600 {}".format(shlex.quote(authorized_keys)))

        # change the ownership of the /home/<username> directory to the user and
        # group of the user (username:username)
        connection.sudo(
            "chown -R {}:{} {}".format(
                quoted_username, quoted_username, shlex.quote("/home/{}".format(username))
            )
        )
    except Exception as e:
        logger.error("Exception occured while adding user: " + str(e))
        traceback.print_exc()
        return False, "Failed to add user"

    # Close the connection
    connection.close()
    return True, ""


def revoke_user_access(hostname, ip, ssh_key, username):
    return replace_user_key(hostname, ip, "", ssh_key, username)


def replace_user_key(hostname, ip, new_ssh_key, old_ssh_key, username):
    connection = get_connection_to_host(ip)
    if not connection:
        return False, "Authentication failed to machine."

    if not is_valid_username(username):
        logger.error("SSHModule: rejected malformed username %r", username)
        return False, "Invalid username"

    # Escape sed's regex metacharacters so the keys are matched/substituted
    # literally (the security guard against shell injection is shlex.quote on
    # the whole sed expression below; this only preserves sed correctness).
    old_ssh_key = re.sub(r"([/\\&.*[\]^$])", r"\\\1", old_ssh_key)
    new_ssh_key = re.sub(r"([/\\&])", r"\\\1", new_ssh_key)

    try:
        # Replace the old SSH key with the new SSH key in
        # the authorized_keys file on the remote machine
        sed_expr = "s/{}/{}/g".format(old_ssh_key, new_ssh_key)
        authorized_keys = "/home/{}/.ssh/authorized_keys".format(username)
        connection.sudo(
            "sed -i {} {}".format(
                shlex.quote(sed_expr), shlex.quote(authorized_keys)
            )
        )
    except Exception as e:
        logger.exception("Exception while replacing the ssh Key: " + str(e))
        return False, "Failed to replace ssh key"

    # Close the connection
    connection.close()
    return True, ""
