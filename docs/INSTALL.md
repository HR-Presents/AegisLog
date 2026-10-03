# Installation

## Windows standalone executable

The recommended Windows installation is the one-file console application:

1. Open the [published releases](https://github.com/HR-Presents/AegisLog-AI/releases).
2. Download `AegisLog.exe`.
3. Optionally download `AegisLog.exe.sha256` and verify the executable before running it.
4. Run `AegisLog.exe` to open Mission Control.

No Python installation or support directory is required. Unless the release notes explicitly say otherwise, do not assume the executable is digitally signed; Windows SmartScreen or antivirus reputation warnings can occur for unsigned PyInstaller applications.

PowerShell checksum verification:

```powershell
Get-FileHash .\AegisLog.exe -Algorithm SHA256
Get-Content .\AegisLog.exe.sha256
```

Compare the two SHA-256 values exactly. Always use the checksum published beside the same release asset you downloaded. The published stable version is v2.1.3. The audited terminal/report updates are a newer development build; see [prepared release notes](RELEASE_V2.1.4.md) for its verified artifact and limitations.

## Install as a terminal command

AegisLog runs inside your existing PowerShell, Command Prompt, or Linux/macOS terminal. It does not replace your shell.

Requires Python 3.10+ and pipx. No Git checkout or supplied demo log is required for this installation route.

### Windows: prepare pipx once

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

Close and reopen the terminal after `ensurepath` so Windows loads the updated PATH.

### Install or update the audited build

```powershell
cd $HOME
py -m pipx install --force "https://github.com/HR-Presents/AegisLog-AI/archive/3fa654012458ca91e38ca40dd31e25d016dec70a.zip"
```

This immutable URL installs the audited development build, currently reporting version 2.1.3; it does not install a published v2.1.4 release. `--force` also updates an existing installation. Do not add `--pip-args="--force-reinstall"`: with the uv backend that duplicates the reinstall option and fails. Python 3.10–3.13 are covered by CI; Python 3.14 is not yet part of that test matrix.

### Start, use, and exit

```powershell
aegislog start
```

Choose **04 Native logs** to investigate your computer's supported telemetry without supplying a log file, or **05 Native monitor** to watch it. File analysis is also available when you have a log to investigate.

Press **Q** to exit AegisLog and return to your normal terminal prompt. The installed command stays available; run `aegislog start` whenever you need it again.

Check the installation with `aegislog --version` and `aegislog doctor`.

Remove it with:

```powershell
py -m pipx uninstall aegislog-ai
```

On Linux/macOS, install pipx using its documented platform instructions, then use the same `pipx install` and `aegislog` commands.

## Development installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

On Windows PowerShell activate with `.venv\Scripts\Activate.ps1`.

The repository also includes `install.sh` and `install.ps1` helpers for source checkouts. Core processing is local, read-only and deterministic; no AI provider is required.

## Windows Security channel

For Security events only, open Start, search PowerShell, choose **Run as administrator**, approve the Windows prompt, then run `cd $HOME` and `aegislog start`. Choose C Check Computer and the readable Security source. Q returns to PowerShell. System/Application checks usually work without elevation.
