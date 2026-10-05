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

Compare the two SHA-256 values exactly, using the checksum beside the same release asset. The published version is **v2.1.17**. See [release notes](RELEASE_V2.1.17.md).

## Install as a terminal command

AegisLog runs inside your existing terminal; Q returns to your shell. Requires Python 3.10+ and pipx. Native collectors depend on the OS, installed tools and channel permissions.

### Windows: prepare pipx once

Check `python --version`. If `python` is unavailable but `py --version` works, substitute `py` in the commands below.

```cmd
python -m pip install --user pipx
python -m pipx ensurepath
```

Close and reopen the terminal to reload PATH. Administrator access is not required for normal installation.

### Latest reviewed report design on main

The approved company-facing summary and polished full report are included in the published v2.1.17 wheel and Windows EXE/ZIP. Generate a new report after updating to apply the native scope and summary pagination fixes; saved HTML/PDF files remain unchanged. Use A4, 100% scale and turn off browser Headers and footers when saving PDF.

### Upgrade and verify

Exit AegisLog first, then install the published wheel:

```cmd
python -m pipx install --force "https://github.com/HR-Presents/AegisLog-AI/releases/download/v2.1.17/aegislog_ai-2.1.17-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

The version should be **2.1.17**. Regenerate existing reports after updating. Your source logs are not modified; retain saved reports until you choose to delete them. Do not add `--pip-args="--force-reinstall"`: it can duplicate the uv backend's reinstall option.

If `aegislog` is not recognized after installation, reopen the terminal. In Command Prompt, an immediate launch is `"%USERPROFILE%\.local\bin\aegislog.exe" start`; in PowerShell use `& "$env:USERPROFILE\.local\bin\aegislog.exe" start`.

For the standalone distribution, download the new EXE/ZIP, verify its matching checksum and run the new copy. An older extracted EXE does not update automatically. The executable is unsigned; a matching checksum does not imply a valid publisher signature.

Python 3.10–3.14 are covered by Linux CI. Python 3.14 also has Windows installation, terminal start/quit, report and portable-benchmark smoke coverage. On Linux/macOS use `python3` where appropriate and the same published wheel with pipx.

## Start, use, and exit

```powershell
aegislog start
```

Choose **04 Native logs** to investigate your computer's supported telemetry without supplying a log file, or **05 Native monitor** to watch it. File analysis is also available when you have a log to investigate.

Press **Q** to exit AegisLog and return to your normal terminal prompt. The installed command stays available; run `aegislog start` whenever you need it again.

Check the installation with `aegislog --version` and `aegislog doctor`.

Remove it with:

```powershell
python -m pipx uninstall aegislog-ai
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
