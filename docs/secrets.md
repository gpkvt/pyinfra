# Secrets management

The project stores sensitive values in a JSON document encrypted with GPG. Ordinary host configuration belongs in `group_data/`; credentials and private keys belong in the encrypted secrets document.

## Files

| File | Purpose | Commit? |
| --- | --- | --- |
| `secrets.json.gpg.example` | Plaintext JSON example/schema with placeholder values | Yes, after checking it contains no real secrets |
| `secrets.json` | Temporary plaintext working file | No |
| `secrets.json.gpg` | Encrypted secrets consumed by deployment | Normally no; keep outside version control |

Both real secret files are listed in `.gitignore`.

The repository includes `files/scripts/gpg-vault`, an interactive helper deployed by `tasks/scripts.py`. It manages the plaintext/encrypted file pair locally; it does not change the JSON schema or the way pyinfra loads secrets. The repository also includes a [Visual Studio Code extension](../vscode/gpg-vault/README.md) for performing the same GPG operations from the editor.

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

## Manage secrets with `gpg-vault`

`gpg-vault` is installed as a user utility by `tasks/scripts.py`. Once `files/scripts/` has been synchronized and the `/usr/local/bin/` link created, run it from the repository root (or pass an explicit path with `--file`). It requires GPG and uses the executable named by `$EDITOR`, defaulting to `nano`.

```bash
gpg-vault create   # Create a new encrypted file in the editor
gpg-vault edit     # Decrypt, edit and re-encrypt
gpg-vault view     # Print decrypted contents to standard output
gpg-vault encrypt  # Encrypt secrets.json and remove plaintext on success
gpg-vault decrypt  # Decrypt to secrets.json
gpg-vault rekey    # Change the GPG passphrase
gpg-vault status  # Show file presence
```

The default pair is `secrets.json` and `secrets.json.gpg`. Select another plaintext filename by placing `--file FILE` before the command:

```bash
gpg-vault --file /path/to/credentials.json create
gpg-vault --file /path/to/credentials.json edit
gpg-vault --file /path/to/credentials.json status
```

`create` and `edit` stage plaintext in a private temporary directory and replace the encrypted file only after encryption succeeds. `encrypt` removes the source plaintext after successful encryption. `decrypt` refuses to overwrite an existing plaintext file and sets its mode to `0600`. `view` writes decrypted data to the terminal; do not capture its output in logs. `status` reports file presence only, not passphrase or JSON validity.

The `view` and `decrypt` commands intentionally expose plaintext. Keep the terminal, filesystem and any resulting plaintext file secure. Temporary-directory cleanup is best-effort and does not replace sound host security or backups.

## Use the VS Code extension

The `vscode/gpg-vault/` directory contains a standalone VS Code extension. It provides Command Palette commands to encrypt or decrypt the active local file, toggle a file between encrypted and decrypted states, and encrypt or decrypt selected text. The toggle command is also bound to `Ctrl+Alt+E` on Windows/Linux and `Cmd+Alt+E` on macOS. A `.gpg` file can also be decrypted from the VS Code Explorer context menu.

The extension invokes the local GPG executable and delegates passphrase entry to GPG Agent/pinentry; it does not store passphrases in VS Code. It uses symmetric AES-256 and produces ASCII-armored ciphertext. GPG and the command-line `gpg-vault` helper can decrypt this output, and the extension can also decrypt the binary ciphertext produced by the shell helper.

File encryption saves the active document first, writes or replaces the sibling `.gpg` file without an overwrite prompt, and then removes the plaintext source. It attempts to overwrite the regular plaintext file with random data and flush it before unlinking, but this is best-effort sanitization rather than a guarantee of physical erasure. File decryption writes the original filename and replaces an existing plaintext destination without prompting. Decrypted files are created with owner-only permissions where supported. The `gpg-vault.openDecryptedFile` setting (default `true`) controls whether the decrypted file is opened in the editor; `gpg-vault.gpgPath` selects the GPG executable.

Selection commands replace the selected text in the editor with its encrypted or decrypted form. The extension stages operation data in a private temporary directory and removes that directory after the operation. See the [extension README](../vscode/gpg-vault/README.md) for installation and command details.

## Manual GPG fallback

The helper wraps symmetric AES-256 GPG encryption. If it is unavailable, the basic operations are:

```bash
gpg --symmetric --cipher-algo AES256 --output secrets.json.gpg secrets.json
gpg --decrypt secrets.json.gpg | python -m json.tool >/dev/null
```

For manual workflows, verify encrypted output before deleting plaintext. `shred` cannot guarantee secure erasure on every filesystem, SSD, snapshotting storage or backup system. Prefer encrypted storage and minimize plaintext lifetime. Ensure `secrets.json.gpg` has restrictive permissions (`chmod 600 secrets.json.gpg`). Keep a secure backup of the previous encrypted file until the new one has been verified and deployed.

## Security checklist

- Never commit `secrets.json` or `secrets.json.gpg`.
- Keep the example file free of real credentials.
- Use a strong, unique GPG passphrase and protect access to it.
- Restrict filesystem permissions on both encrypted and plaintext files.
- Do not print secret values in task logs or error messages.
- Rotate credentials immediately if they are exposed.
- Review backups, editor swap files, temporary directories and shell history for accidental plaintext copies.
- Do not assume that encryption makes a credential-bearing URL safe to share once decrypted.
