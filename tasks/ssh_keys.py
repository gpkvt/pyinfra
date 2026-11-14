# pylint: disable=E0401
"""
Manage SSH keypairs and authorized_keys.

Configuration:
    ssh_keys:
        List of SSH keypairs to create.
    ssh_authorized_keys:
        Mapping of system users to public keys.
    ssh_authorized_keys_enabled:
        Whether to manage authorized_keys. Defaults to True.

Supported algorithms:
    - ed25519
    - rsa

Private keys are never overwritten automatically.
"""

import builtins
import re
import shlex

from pyinfra import host
from pyinfra.operations import files, server
from pyinfra.facts.files import File

if not hasattr(builtins, "homedir"):
    from common import initialize
    initialize(host)

homedir: str = getattr(builtins, "homedir")
ssh_dir = f"{homedir}/.ssh/"

username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

ssh_keys = host.data.get("ssh_keys", [])
authorized_keys = (
    host.data.get("ssh_authorized_keys", {})
    if host.data.get("ssh_authorized_keys_enabled", True)
    else {}
)

secrets: dict = getattr(builtins, "secrets")
ssh_secrets = secrets.get("ssh", {})
default_passphrase = ssh_secrets.get("default_passphrase", "")

if ssh_keys or authorized_keys:
    files.directory(
        name="Ensure SSH directory exists",
        path=ssh_dir,
        user=username,
        group=usergroup,
        mode="700",
        _sudo=False,
    )

for key in ssh_keys:
    name = key["name"]
    key_type = key.get("type", "ed25519")
    comment = key.get("comment", f"{username}@{host.name}")

    if not re.fullmatch(r"[a-zA-Z0-9._-]+", name):
        raise ValueError(f"Invalid SSH key name: {name}")
    if key_type not in ("ed25519", "rsa"):
        raise ValueError(f"Unsupported SSH key type: {key_type}")

    passphrase = ssh_secrets.get(name, {}).get("passphrase", default_passphrase)
    key_path = f"{ssh_dir}{name}"
    pub_path = f"{key_path}.pub"

    command = [
        "ssh-keygen", "-q", "-t", key_type, "-C", comment, "-f", key_path,
    ]
    if passphrase:
        command.extend(["-N", passphrase])

    if key_type == "rsa":
        bits = int(key.get("bits", 4096))
        if bits < 3072:
            raise ValueError("RSA keys must have at least 3072 bits")
        command.extend(["-b", str(bits)])

    generate_command = " ".join(shlex.quote(str(arg)) for arg in command)
    private_key_exists = host.get_fact(File, path=key_path)
    public_key_exists = host.get_fact(File, path=pub_path)

    server.shell(
        name=f"Generate SSH keypair: {name}",
        commands=[
            f"""
            if [ ! -e {shlex.quote(key_path)} ] &&
               [ ! -e {shlex.quote(pub_path)} ]; then
                umask 077
                {generate_command}
            elif [ ! -f {shlex.quote(key_path)} ] ||
                 [ ! -f {shlex.quote(pub_path)} ]; then
                echo "Incomplete SSH keypair: {name}" >&2
                exit 1
            fi
            """
        ],
        # Run for a missing pair or an incomplete pair. The command creates
        # only when both files are absent and fails safely when only one exists.
        _if=[
            lambda private_key_exists=private_key_exists,
                   public_key_exists=public_key_exists:
                not (private_key_exists and public_key_exists)
        ],
        _sudo=False,
    )

    files.file(
        name=f"Set private key permissions: {name}",
        path=key_path,
        user=username,
        group=usergroup,
        mode="600",
        _sudo=False,
    )
    files.file(
        name=f"Set public key permissions: {name}",
        path=pub_path,
        user=username,
        group=usergroup,
        mode="644",
        _sudo=False,
    )

for user, public_keys in authorized_keys.items():
    if isinstance(public_keys, str):
        public_keys = [public_keys]
    server.user_authorized_keys(
        name=f"Manage authorized_keys for {user}",
        user=user,
        public_keys=public_keys,
        delete_keys=True,
        _sudo=False,
    )
