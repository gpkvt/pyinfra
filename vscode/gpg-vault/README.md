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
| **GPG Vault: Encrypt Current File** | Encrypts the active saved or unsaved text document into a sibling `.gpg` file. After successful encryption, it securely overwrites and deletes the plaintext source by default; set `gpg-vault.deletePlaintextAfterEncrypt` to `false` to keep it. |
| **GPG Vault: Decrypt Current .gpg File** | Decrypts the active `.gpg` file into the filename without the `.gpg` suffix. Existing destination files are never overwritten. You can also right-click a `.gpg` file in the Explorer and choose this command, including for binary files created by the shell helper. |
| **GPG Vault: Encrypt Selection** | Replaces the selected text with an ASCII-armored GPG message. |
| **GPG Vault: Decrypt Selection** | Replaces the selected armored GPG message with plaintext. |

The file workflow mirrors the `secrets.json` / `secrets.json.gpg` pair used by `gpg-vault`. Encryption creates an ASCII-armored GPG file; this is fully readable by GPG and by the repository's `gpg-vault` and deployment-time decryption. The command-line helper currently creates binary GPG output, which this extension can also decrypt.

File encryption asks before replacing an existing `.gpg` file. File decryption never overwrites an existing plaintext file. Explorer context-menu decryption can read both ASCII-armored and binary GPG files, including ciphertext produced by the shell helper. Decrypted files are created with owner-only permissions where the operating system supports POSIX file modes. Temporary working files are placed in a private temporary directory and removed after each operation.

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| `gpg-vault.gpgPath` | `gpg` | GPG executable path. |
| `gpg-vault.deletePlaintextAfterEncrypt` | `true` | Best-effort overwrite and delete the plaintext source automatically after successful file encryption. Set to `false` to keep plaintext files. |
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
- The extension never silently deletes plaintext. With `deletePlaintextAfterEncrypt` enabled (the default), it first saves the document and encrypts the bytes on disk. After successful encryption, it overwrites the regular plaintext file with random data, flushes the file, and unlinks it. It refuses deletion if the file changed or was replaced during encryption. Files with multiple hard links are not overwritten or deleted. This is best-effort sanitization: SSD wear-leveling, copy-on-write filesystems, snapshots, backups, and storage-level journaling can retain previous blocks, so software overwrite cannot guarantee physical erasure. For stronger assurance, use full-disk encryption and manage snapshots/backups accordingly.
- Encryption does not make it safe to commit or share secret files. Keep encrypted files and backups protected, and review your Git ignore rules.
- Avoid using selection commands on very large documents. They temporarily stage the selected content in a private temporary directory.
- The extension operates on local `file:` documents for file-level commands. Selection commands work in any editable text document.

## Compatibility

GPG symmetric encryption uses AES-256, the same cipher selected by the repository's `gpg-vault` script. GPG's standard encrypted data format is used; no custom container or metadata is added.
