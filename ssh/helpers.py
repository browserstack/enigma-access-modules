import json
import traceback
import logging

from fabric import Connection

logger = logging.getLogger(__name__)

# get user from the config.json file
with open("ssh/config.json", "r") as f:
    global enigma_ssh_root_user
    enigma_ssh_root_user = json.load(f)["enigma_root_user"]


with open("ssh/inventory.csv", "r") as f:
    global ssh_machine_list
    ssh_machine_list = {}
    # convert inventory.csv file to dictionary with hostname as key and ip as value
    for line in f.readlines():
        ssh_machine_list[line.split(",")[0]] = line.split(",")[1].strip()


def get_ip_from_hostname(hostname):
    return ssh_machine_list[hostname]


def get_conn_to_host(hostname):
    ip = get_ip_from_hostname(hostname)

    # Connect to the remote machine
    c = Connection(user=enigma_ssh_root_user, host=ip)
    print(c)

    # check whether authentication is successful or not
    try:
        c.open()
        return c
    except Exception as e:
        print(f"Authentication failed: {e}")
        traceback.print_exc()
        return


def sshHelper(labels, user, action):
    for label in labels:
        access_level = label["access_level"]
        hostname = label["hostname"]
        username = user.username
        ssh_key = user.ssh_public_key.key

        if action == "grant":
            return add_user(hostname, ssh_key, username, access_level)
        elif action == "revoke":
            return replace_user_key(hostname, "", ssh_key, username)


def add_user(hostname, ssh_key, username, should_be_root):
    c = get_conn_to_host(hostname)

    # Check if the user already exists, if so, return and do nothing
    if not c.sudo("id {}".format(username), warn=True).failed:
        print("User already exists")
        return False, "User already exists"

    try:
        # Create the user
        c.sudo("useradd -m {}".format(username))
        # Set the password to nothing
        c.sudo("passwd -d {}".format(username))

        # Check if the user should be a root user or a basic user
        if should_be_root:
            c.sudo("usermod -aG sudo {}".format(username))

        # Create the .ssh directory
        c.sudo("mkdir /home/{}/.ssh".format(username))
        # Create the authorized_keys file
        c.sudo("touch /home/{}/.ssh/authorized_keys".format(username))

        # Add the user's SSH key to the authorized_keys file on the remote machine
        c.sudo(
            'echo "{}" | sudo tee -a /home/{}/.ssh/authorized_keys > /dev/null'.format(
                ssh_key, username
            )
        )

        # Change the permissions of the authorized_keys file to 600
        # (only the user can read and write)
        c.sudo("chmod 600 /home/{}/.ssh/authorized_keys".format(username))

        # change the ownership of the /home/<username> directory to the user and
        # group of the user (username:username)
        c.sudo("chown -R {}:{} /home/{}".format(username, username, username))
    except Exception as e:
        logger.error(str(e))
        traceback.print_exc()
        return False, str(e)

    # Close the connection
    c.close()
    return True, ""


def revoke_user_access(hostname, ssh_key, username):
    replace_user_key(hostname, "", ssh_key, username)


def replace_user_key(hostname, new_ssh_key, old_ssh_key, username):
    c = get_conn_to_host(hostname)

    # Replace the / with \/ in the old SSH key and the new SSH key so that it can
    # be used in the sed command below (sed command uses / as a delimiter)
    old_ssh_key = old_ssh_key.replace("/", "\/")
    new_ssh_key = new_ssh_key.replace("/", "\/")

    # Replace the old SSH key with the new SSH key in the authorized_keys file on the remote machine
    c.sudo(
        'sed -i "s/{}/{}/g" /home/{}/.ssh/authorized_keys'.format(
            old_ssh_key, new_ssh_key, username
        )
    )

    # Close the connection
    c.close()


def add_key_existing_user(hostname, ssh_key, username):
    c = get_conn_to_host(hostname)

    # Add the user's SSH key to the authorized_keys file on the remote machine
    c.sudo(
        'echo "{}" | sudo tee -a /home/{}/.ssh/authorized_keys > /dev/null'.format(
            ssh_key, username
        )
    )
    c.sudo("cat /home/{}/.ssh/authorized_keys".format(username))

    # Close the connection
    c.close()

"""
# Path: ssh/main.py
ssh_key = (
    "ssh-rsa"
    " AAAAB3NzaC1yc2EAAAADAQABAAABAQDNFh6NsQLEgteLgEFKEaH3DI3mW8h0x0pM3LoGDYXmnYyhavw5r3jS3Mhx6tsnyxsbBxVpbP51uY0CawR0BnOqrGGUOQnd/gdZmXXx5ef8xGwYX4xapFXGJH5mM0KN8EJoH/rwf7K9ufqHqtNWmUKLJhZdJgr0NH8xDOntwtAVD/Qz9TmQegrv7MSJjvLyzzA8kQF65QcgBCw+g2wWZKrfW1e1N0Ts9URDvRQBZ0GZzJjoNnNtBv2UE6lse/pXMxEi8zgNnGsrladk3WTl/oG1Bw/FPRDcqyRRPaJ01msPt89ea1BMqWfvuTuSkdkfLPZtguxAKRjhZ3whwC6FlXbN"
    " khushhal@Khushhals-MacBook-Pro.local"
)
# revoke_user_access("test_machine", ssh_key, "test1")
# add_user("test_machine", ssh_key, "test1", True)
# replace_user_key("test_machine", "123", ssh_key, "test1")
# add_key_existing_user("test_machine", ssh_key, "test1")
# remove_user("test_machine", "test1")

# add_key_existing_user("test_machine", ssh_key, "test1")
# revoke_user_access("test_machine", ssh_key, "test1")

add_user("test_machine", ssh_key, "test3", False)
add_user("test_machine", ssh_key, "test3", False)
"""
