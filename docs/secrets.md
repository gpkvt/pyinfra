# Secrets management

The project stores sensitive values in a JSON document encrypted with GPG. Ordinary host configuration belongs in `group_data/`; credentials and private keys belong in the encrypted secrets document.

## Files

| File | Purpose | Commit? |
| --- | --- | --- |
| `secrets.json.gpg.example` | Plaintext JSON example/schema with placeholder values | Yes, after checking it contains no real secrets |
| `secrets.json` | Temporary plaintext working file | No |
| `secrets.json.gpg` | Encrypted secrets consumed by deployment | Normally no; keep outside version control |

Both real secret files are listed in `.gitignore`.

## How loading works

`common.initialize()` checks for `secrets.json.gpg` using pyinfra's `File` fact. If found, it executes `gpg --decrypt secrets.json.gpg`, parses standard output as JSON, and assigns the resulting dictionary to `builtins.secrets`. If the file is absent, `builtins.secrets` becomes `{}` and deployment continues.

Decryption failures and invalid JSON are not silently ignored: GPG errors and JSON parsing errors stop initialization. The GPG process may prompt for the passphrase depending on the local GPG agent configuration.

## Supported top-level keys

The example file documents the current data shape:

| Key | Consumer | Values |
| --- | --- | --- |
| `wireguard` | `tasks/wireguard.py` | Interface-indexed private keys and peer values, including optional preshared keys. |
| `dehydrated` | `tasks/dehydrated.py` | Hetzner DNS API token. |
| `git_credentials` | `tasks/git.py` | List of credential-bearing Git URLs. |
| `docker.miniflux` | `tasks/docker/miniflux.py` | Miniflux admin and PostgreSQL credentials. |
| `ssh` | `tasks/ssh_keys.py` | Default and per-key passphrases. |

A secret entry alone does not necessarily activate a task. For example, WireGuard also needs `wireguard_config` in host data. See [Deployment workflow](deployment.md).

## Example structure

Use `secrets.json.gpg.example` as the authoritative example. A simplified structure is shown below; replace every placeholder and remove categories you do not use.

```json
{
  "dehydrated": {
    "hetzner_api_token": "REPLACE_ME"
  },
  "wireguard": {
    "wg0": {
      "privatekey": "REPLACE_ME",
      "peers": [
        {
          "PublicKey": "REPLACE_ME",
          "PresharedKey": "REPLACE_ME",
          "AllowedIPs": "0.0.0.0/0,::/0",
          "Endpoint": "vpn.example.net:51820",
          "PersistentKeepalive": 25
        }
      ]
    }
  },
  "git_credentials": [
    "https://user:REPLACE_ME@git.example.net"
  ],
  "docker": {
    "miniflux": {
      "admin_username": "admin@example.net",
      "admin_password": "REPLACE_ME",
      "postgres_password": "REPLACE_ME"
    }
  },
  "ssh": {
    "default_passphrase": "REPLACE_ME",
    "id_ed25519": {
      "passphrase": "REPLACE_ME"
    }
  }
}
```

Do not use the placeholder values in a real deployment. Avoid storing secrets in shell history or temporary files on shared systems.

## Create and encrypt the file

```bash
cp secrets.json.gpg.example secrets.json
${EDITOR:-vi} secrets.json
python -m json.tool secrets.json

gpg --symmetric --cipher-algo AES256 --output secrets.json.gpg secrets.json
```

Verify that the encrypted file can be read before removing plaintext:

```bash
gpg --decrypt secrets.json.gpg | python -m json.tool >/dev/null
shred -u secrets.json
```

`shred` cannot guarantee secure erasure on every filesystem, SSD, snapshotting storage or backup system. Prefer encrypted storage and minimize the lifetime of plaintext secrets. Ensure the encrypted file has restrictive permissions:

```bash
chmod 600 secrets.json.gpg
```

## Inspect or update secrets

Decrypt to a temporary file only when necessary:

```bash
gpg --decrypt secrets.json.gpg > secrets.json
${EDITOR:-vi} secrets.json
python -m json.tool secrets.json

gpg --symmetric --cipher-algo AES256 --output secrets.json.gpg.new secrets.json
# Verify the new encrypted file before replacing the old one.
gpg --decrypt secrets.json.gpg.new | python -m json.tool >/dev/null
mv secrets.json.gpg.new secrets.json.gpg
shred -u secrets.json
```

Keep a secure backup of the previous encrypted file until the new one has been verified and deployed.

## Security checklist

- Never commit `secrets.json` or `secrets.json.gpg`.
- Keep the example file free of real credentials.
- Use a strong, unique GPG passphrase and protect access to it.
- Restrict filesystem permissions on both encrypted and plaintext files.
- Do not print secret values in task logs or error messages.
- Rotate credentials immediately if they are exposed.
- Review backups, editor swap files, temporary directories and shell history for accidental plaintext copies.
- Do not assume that encryption makes a credential-bearing URL safe to share once decrypted.
