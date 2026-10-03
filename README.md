<div align="center">

# AEGISLOG

**Terminal-first defensive log investigation for analysts who want evidence, not noise.**

[![CI](https://github.com/HR-Presents/AegisLog-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/HR-Presents/AegisLog-AI/actions/workflows/ci.yml)
[![Security](https://github.com/HR-Presents/AegisLog-AI/actions/workflows/security.yml/badge.svg)](https://github.com/HR-Presents/AegisLog-AI/actions/workflows/security.yml)
[![Latest release](https://img.shields.io/github/v/release/HR-Presents/AegisLog-AI?display_name=tag&style=flat-square&color=4C8DFF)](https://github.com/HR-Presents/AegisLog-AI/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-4C8DFF.svg?style=flat-square)](LICENSE)

[**Download**](https://github.com/HR-Presents/AegisLog-AI/releases/latest) · [User Guide](docs/USER_GUIDE.md) · [Commands](docs/COMMANDS.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)

`LOCAL-FIRST` &nbsp; `READ-ONLY` &nbsp; `DETERMINISTIC` &nbsp; `DEFENSIVE`

</div>

---

## A security investigation console, not another noisy scanner

AegisLog turns raw logs into structured investigation context while keeping analysis local and retained evidence visible. Its core detection and correlation pipeline is deterministic: findings are signals for analyst review, never automatic claims of compromise or attribution.

### Core capabilities

| | Capability | What it gives the analyst |
|---|---|---|
| **01** | **ANALYZE** | Parse a log, surface findings, correlate incidents, and generate a self-contained report. |
| **02** | **LIVE MONITOR** | Watch a log source continuously with read-only detection. |
| **03** | **MULTI-SOURCE** | Correlate activity across multiple live telemetry sources. |
| **04** | **NATIVE TELEMETRY** | Inspect supported Windows, Linux, and Docker sources. |
| **05** | **INCIDENTS** | Review evidence chains, severity, confidence, and investigation context. |
| **06** | **REPORTING** | Produce analyst-oriented HTML evidence reports that stay local. |

AI Analyst is not part of the supported public product surface. No remote model workflow, auto-remediation, exploitation, persistence, credential theft, or silent host modification is part of the supported product surface.

---

## Current release

The current published stable release is **v2.1.3**.

- Release target commit: `c01247b34a2dd54c863dd142c618f03e184af8f8`
- Windows artifacts: `AegisLog.exe` and `AegisLog.exe.sha256`
- Windows EXE SHA-256: `1ddda99e03fd36ba1816b1567a28b8cc23d410583f34771c1287f9e3c1a28155`
- The Windows executable is currently unsigned.
- Maintained benchmark results are synthetic regression evidence only, not independently validated real-world effectiveness evidence.

### Windows visual-status note

The published v2.1.3 executable is functionally released, but its Mission Control presentation did **not** pass subsequent real-Windows visual acceptance. A later unreleased UI experiment on `main` also failed visual review. Those attempts are not being promoted as a finished visual design, and no newer release should be inferred from development-branch or CI artifacts.

The current development dashboard follows the [terminal reference design](docs/TERMINAL_REFERENCE_DESIGN.md), with cyan headings, mint bars, thin borders, and telemetry-based charts. Its labelled development previews do not replace Windows visual acceptance.

The development [Security Workbench](docs/SECURITY_WORKBENCH.md) adds filtered evidence, report access, demo replay, login-sequence review, account timelines, supplied watchlists, integrity fingerprints, detection tuning and collector health. Enter `S` or `P` from the interactive shell.

Public product screenshots should come from a verified build and should not be presented as accepted product imagery until a real Windows capture has been reviewed.

---

## Quick start

### Windows standalone

1. Open the [latest release](https://github.com/HR-Presents/AegisLog-AI/releases/latest).
2. Download `AegisLog.exe` and, optionally, `AegisLog.exe.sha256`.
3. Verify the checksum if required.
4. Start the console:

```powershell
.\AegisLog.exe start
```

The interactive shell uses the authoritative `aegis@console >` prompt. Windows SmartScreen or endpoint-security reputation warnings may appear because the executable is unsigned, even when the published checksum matches.

### Install a terminal command

With Python 3.10+ and pipx installed:

```bash
pipx install "https://github.com/HR-Presents/AegisLog-AI/archive/refs/heads/codex/report-print-quality.zip"
aegislog start
```

This installs the report-update review branch. Choose **04 Native logs** or **05 Native monitor** to use supported system telemetry without a supplied demo file. Press **Q** to return to your existing terminal. See [installation instructions](docs/INSTALL.md) for Windows pipx setup and uninstalling.

### Python 3.10+

```bash
git clone https://github.com/HR-Presents/AegisLog-AI.git
cd AegisLog-AI
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
aegislog doctor
aegislog start
```

---

## Investigation workflow

```text
TELEMETRY
   |
   v
PARSE + NORMALIZE
   |
   v
DETERMINISTIC DETECTIONS
   |
   v
CORRELATION + ANOMALY CONTEXT
   |
   v
INCIDENT QUEUE
   |
   v
EVIDENCE-LED REVIEW
   |
   v
LOCAL HTML REPORT
```

A high-severity finding or confidence score means **review this evidence carefully**. It does not mean the system is definitely compromised.

---

## Common commands

```text
AegisLog.exe dashboard C:\path\to\auth.log
AegisLog.exe incidents C:\path\to\auth.log
AegisLog.exe explain C:\path\to\auth.log <incident-id>
AegisLog.exe mitre C:\path\to\auth.log

AegisLog.exe live C:\logs\auth.log --profile security
AegisLog.exe live-multi C:\logs\auth.log C:\logs\web.log --profile authentication

AegisLog.exe native-sources
AegisLog.exe native-analyze windows --channel Security
AegisLog.exe native-live journald --profile operations

AegisLog.exe doctor
AegisLog.exe --help
```

See the complete [Command Reference](docs/COMMANDS.md).

---

## Security model

AegisLog treats log-derived content as untrusted input and keeps the analyst in control.

- **Read-only host interaction** — investigation does not become remediation.
- **Deterministic local analysis** — detection behavior remains inspectable and testable.
- **Evidence before verdicts** — uncertainty and retained evidence remain visible.
- **No installation telemetry** — the project does not add tracking simply to count users.
- **Safe public collaboration** — issues and reviews should use sanitized or synthetic data.

Read [Security](SECURITY.md), [Threat Model](docs/THREAT_MODEL.md), [Privacy](docs/PRIVACY.md), and [No Auto-Remediation](docs/NO_AUTOREMEDIATION.md).

---

## Documentation

| Start here | Engineering / reference |
|---|---|
| [Installation](docs/INSTALL.md) | [Architecture](docs/ARCHITECTURE.md) |
| [Quick Start](docs/QUICKSTART.md) | [Detection Pipeline](docs/DETECTION_PIPELINE.md) |
| [User Guide](docs/USER_GUIDE.md) | [Parsers](docs/PARSERS.md) |
| [Commands](docs/COMMANDS.md) | [Rules](docs/RULES.md) |
| [Demo](docs/DEMO.md) | [Collectors](docs/COLLECTORS.md) |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | [Testing](docs/TESTING.md) |
| [FAQ](docs/FAQ.md) | [Performance](docs/PERFORMANCE.md) |
| [Documentation Index](docs/README.md) | [Limitations](docs/LIMITATIONS.md) |

---

## Contributing

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
bandit -q -r src
```

Keep pull requests focused, add tests for behavioral changes, and never commit credentials, customer information, or sensitive production logs.

---

## License

AegisLog is released under the [MIT License](LICENSE).

<div align="center">

**AEGISLOG** · Investigate locally. Preserve evidence. Keep the analyst in control.

</div>

### Scan a folder of logs

In `aegislog start`, choose **F Scan Folder** and enter a folder path. A bounded recursive scan finds nonempty text candidates (`.log`, `.txt`, `.jsonl`, `.ndjson`, `.json`, `.csv`), skips symlinks and binary files, and lets you select numbers or ALL. Each selected source receives its own summary and evidence report under `aegislog-reports/folder-scan/`; **R Reports** opens them. Sources remain unchanged. Extension matching does not guarantee parser support. Discovery stops at 200 candidates or 10,000 entries; choose a smaller folder to cover the rest. B returns and Q quits.

### Guided checks and local graphical dashboard

Use **C Check Computer** for readable-source discovery and a bounded native-log investigation, or **D Local Dashboard** for a local browser interface. Equivalent commands:

```powershell
aegislog check-computer
aegislog desktop
```

The dashboard offers beginner/analyst views, keyboard-accessible controls, adjustable text size, finding explanations, severity counts, HTML reports and credential-redacted JSON. Quit or Ctrl+C returns to the shell. It uses the same local engine as the terminal and binds only to 127.0.0.1. Reports stay on disk. No automatic uploads or automatic remediation. See [Getting started](docs/GETTING_STARTED.md), [Compatibility](docs/COMPATIBILITY.md), and [Product readiness](docs/PRODUCT_READINESS.md).

Folder scans now default to likely logs, offer identical-content deduplication, preserve relative source locations, and produce a searchable batch overview plus JSON manifest. B/Escape/Ctrl+C cancels while retaining completed reports. **O** opens completed reports and **F** opens their folder. **R** paginates all saved summaries and batch overviews; the terminal keeps **C/D/F/R/A** shortcuts visible beneath the scrollable home. Physical lines, records and recognized records are reported separately. Supported structured inputs and detection limits are listed in [compatibility](docs/COMPATIBILITY.md).
