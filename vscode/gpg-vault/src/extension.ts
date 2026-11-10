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
  expected: Awaited<ReturnType<typeof fs.stat>>
): Promise<void> {
  const fileInfo = await fs.lstat(filePath);
  if (!fileInfo.isFile() || fileInfo.isSymbolicLink()) {
    throw new Error("Refusing secure deletion: plaintext path is not a regular file.");
  }
  if (fileInfo.nlink > 1) {
    throw new Error("Refusing secure deletion: plaintext file has multiple hard links.");
  }
  if (
    fileInfo.dev !== expected.dev ||
    fileInfo.ino !== expected.ino ||
    fileInfo.size !== expected.size ||
    fileInfo.mtimeMs !== expected.mtimeMs
  ) {
    throw new Error("Plaintext file changed after encryption; refusing to delete it.");
  }

  const handle = await fs.open(filePath, "r+");
  try {
    const openedInfo = await handle.stat();
    if (openedInfo.dev !== expected.dev || openedInfo.ino !== expected.ino) {
      throw new Error("Plaintext file was replaced; refusing secure deletion.");
    }

    const bufferSize = 64 * 1024;
    let position = 0;
    while (position < openedInfo.size) {
      const length = Math.min(bufferSize, openedInfo.size - position);
      const randomData = randomBytes(length);
      let written = 0;
      while (written < length) {
        const result = await handle.write(randomData, written, length - written, position + written);
        if (result.bytesWritten === 0) throw new Error("Could not overwrite the complete plaintext file.");
        written += result.bytesWritten;
      }
      position += length;
    }
    await handle.sync();
  } finally {
    await handle.close();
  }

  const currentInfo = await fs.lstat(filePath);
  if (currentInfo.dev !== expected.dev || currentInfo.ino !== expected.ino) {
    throw new Error("Plaintext file was replaced during secure deletion; refusing to unlink it.");
  }
  await fs.unlink(filePath);
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

  let overwrite = false;
  try {
    await fs.lstat(encryptedPath);
    const answer = await vscode.window.showWarningMessage(
      `The encrypted file already exists: ${encryptedPath}. Replace it?`,
      { modal: true },
      "Overwrite",
      "Cancel"
    );
    if (answer !== "Overwrite") {
      return;
    }
    overwrite = true;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw error;
    }
  }

  // Save first so the bytes encrypted are exactly the bytes that will later be
  // securely deleted from disk. This also avoids deleting an older on-disk
  // version while encrypting newer, unsaved editor contents.
  if (document.isDirty) {
    const saved = await document.save();
    if (!saved) {
      throw new Error("Could not save the plaintext file; encryption was cancelled.");
    }
  }

  const plaintext = await fs.readFile(sourcePath);
  const plaintextInfo = await fs.stat(sourcePath);
  const ciphertext = await transformBytes("encrypt", plaintext);

  // Stage the ciphertext beside the destination so the final operation stays
  // on the same filesystem. A hard link gives new files no-clobber semantics;
  // rename atomically replaces an existing file only after explicit consent.
  const temporaryPath = path.join(
    path.dirname(encryptedPath),
    `.${path.basename(encryptedPath)}.${Date.now()}.${Math.random().toString(16).slice(2)}.tmp`
  );
  try {
    await fs.writeFile(temporaryPath, ciphertext, { flag: "wx", mode: 0o600 });
    if (overwrite) {
      await fs.rename(temporaryPath, encryptedPath);
    } else {
      await fs.link(temporaryPath, encryptedPath);
      await fs.unlink(temporaryPath);
    }
    await fs.chmod(encryptedPath, 0o600).catch(() => undefined);
  } finally {
    await fs.unlink(temporaryPath).catch(() => undefined);
  }

  const deleteSource = vscode.workspace
    .getConfiguration("gpg-vault")
    .get<boolean>("deletePlaintextAfterEncrypt", true);

  if (deleteSource) {
    // Encryption has completed and the ciphertext is safely in place. Remove
    // the exact plaintext file that was encrypted; abort deletion if it changed
    // or was replaced while GPG was running.
    await securelyDeletePlaintext(sourcePath, plaintextInfo);
  }

  const encryptedDocument = await vscode.workspace.openTextDocument(vscode.Uri.file(encryptedPath));
  await vscode.window.showTextDocument(encryptedDocument, { preview: false });
  void vscode.window.showInformationMessage(
    overwrite
      ? `Encrypted file replaced: ${path.basename(encryptedPath)}`
      : `Encrypted file created: ${path.basename(encryptedPath)}`
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

  try {
    await fs.access(plaintextPath);
    throw new Error(`Refusing to overwrite existing file: ${plaintextPath}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw error;
    }
  }

  const ciphertext = await fs.readFile(encryptedPath);
  const plaintext = await transformBytes("decrypt", ciphertext);
  await fs.writeFile(plaintextPath, plaintext, { flag: "wx", mode: 0o600 });
  await fs.chmod(plaintextPath, 0o600).catch(() => undefined);

  const openDecrypted = vscode.workspace
    .getConfiguration("gpg-vault")
    .get<boolean>("openDecryptedFile", true);
  if (openDecrypted) {
    const decryptedDocument = await vscode.workspace.openTextDocument(vscode.Uri.file(plaintextPath));
    await vscode.window.showTextDocument(decryptedDocument, { preview: false });
  }
  void vscode.window.showInformationMessage(`Decrypted file created: ${path.basename(plaintextPath)}`);
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
