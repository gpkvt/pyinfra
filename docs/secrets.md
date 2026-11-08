# Secrets Management

Sensitive configuration is maintained **separately** from ordinary host
configuration and encrypted using **GPG**.

## Files involved

| File | Role | In version control? |
| --- | --- | --- |
| `secrets.json.gpg.example` | Template documenting the expected secrets structure | Yes |
| `secrets.json.gpg` | Actual encrypted secrets | **No** |
| `secrets.json` | Plaintext secrets (transient) | **Never** |

The repository provides `secrets.json.gpg.example` as a template — copy it,
fill in real values, and encrypt it. The actual `secrets.json.gpg` file is
not included in version control.

## How secrets are loaded

At deployment time, `common.initialize()`:

1. Checks for the presence of `secrets.json.gpg` (via the pyinfra `File` fact).
2. If present, runs `gpg --decrypt secrets.json.gpg`, parses the output as
   JSON, and publishes it as `builtins.secrets`
   (prints: `Loading Secrets: Decrypted successfully`).
3. If absent, sets `builtins.secrets = {}`
   (prints: `Loading Secrets: None, skipping…`).
   **Deployment continues with an empty secrets dictionary; features
   requiring secrets are consequently skipped.**

Errors handled explicitly: `subprocess.CalledProcessError` (GPG decryption
fails) and `json.JSONDecodeError` (invalid JSON).

## Feature gates depending on secrets

| Secrets key | Enables |
| --- | --- |
| `wireguard` | `tasks/wireguard.py` (together with `host.data.wireguard_config`) |
| `dehydrated` | `tasks/dehydrated.py` (ACME/Let's Encrypt certificates) |
| `git_credentials` | `tasks/git.py` (Git credentials) |
| `docker.miniflux` | `tasks/docker/miniflux.py` (Docker deployment of Miniflux RSS reader) |

The full secret categories are documented in `secrets.json.gpg.example`.

## Manual encryption / decryption

From the docstring of `common.py` (verbatim):

```bash
# encrypt manually:
gpg --symmetric --cipher-algo AES256 secrets.json && rm secrets.json

# decrypt manually:
gpg --decrypt secrets.json.gpg > secrets.json
```

**Remove the decrypted file after use.**

## Security recommendations

- Never commit `secrets.json` (plaintext) to version control.
- Keep `secrets.json` and `secrets.json.gpg` ignored via `.gitignore` —
  the repository's `.gitignore` maintains the relevant entries.
- `secrets.json.gpg.example` is safe to commit: it contains structure, not
  values.
