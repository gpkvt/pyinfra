# GPG Vault for Visual Studio Code

A small VS Code extension for editing GPG-encrypted secrets without leaving the editor. It uses the local `gpg` executable and symmetric AES-256 encryption, matching the encryption format used by [`files/scripts/gpg-vault`](../../files/scripts/gpg-vault).

## Requirements

- Visual Studio Code 1.85 or newer.
- GnuPG (`gpg`) installed and available on `PATH`, or configured with `gpg-vault.gpgPath`.
- A working GPG agent and pinentry program. The extension never asks for, stores, or passes your passphrase itself; GPG handles passphrase entry.

## Commands

Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and choose:

| Command | What it does |
| --- | --- |
| **GPG Vault: Encrypt Current File** | Encrypts the active saved or unsaved text document into a sibling `.gpg` file. The source is kept by default. |
| **GPG Vault: Decrypt Current .gpg File** | Decrypts the active `.gpg` file into the filename without the `.gpg` suffix. Existing destination files are never overwritten. |
| **GPG Vault: Encrypt Selection** | Replaces the selected text with an ASCII-armored GPG message. |
| **GPG Vault: Decrypt Selection** | Replaces the selected armored GPG message with plaintext. |

The file workflow mirrors the `secrets.json` / `secrets.json.gpg` pair used by `gpg-vault`. Encryption creates an ASCII-armored GPG file; this is fully readable by GPG and by the repository's `gpg-vault` and deployment-time decryption. The command-line helper currently creates binary GPG output, which this extension can also decrypt.

File encryption never overwrites an existing `.gpg` file. File decryption never overwrites an existing plaintext file. Decrypted files are created with owner-only permissions where the operating system supports POSIX file modes. Temporary working files are placed in a private temporary directory and removed after each operation.

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| `gpg-vault.gpgPath` | `gpg` | GPG executable path. |
| `gpg-vault.deletePlaintextAfterEncrypt` | `false` | Ask for confirmation before deleting the plaintext source after a successful file encryption. |
| `gpg-vault.openDecryptedFile` | `true` | Open the decrypted file in the editor after decryption. |

## Install from source

From this directory:

```bash
npm install
npm run compile
```

To install the extension locally, package it with the VS Code Extension Manager:

```bash
npx @vscode/vsce package
code --install-extension pyinfra-gpg-vault-0.1.0.vsix
```

For development, open this directory as a VS Code workspace and press F5 to launch an Extension Development Host (after installing dependencies).

## Security notes

- GPG controls passphrase entry through your configured pinentry/GPG-agent setup. Do not configure loopback passphrase entry or put passphrases in VS Code settings.
- The extension does not silently delete plaintext. If you enable `deletePlaintextAfterEncrypt`, it asks for confirmation each time.
- Encryption does not make it safe to commit or share secret files. Keep encrypted files and backups protected, and review your Git ignore rules.
- Avoid using selection commands on very large documents. They temporarily stage the selected content in a private temporary directory.
- The extension operates on local `file:` documents for file-level commands. Selection commands work in any editable text document.

## Compatibility

GPG symmetric encryption uses AES-256, the same cipher selected by the repository's `gpg-vault` script. GPG's standard encrypted data format is used; no custom container or metadata is added.
