# Secrets Management

Sensitive configuration is maintained **separately** from ordinary host configuration and encrypted using **GPG**.

## Files involved

| File | Role | In version control? |
| --- | --- | --- |
| `secrets.json.gpg.example` | Template documenting the expected secrets structure | Yes |
| `secrets.json.gpg` | Actual encrypted secrets | **No** |
| `secrets.json` | Plaintext secrets (transient) | **Never** |

The repository provides `secrets.json.gpg.example` as a template. Copy it, fill in real values, and encrypt it. The actual `secrets.json.gpg` file is not included in version control.

## How secrets are loaded

At deployment time, `common.initialize()`:

1. Checks for the presence of `secrets.json.gpg` using the pyinfra `File` fact.
2. If present, runs `gpg --decrypt secrets.json.gpg`, parses the output as JSON, and publishes it as `builtins.secrets`.
3. If absent, sets `builtins.secrets = {}` and prints `Loading Secrets: None, skipping...`.

Deployment continues with an empty secrets dictionary when the encrypted file is absent. Features requiring secrets are consequently skipped or use their configured defaults.

Errors handled explicitly:

- `subprocess.CalledProcessError`: GPG decryption fails.
- `json.JSONDecodeError`: Decrypted content is not valid JSON.

## Secret categories

The following categories are defined in `secrets.json.gpg.example` and consumed by deployment tasks:

| Secrets key | Enables / used by |
| --- | --- |
| `wireguard` | `tasks/wireguard.py` — private keys for configured interfaces |
| `dehydrated` | `tasks/dehydrated.py` — Hetzner DNS API token for certificate management |
| `git_credentials` | `tasks/git.py` — Git credentials |
| `docker.miniflux` | `tasks/docker/miniflux.py` — Miniflux database and administrator credentials |
| `ssh` | `tasks/ssh_keys.py` — default and individual SSH key passphrases |

Some features require corresponding host configuration in addition to secrets. For example, WireGuard requires both `host.data.wireguard_config` and the corresponding entries under `secrets.wireguard`.

## Example structure

The following is a valid JSON example illustrating the supported secret categories:

json

```json
{
  "dehydrated": {
    "hetzner_api_token": "SECRETTOKEN"
  },
  "wireguard": {
    "home": {
      "privatekey": "SECRETKEY",
      "peers": [
        {
          "PublicKey": "SECRETKEY",
          "PresharedKey": "SECRETKEY",
          "AllowedIPs": "0.0.0.0/0,::/0",
          "Endpoint": "example.com:56965",
          "PersistentKeepalive": 25
        }
      ]
    }
  },
  "git_credentials": [
    "https://user:SECRETPASSWORD@gitea.org"
  ],
  "docker": {
    "miniflux": {
      "admin_username": "user@example.com",
      "admin_password": "SECRETPASSWORD",
      "postgres_password": "SECRETPASSWORD"
    }
  },
  "ssh": {
    "default_passphrase": "default-secret",
    "id_ed25519": {
      "passphrase": "my-secret-passphrase"
    },
    "id_github": {
      "passphrase": "another-secret"
    }
  }
}
```

Replace all example values with your own credentials and keys.

## Manual encryption / decryption

### Create the secrets file

Copy the example:

bash

```bash
cp secrets.json.gpg.example secrets.json
```

Edit `secrets.json` and replace the placeholder values.

Validate the JSON before encryption:

bash

```bash
python -m json.tool secrets.json
```

Encrypt manually:

bash

```bash
gpg --symmetric --cipher-algo AES256 secrets.json
```

This creates `secrets.json.gpg`.

After verifying that encryption succeeded, remove the plaintext file:

bash

```bash
shred -u secrets.json
```

### Manual decryption

For inspection or maintenance:

bash

```bash
gpg --decrypt secrets.json.gpg > secrets.json
```

**Remove the decrypted file after use.**

## Security recommendations

- Never commit `secrets.json` (plaintext) to version control.
- Never commit `secrets.json.gpg` unless explicitly intended.
- Keep both files ignored through `.gitignore`.
- `secrets.json.gpg.example` is safe to commit only when it contains placeholders rather than real credentials.
- Use a strong GPG passphrase.
- Restrict access to encrypted and decrypted secret files.
- Never reuse credentials across services.
- Rotate credentials if they are accidentally exposed.
- Remove decrypted files after use.

The repository's `.gitignore` already contains:

gitignore

```gitignore
secrets.json
secrets.json.gpg
```
