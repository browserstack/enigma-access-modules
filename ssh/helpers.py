import json
import traceback
import logging

from fabric import Connection

logger = logging.getLogger(__name__)
from EnigmaAutomation.settings import ACCESS_MODULES


with open(ACCESS_MODULES["ssh"]["inventory_file_path"], "r") as f:
    global ssh_machine_list
    ssh_machine_list = {}
    # convert inventory.csv file to dictionary with hostname as key and ip as value
    for line in f.readlines():
        ssh_machine_list[line.split(",")[0]] = line.split(",")[1].strip()

def get_ip_from_hostname(hostname):
    return ssh_machine_list[hostname]


def get_connection_to_host(ip):

    # Connect to the remote machine
    connection = Connection(user=ACCESS_MODULES["ssh"]["engima_root_user"], host=ip, connect_kwargs={"key_filename": ACCESS_MODULES["ssh"]["private_key_path"]})
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
        connection.sudo(
            'echo "{}" | sudo tee -a /home/{}/.ssh/authorized_keys > /dev/null'.format(
                ssh_key, username
            )
        )
    except Exception as e:
        logger.exception("Exception while adding ssh key to {}: {}".format(username, str(e)))
        return False, "Failed to add ssh to user"

    connection.close()
    return True, ""

def add_user(hostname, ip, ssh_key, username, access_level):
    connection = get_connection_to_host(ip)

    if not connection:
        return False, "Authentication failed to machine."

    # Check if the user already exists, if so, return and do nothing
    if not connection.sudo("id {}".format(username), warn=True).failed:
        logger.info("User already exists")
        return False, "User already exists"

    try:
        # Create the user
        connection.sudo("useradd -m {}".format(username))
        # Set the password to nothing
        connection.sudo("passwd -d {}".format(username))

        # Check if the user should be a root user or a basic user
        if access_level == "sudo":
            connection.sudo("usermod -aG {} {}".format(ACCESS_MODULES["ssh"]["common_sudo_group"], username))

        # Create the .ssh directory
        connection.sudo("mkdir /home/{}/.ssh".format(username))
        # Create the authorized_keys file
        connection.sudo("touch /home/{}/.ssh/authorized_keys".format(username))

        # Add the user's SSH key to the authorized_keys file on the remote machine
        connection.sudo(
            'echo "{}" | sudo tee -a /home/{}/.ssh/authorized_keys > /dev/null'.format(
                ssh_key, username
            )
        )

        # Change the permissions of the authorized_keys file to 600
        # (only the user can read and write)
        connection.sudo("chmod 600 /home/{}/.ssh/authorized_keys".format(username))

        # change the ownership of the /home/<username> directory to the user and
        # group of the user (username:username)
        connection.sudo("chown -R {}:{} /home/{}".format(username, username, username))
    except Exception as e:
        logger.error("Exception occured while adding user: "+str(e))
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

    # Replace the / with \/ in the old SSH key and the new SSH key so that it can
    # be used in the sed command below (sed command uses / as a delimiter)
    old_ssh_key = old_ssh_key.replace("/", "\/")
    new_ssh_key = new_ssh_key.replace("/", "\/")

    try:
        # Replace the old SSH key with the new SSH key in the authorized_keys file on the remote machine
        connection.sudo(
            'sed -i "s/{}/{}/g" /home/{}/.ssh/authorized_keys'.format(
                old_ssh_key, new_ssh_key, username
            )
        )
    except Exception as e:
        logger.exception("Exception while replacing the ssh Key: "+str(e))
        return False, "Failed to replace ssh key"

    # Close the connection
    connection.close()
    return True, ""

