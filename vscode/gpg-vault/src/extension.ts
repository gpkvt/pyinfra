import * as vscode from "vscode";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { randomBytes } from "node:crypto";

const execFileAsync = promisify(execFile);

type GpgOperation = "encrypt" | "decrypt";

async function withPrivateTempDirectory<T>(
  callback: (directory: string) => Promise<T>
): Promise<T> {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "vscode-gpg-vault-"));
  try {
    await fs.chmod(directory, 0o700).catch(() => undefined);
    return await callback(directory);
  } finally {
    await fs.rm(directory, { recursive: true, force: true });
  }
}

function gpgExecutable(): string {
  return vscode.workspace.getConfiguration("gpg-vault").get<string>("gpgPath", "gpg");
}

async function runGpg(
  operation: GpgOperation,
  input: string,
  output: string
): Promise<void> {
  const args =
    operation === "encrypt"
      ? ["--quiet", "--symmetric", "--armor", "--cipher-algo", "AES256", "--output", output, input]
      : ["--quiet", "--decrypt", "--output", output, input];

  try {
    await execFileAsync(gpgExecutable(), args, {
      windowsHide: true,
      timeout: 120_000,
      maxBuffer: 1024 * 1024
    });
  } catch (error) {
    const details = error as NodeJS.ErrnoException & { stderr?: string };
    const stderr = details.stderr?.trim();
    if (details.code === "ENOENT") {
      throw new Error(`GPG executable not found: ${gpgExecutable()}`);
    }
    throw new Error(stderr || details.message || "GPG operation failed.");
  }
}

async function transformBytes(
  operation: GpgOperation,
  input: Buffer
): Promise<Buffer> {
  return withPrivateTempDirectory(async (directory) => {
    const inputPath = path.join(directory, "input");
    const outputPath = path.join(directory, "output");
    await fs.writeFile(inputPath, input, { mode: 0o600 });
    await runGpg(operation, inputPath, outputPath);
    return fs.readFile(outputPath);
  });
}

async function securelyDeletePlaintext(
  filePath: string,
  expected: Buffer,
  expectedInfo: Awaited<ReturnType<typeof fs.stat>>
): Promise<void> {
  // Deletion is mandatory after successful encryption. Overwriting the file
  // first is best-effort because SSDs, CoW filesystems and open handles can
  // prevent reliable physical erasure. Never let a failed wipe leave plaintext
  // on disk: unlink the path in all cases.
  try {
    const pathInfo = await fs.lstat(filePath);
    if (
      pathInfo.isFile() &&
      !pathInfo.isSymbolicLink() &&
      pathInfo.nlink === 1 &&
      pathInfo.dev === expectedInfo.dev &&
      pathInfo.ino === expectedInfo.ino
    ) {
      const handle = await fs.open(filePath, "r+");
      try {
        const openedInfo = await handle.stat();
        if (
          openedInfo.dev === expectedInfo.dev &&
          openedInfo.ino === expectedInfo.ino &&
          openedInfo.size === expected.length
        ) {
          const currentContents = await handle.readFile();
          if (currentContents.equals(expected)) {
            const bufferSize = 64 * 1024;
            let position = 0;
            while (position < openedInfo.size) {
              const length = Math.min(bufferSize, openedInfo.size - position);
              const randomData = randomBytes(length);
              let written = 0;
              while (written < length) {
                const result = await handle.write(randomData, written, length - written, position + written);
                if (result.bytesWritten === 0) throw new Error("Could not overwrite plaintext.");
                written += result.bytesWritten;
              }
              position += length;
            }
            await handle.sync();
          }
        }
      } finally {
        await handle.close();
      }
    }
  } catch {
    // Continue to unlink even if secure overwriting is unavailable.
  } finally {
    await fs.unlink(filePath).catch(async (error: NodeJS.ErrnoException) => {
      if (error.code !== "ENOENT") throw error;
    });
  }
}
async function showFailure(action: () => Promise<void>): Promise<void> {
  try {
    await action();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    void vscode.window.showErrorMessage(`GPG Vault: ${message}`);
  }
}

async function encryptFile(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    throw new Error("No active editor.");
  }
  const document = editor.document;
  if (document.uri.scheme !== "file") {
    throw new Error("File encryption is available only for local files.");
  }
  if (document.languageId === "binary") {
    throw new Error("The active document is not a text document.");
  }

  const sourcePath = document.uri.fsPath;
  if (sourcePath.toLowerCase().endsWith(".gpg")) {
    throw new Error("The active file already has a .gpg suffix. Use Decrypt Current .gpg File.");
  }
  const encryptedPath = `${sourcePath}.gpg`;

  // Save first so the bytes encrypted are exactly the bytes that will later be
  // securely deleted from disk. This also avoids deleting an older on-disk
  // version while encrypting newer, unsaved editor contents.
  if (document.isDirty) {
    const saved = await document.save();
    if (!saved) {
      throw new Error("Could not save the plaintext file; encryption was cancelled.");
    }
  }

  const plaintextInfo = await fs.stat(sourcePath);
  const plaintext = await fs.readFile(sourcePath);
  const afterReadInfo = await fs.stat(sourcePath);
  if (
    plaintextInfo.dev !== afterReadInfo.dev ||
    plaintextInfo.ino !== afterReadInfo.ino ||
    plaintextInfo.size !== afterReadInfo.size ||
    plaintextInfo.mtimeMs !== afterReadInfo.mtimeMs
  ) {
    throw new Error("Plaintext file changed while being read; encryption was cancelled.");
  }
  const ciphertext = await transformBytes("encrypt", plaintext);

  // Stage the ciphertext beside the destination so the final operation stays
  // on the same filesystem. Rename atomically replaces an existing encrypted
  // file without prompting, or creates it when it does not yet exist.
  const temporaryPath = path.join(
    path.dirname(encryptedPath),
    `.${path.basename(encryptedPath)}.${Date.now()}.${Math.random().toString(16).slice(2)}.tmp`
  );
  try {
    await fs.writeFile(temporaryPath, ciphertext, { flag: "wx", mode: 0o600 });
    // Explicitly remove the previous ciphertext so replacement never invokes
    // an editor/workspace overwrite flow or depends on platform rename rules.
    await fs.rm(encryptedPath, { force: true });
    await fs.rename(temporaryPath, encryptedPath);
    await fs.chmod(encryptedPath, 0o600).catch(() => undefined);
  } finally {
    await fs.unlink(temporaryPath).catch(() => undefined);
  }

  // Always remove the plaintext after the ciphertext has been written.
  // Abort cleanup if the source changed or was replaced while GPG was running.
  await securelyDeletePlaintext(sourcePath, plaintext, plaintextInfo);

  const encryptedDocument = await vscode.workspace.openTextDocument(vscode.Uri.file(encryptedPath));
  await vscode.window.showTextDocument(encryptedDocument, { preview: false });
  void vscode.window.showInformationMessage(
    `Encrypted file saved: ${path.basename(encryptedPath)}`
  );
}

async function decryptFile(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    throw new Error("No active editor.");
  }
  const document = editor.document;
  if (document.uri.scheme !== "file") {
    throw new Error("File decryption is available only for local files.");
  }

  const encryptedPath = document.uri.fsPath;
  if (!encryptedPath.toLowerCase().endsWith(".gpg")) {
    throw new Error("The active file must end in .gpg.");
  }
  const plaintextPath = encryptedPath.slice(0, -4);

  const ciphertext = await fs.readFile(encryptedPath);
  const plaintext = await transformBytes("decrypt", ciphertext);

  // Stage beside the destination and rename into place. On POSIX this
  // atomically replaces an existing plaintext file without a confirmation.
  const temporaryPath = path.join(
    path.dirname(plaintextPath),
    `.${path.basename(plaintextPath)}.${Date.now()}.${Math.random().toString(16).slice(2)}.tmp`
  );
  try {
    await fs.writeFile(temporaryPath, plaintext, { flag: "wx", mode: 0o600 });
    await fs.rename(temporaryPath, plaintextPath);
    await fs.chmod(plaintextPath, 0o600).catch(() => undefined);
  } finally {
    await fs.unlink(temporaryPath).catch(() => undefined);
  }

  const openDecrypted = vscode.workspace
    .getConfiguration("gpg-vault")
    .get<boolean>("openDecryptedFile", true);
  if (openDecrypted) {
    const decryptedDocument = await vscode.workspace.openTextDocument(vscode.Uri.file(plaintextPath));
    await vscode.window.showTextDocument(decryptedDocument, { preview: false });
  }
  void vscode.window.showInformationMessage(`Decrypted file created: ${path.basename(plaintextPath)}`);
}

async function toggleFileEncryption(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.uri.scheme !== "file") {
    throw new Error("Open a local file before toggling encryption.");
  }

  if (editor.document.uri.fsPath.toLowerCase().endsWith(".gpg")) {
    await decryptFile();
  } else {
    await encryptFile();
  }
}

async function transformSelection(operation: GpgOperation): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    throw new Error("No active editor.");
  }
  const selection = editor.selection;
  if (selection.isEmpty) {
    throw new Error("Select the text to encrypt or decrypt first.");
  }

  const selectedText = editor.document.getText(selection);
  const input = Buffer.from(selectedText, "utf8");
  const output = await transformBytes(operation, input);
  let replacement: string;
  try {
    replacement = new TextDecoder("utf-8", { fatal: true }).decode(output);
  } catch {
    throw new Error("The decrypted data is not valid UTF-8 text and cannot replace an editor selection.");
  }

  await editor.edit((editBuilder) => editBuilder.replace(selection, replacement));
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("gpg-vault.encryptFile", () =>
      showFailure(encryptFile)
    ),
    vscode.commands.registerCommand("gpg-vault.decryptFile", () =>
      showFailure(decryptFile)
    ),
    vscode.commands.registerCommand("gpg-vault.toggleFileEncryption", () =>
      showFailure(toggleFileEncryption)
    ),
    vscode.commands.registerCommand("gpg-vault.encryptSelection", () =>
      showFailure(() => transformSelection("encrypt"))
    ),
    vscode.commands.registerCommand("gpg-vault.decryptSelection", () =>
      showFailure(() => transformSelection("decrypt"))
    )
  );
}

export function deactivate(): void {
  // No long-lived resources to release.
}
