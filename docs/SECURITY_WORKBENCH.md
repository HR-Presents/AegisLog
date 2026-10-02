# Security workbench

Development feature; no new stable version is implied. Open the terminal shell with `AegisLog.exe start`, then enter **S** for the Security Workbench or **P** for a built-in demo replay. S asks for one existing log file. The workbench uses the established cyan, mint, neutral-border and semantic-severity palette.

## Controls

| Control | Action |
|---|---|
| F | Select severity, finding category, service, source format/filename, and time range |
| X | Clear all filters |
| O | Generate the filtered HTML report and open it locally in a browser |
| E | Create a redacted JSON evidence export; existing files are never overwritten |
| T | Show account, privilege, login, process and audit observations with source line references |
| W | Load an exact IP/domain watchlist; blank clears it |
| C | Load threshold/exception tuning JSON; blank restores defaults |
| I | Record a new SHA-256 baseline or compare against an existing baseline |
| P | Replay the first 150 recorded lines at 0.2 seconds per line in a labelled demo monitor |
| R | Reread the file and recalculate analysis |
| B / Q | Return to the main menu / quit |

Press Enter after typing an action. Live/replay views accept single-key B/Escape to stop and Q to quit; Ctrl+C also stops. Reports open only when O or `--open-report` is selected. Browser launch failures show the report path for manual opening.

## CLI examples

```powershell
.\AegisLog.exe security .\security-demo.log --severity HIGH --export .\evidence.json
.\AegisLog.exe security .\security-demo.log --service sshd --since 2026-10-02T12:01:00Z --until 2026-10-02T12:01:30Z
.\AegisLog.exe security .\security-demo.log --watchlist .\watchlist-demo.txt --tuning .\tuning-demo.json --open-report
.\AegisLog.exe security .\security-demo.log --interactive
.\AegisLog.exe replay
.\AegisLog.exe replay .\security-demo.log --interval 0.2 --limit 150
.\AegisLog.exe integrity-record .\security-demo.log .\baseline.json
.\AegisLog.exe integrity-check .\security-demo.log .\baseline.json
```

The fixtures in [examples](examples/) are synthetic. Their IP addresses are documentation ranges and the watchlist is not real threat intelligence. The built-in replay includes healthy requests, repeated failed logins followed by success, account creation, group changes, privilege assignment, process auditing, firewall activity, an operational error and audit-log clearing. Recorded timestamps stay historical; replay activity/rates describe arrival into the demo monitor. Replay never appends to the input file or impersonates a live collector.

## Detection and evidence semantics

The workbench adds a HIGH review signal when a timestamped successful login follows at least five failures for the same account, normalized source IP, and reported host/workstation within 300 seconds. It supports SSH accepted-password/public-key messages and Windows 4625/4624 records. Missing account, IP, or timestamp prevents this sequence rule from firing. Success clears the corresponding failure sequence. Workbench processing sorts timestamped records, so out-of-order input can still be reviewed. Live monitors use the same default rule inside their retained window; multi-source sequence analysis stays within each source. A sequence is evidence for review, not proof of account compromise.

Supported account and privilege observations appear in chronological order with source line numbers. A Windows account field may identify an actor or a target; the UI and report do not claim these are interchangeable. An encoded PowerShell command or certutil URL-cache command in a Windows process-creation event produces a contextual process-review signal. Legitimate administration can trigger it.

Watchlists contain one exact canonical IP or ASCII domain per line, with `#` comments. Matching normalizes IP representations and URL hostnames; it does not treat a substring or a different subdomain as an exact match. Indicator ownership, age and accuracy are supplied by the analyst. No automatic external feed or reputation claim is made.

Time filters require ISO timestamps with an explicit timezone and compare in UTC. Unknown timestamps are excluded only when a time range is selected. `--timestamp-year` supplies explicit context for syslog timestamps without a year. Source filtering accepts the parsed format (`windows`, `iso-service`, `web`, `json/journald`, `generic`), source filename, or full path. Severity/category filters select findings and their retained referenced events; related evidence outside a time/service filter may be referenced by a finding, but is not included as selected event content. Filters affect presentation/export, not source data.

## Tuning

JSON accepts `login_failure_threshold` (2–100), `login_window_seconds` (30–3600), and at most 50 exceptions. Each exception has an exact category, a nonempty literal `contains` substring, and a documented `reason` (each at most 256 characters). Matching is case-insensitive. There is no executable rule code or custom regex in this configuration. The threshold governs the new failure-to-success rule; the window also configures the workbench's existing failure correlation. Live monitoring currently uses default thresholds and does not load this file.

Suppression removes a finding from active counts but preserves its evidence and reason in the workbench, JSON exports, and HTML report. Filters can still inspect suppressed findings. Refresh keeps active session filters, watchlists, and tuning. Settings are session-scoped and do not silently modify global configuration.

## Collection and integrity

File, multi-source and native live views show successful collection times, errors, failure counts, and retained-window evictions/truncation. File polling retries permission/read errors. Multi-source polling continues with healthy sources when another fails. Native polling preserves its read-only collector and deduplication behavior. Returned native snapshot-event counts can include previously seen events; a successful empty poll means the collector returned no events, not that coverage or host safety is proven.

Integrity baselines use streaming SHA-256 and bind to the resolved source path. Recording refuses existing targets and source overwrites. Checking returns exit code 0 for UNCHANGED, 1 for CHANGED, and a CLI error for an invalid/mismatched baseline. Normal log growth also changes a hash. Baselines are local, unsigned files; someone able to change both the log and baseline can defeat this comparison. Concurrent changes during hashing are rejected where file metadata reveals them.

JSON exports include selected redacted events, source line numbers, signal references, documented suppressions, filters, tuning and retention counts. Their source fingerprint is taken **at export**, not at analysis; it is explicitly labelled and is not a claim of signed provenance. Redaction is best effort. Preserve and protect original logs separately.

## Bounds and limitations

Workbench input prefixes are capped at 16 KiB per line; retained evidence is capped at 10,000 recent lines and 8 MB. Analysis covers the retained sample, not every original line. Signals are capped at 10,000, and bounded engine state may omit more; omitted counts are disclosed. A signal retains at most 100 matching line references; login-success sequences retain the last 100 failure references plus the success. Watchlists are capped at 200 KB/2,000 entries and tuning at 100 KB. Unknown formats, unavailable fields, sampling, and native collector permissions affect coverage.

Reports and exports are local output artifacts. No accounts, firewall settings, services, source logs or host security policy are modified. Actual Windows keyboard, browser-opening, Unicode, colour and resize acceptance still requires the packaged build.
