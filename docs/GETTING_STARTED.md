# Get useful results in five minutes

AegisLog investigates logs locally. It highlights rule matches and unusual activity, explains practical next steps, and creates reports. It does not establish that a computer is clean or compromised and does not change system settings.

## Install and launch

Windows users need Python 3.10+ for the pipx route:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

Reopen PowerShell, then install this review branch:

```powershell
cd $HOME
py -m pipx install "https://github.com/HR-Presents/AegisLog-AI/archive/refs/heads/codex/report-print-quality.zip"
aegislog start
```

Already installed? Use the same install command with `--force` to replace it with the current branch build. This is a review build, not a signed stable release. For reproducible deployment, use a reviewed full commit SHA in the archive URL rather than a moving branch. Linux/macOS users can prepare pipx using its official platform instructions and use the same install/launch commands.

The Windows standalone ZIP is an alternative that does not require Python. Run its executable from a user-owned working directory so reports can be written. Verify its SHA-256 against the included checksum. See INSTALL.md and RELEASE_SECURITY.md for distribution and signing details.

## Check this computer

1. Choose **C Check Computer**.
2. Read the source descriptions and probe results. System/Application/Security are offered on Windows; journald on Linux. Access is tested with a bounded read-only probe, not inferred from the operating system. Known Windows servicing and Linux auth/syslog/Nginx/Apache log paths are also offered when present; those files are analyzed in full rather than using a native time window.
3. Select a readable source and the last hour, 24 hours or 7 days.
4. Review the event count, collection scope, retained evidence and findings. The terminal collects at most 300 events for this guided workflow; a busy source may have earlier events excluded by that cap.
5. Use **R Reports** to open the summary. Follow full evidence links when needed. Press **B** to return or **Q** to quit.

For protected Windows Security logs, use the minimum required permissions; AegisLog does not elevate itself or alter auditing configuration. Empty collection does not prove a clean system.

## Files and folders

- **01 Analyze Log:** one text log.
- **F Scan Folder:** discover nonempty text candidates in a folder and its subfolders, select numbers or ALL, and analyze each source separately.
- **02/03/05:** live file, multiple-source or native monitoring.

Folder scanning stops at 200 candidates or 10,000 entries. It skips symlinks, empty files and obvious binary content. Extensions do not guarantee parser support. Choose a smaller folder if discovery reaches its limit.

## Interpret the output

Operational issues include application errors and service failures. Security leads include account, authentication and suspicious access signals. A rule match is not a measured probability of compromise. Check whether the activity was authorized, compare adjacent events, and preserve evidence before acting.

The guided result includes retained-format counts, generic fallback counts, truncation and retention notes. These describe the analyzed/retained evidence, not universal log-format coverage.

## Troubleshoot and give feedback

Run `aegislog doctor` for runtime diagnostics. If a file is binary or UTF-16, export a UTF-8 text version. If a native source is unavailable, review its displayed reason and try file analysis.

Report bugs at https://github.com/HR-Presents/AegisLog-AI/issues with version/build, OS, installation method, chosen workflow and a sanitized reproduction. Never attach production logs or credentials without authorization. No feedback or log upload happens automatically.

Uninstall with `py -m pipx uninstall aegislog-ai`. Locally generated reports are separate files and are not deleted by package removal.

## Launching from a protected directory

AegisLog first tries `./aegislog-reports/`. If that location cannot be written (for example Windows System32), it falls back to `%LOCALAPPDATA%\AegisLog\reports` on Windows or `~/.aegislog/reports` elsewhere. R Reports searches both locations. You do not need administrator privileges merely to save reports. If both fail, a readable error is shown. An explicit output directory is honored and never silently redirected.

### Folder and report controls

F scans likely log candidates by default. Include other text/configuration files explicitly if needed, then choose file numbers or ALL. Identical content can share a report while retaining both locations in the batch overview. B/Escape/Ctrl+C cancels; completed reports remain. O opens the overview/report directly; F opens its folder. R lists every saved summary and overview with N/P pages. Review physical lines, records, recognized records and coverage before interpreting zero findings.
