# Architecture

The supported v2 product is local, deterministic and read-only.

1. Files, rolling streams, or native collectors provide telemetry. Native collectors use fixed argument lists and explicit read-only commands.
2. Bounded ingestion discards oversized line tails before decoding. Parsers normalize retained telemetry into events.
3. A shared bounded detection state applies local rules and authentication correlation; anomaly scoring describes event-class rarity in the retained sample.
4. Incident correlation and entity extraction provide evidence for local investigation, explanation, ATT&CK context, and analyst triage.
5. Responsive terminal views and escaped local HTML reports present retained evidence. SQLite stores investigations, cases, and entity history when requested.

## Resource boundaries

`ingestion.iter_bounded_lines` caps file-line prefixes and discards tails in 64 KiB chunks. The dashboard processes every prefix while retaining a recent line/byte-capped visualization sample. Live ingestion has independent per-read, per-line, and rolling-window limits. Truncation and retention affect coverage and are disclosed in reports.

## Trust boundaries

Logs, filenames, rule packs, and collector output are untrusted inputs. Terminal sanitization and common-secret redaction protect normal evidence presentation; HTML values are escaped. Redaction is best effort and does not guarantee all sensitive information is removed.

Declarative rule packs contain regular expressions rather than executable plugin code. Install only reviewed rules: custom expressions use a restricted syntax and bounded pack counts.

The public v2 entrypoint removes legacy AI/provider commands. Historical provider adapters are not supported product workflows. Their transport retains explicit remote opt-in, HTTPS validation, pinned resolved addresses, and response-size limits for compatibility tests.

## Interpretation

Findings, confidence, rarity scores, and ATT&CK mappings guide review; they do not prove compromise or attribution. The application does not modify accounts, firewall rules, services, or plant/host controls.


Custom rule safeguards: packs are limited to 1 MB, 32 files, 100 rules per pack and 200 rules total. Patterns retain literals, anchors, character classes, dot tokens and alternatives; groups, repetition, lookarounds and backreferences are rejected before execution to avoid backtracking stalls. Escaped metacharacters remain literal. Invalid packs are reported and skipped atomically. Existing packs using unsupported constructs must be rewritten; `--no-plugins` disables custom rules. These restrictions do not affect built-in detectors.
