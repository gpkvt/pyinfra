# GPG Vault for Visual Studio Code

A small VS Code extension for working with GPG-encrypted files and selected text without leaving the editor. It uses the local `gpg` executable and symmetric AES-256 encryption, matching the encryption format used by [`files/scripts/gpg-vault`](../../files/scripts/gpg-vault).

## Requirements

- Visual Studio Code 1.85 or newer.
- GnuPG (`gpg`) installed and available on `PATH`, or configured with `gpg-vault.gpgPath`.
- A working GPG agent and pinentry program. The extension never asks for, stores, or passes your passphrase itself; GPG handles passphrase entry.

## Commands

Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and choose:

| Command | What it does |
| --- | --- |
| **GPG Vault: Encrypt Current File** | Saves the active local text document, encrypts it into a sibling `.gpg` file, replaces any existing encrypted destination without prompting, and removes the plaintext source after successful encryption. |
| **GPG Vault: Decrypt Current .gpg File** | Decrypts the active local `.gpg` file into the filename without the suffix, replacing an existing plaintext destination without prompting. |
| **GPG Vault: Toggle File Encryption** | Decrypts the active file when its name ends in `.gpg`; otherwise encrypts it. |
| **GPG Vault: Encrypt Selection** | Replaces the selected text with an ASCII-armored GPG message. |
| **GPG Vault: Decrypt Selection** | Replaces the selected armored GPG message with plaintext. |

The toggle command has a default keyboard shortcut:

- Windows/Linux: `Ctrl+Alt+E`
- macOS: `Cmd+Alt+E`

You can also right-click a `.gpg` file in the Explorer and choose **GPG Vault: Decrypt Current .gpg File**.

## File behavior

File encryption saves the document first so the bytes encrypted match the on-disk source. It writes the encrypted output beside the source and replaces an existing `.gpg` destination without an overwrite confirmation. After the ciphertext has been written, the plaintext source is removed.

**Encrypted files are written as ASCII-armored text**, beginning with `-----BEGIN PGP MESSAGE-----`. This matches the shell-based `files/scripts/gpg-vault` helper. Decryption remains compatible with both ASCII-armored files and existing binary GPG ciphertext.

Before unlinking plaintext, the extension attempts to overwrite the regular file with random data and flush the changes. This is best-effort sanitization, not guaranteed physical erasure: SSD wear-leveling, copy-on-write filesystems, snapshots, backups, journaling and open handles can retain previous data. Use full-disk encryption and manage snapshots/backups appropriately.

File decryption replaces an existing plaintext destination without prompting and applies owner-only permissions where supported. The encrypted source is retained.

Selection commands transform the selected text in place. Decrypted selection data must be valid UTF-8 text.

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| `gpg-vault.gpgPath` | `gpg` | GPG executable path. |
| `gpg-vault.openDecryptedFile` | `true` | Open the decrypted file in the editor after successful file decryption. |

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
- File encryption deletes the plaintext source after writing ciphertext. The overwrite step is best-effort and cannot guarantee physical erasure on all storage devices or filesystems.
- Encryption does not make it safe to commit or share secret files. Keep encrypted files and backups protected, and review your Git ignore rules.
- Avoid using selection commands on very large documents. They temporarily stage the selected content in a private temporary directory.
- The extension operates on local `file:` documents for file-level commands. Selection commands work in any editable text document.

## Compatibility

GPG symmetric encryption uses AES-256, the same cipher selected by the repository's `gpg-vault` script. Both the extension and shell helper create ASCII-armored GPG messages. GPG's standard encrypted data format is used; no custom container or metadata is added.
