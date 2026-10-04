# AegisLog user guide

AegisLog investigates selected logs and accessible native telemetry locally. It preserves source logs and supports human review through deterministic findings, incident groups, and reports. It does not automatically remediate the host.

## Install and launch

Follow [Installation](INSTALL.md) for the standalone release or terminal-command installation. Main may contain reviewed changes newer than published binaries. Run:

```text
aegislog start
```

For the standalone build, use `AegisLog.exe start` from its folder.

## Mission Control

| Choice | Workflow |
|---|---|
| 01 | Analyze an accessible file; type demo for the synthetic dataset |
| 02 / 03 | Live file / multi-source monitoring |
| 04 / 05 | Native snapshot / native monitoring |
| 06 | Incident review |
| 07 / P | Demo / replay |
| 08 / 09 | Health / help |
| C | Guided computer check |
| F | Folder scan |
| S | Security Workbench |
| R | Saved reports |
| A | Workflow guide |
| G | Optional beginner walkthrough |
| B / Q | Back / Quit |

The D browser dashboard is removed. The direct CLI `dashboard` command remains a terminal investigation/report workflow. A opens the guide; it does not launch AI Analyst. Remote model workflows are not part of the supported public product.

## Investigate a file

Choose 01 and paste or drag an accessible file path. Quote paths containing spaces in direct commands:

```text
aegislog dashboard "C:\logs\auth.log"
```

Review processed/recognized records, retention limits, findings, and incident groups before opening the summary and complete report. Supported structured layouts and generic fallback are described in [Compatibility](COMPATIBILITY.md). Unsupported fields and zero findings do not establish safety.

## Check computer logs

Choose C to discover readable native channels and known file sources. Select a source, then a native time window and maximum event count where prompted. Time and count limits can exclude earlier events. Known files are analyzed as files rather than through the native time window.

Windows System/Application usually work without elevation. Security can require an administrator terminal. Docker requires its CLI, engine, and container access; Docker is not needed for ordinary file or Windows Event Log analysis. Linux native collection requires journalctl and appropriate access.

## Scan a folder

Choose F, enter a folder, and select candidates. Discovery is bounded and skips binary files and symlinks. Optional identical-content deduplication preserves relative paths. Sources are analyzed independently; the batch overview is not historical cross-file correlation. Incomplete, failed, or cancelled outcomes are distinct from completed reports.

## Monitor and investigate

Choose 02, 03, or 05 for supported live views. Rolling retained evidence is bounded and is not a complete historical archive. B/Escape stops a live view; Q quits. Use S Workbench for supported evidence filters, details, timelines, and exports.

Direct incident commands include:

```text
aegislog incidents "C:\logs\auth.log"
aegislog explain "C:\logs\auth.log" INC-XXXXXXXX
aegislog mitre "C:\logs\auth.log"
```

Use `aegislog COMMAND --help` for exact arguments. See [Commands](COMMANDS.md).

## Open, print, compare, and share

R browses saved reports. Completed guided investigations offer O Report and F Folder; V Compare baseline and S Share summary are available in the current computer-check result workflow.

A sharing summary omits raw evidence and common identifiers, but aggregate counts can still reveal information about a system. Review it before sharing. Baseline differences require context and are not proof of a new attack.

Read [Reports](REPORTS.md) for summary/full evidence navigation, PDF printing, activity interpretation, and coverage. Generate a new report after updating; existing files remain unchanged.

## Health and exit

Run `aegislog doctor` for runtime and collector availability. READY means the capability is available, not that the host is secure. Q returns control to the shell; the installed command remains available.

If a command is not recognized, reopen the terminal after pipx ensurepath. See [Troubleshooting](TROUBLESHOOTING.md) and [Installation](INSTALL.md).

**MADE BY HR-PRESENTS**
