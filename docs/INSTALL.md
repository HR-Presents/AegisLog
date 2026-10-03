# Installation

## Windows standalone executable

The recommended Windows installation is the one-file console application:

1. Open the [v1.6.0 GitHub release](https://github.com/HR-Presents/AegisLog-AI/releases/tag/v1.6.0).
2. Download `AegisLog.exe`.
3. Optionally download `AegisLog.exe.sha256` and verify the executable before running it.
4. Run `AegisLog.exe` to open Mission Control.

No Python installation or support directory is required. Unless the release notes explicitly say otherwise, do not assume the executable is digitally signed; Windows SmartScreen or antivirus reputation warnings can occur for unsigned PyInstaller applications.

PowerShell checksum verification:

```powershell
Get-FileHash .\AegisLog.exe -Algorithm SHA256
Get-Content .\AegisLog.exe.sha256
```

Compare the two SHA-256 values exactly. Always use the checksum published beside the same release asset you downloaded. See [v1.6.0 release notes](RELEASE_V1.6.0.md) for stable-release details.

## Install as a terminal command

AegisLog runs inside your existing PowerShell, Command Prompt, or Linux/macOS terminal. It does not replace your shell.

Requires Python 3.10+ and pipx. No Git checkout or supplied demo log is required for this installation route.

### Windows: prepare pipx once

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

Close and reopen the terminal after `ensurepath` so Windows loads the updated PATH.

### Install this report-update build

```powershell
pipx install "https://github.com/HR-Presents/AegisLog-AI/archive/refs/heads/codex/report-print-quality.zip"
```

This URL installs the current review branch. For a released version, use a published release tag or commit after release verification.

### Start, use, and exit

```powershell
aegislog start
```

Choose **04 Native logs** to investigate your computer's supported telemetry without supplying a log file, or **05 Native monitor** to watch it. File analysis is also available when you have a log to investigate.

Press **Q** to exit AegisLog and return to your normal terminal prompt. The installed command stays available; run `aegislog start` whenever you need it again.

Check the installation with `aegislog --version` and `aegislog doctor`.

Remove it with:

```powershell
pipx uninstall aegislog-ai
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
