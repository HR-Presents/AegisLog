# Remaining owner and independent validation work

## Repository protection

Verified on 2026-10-05: the active Protect main ruleset targets `main`, blocks deletion and force pushes, requires a pull request with one approval and approval of the latest push, and requires resolved review threads. The bypass list is empty.

Seven required checks are configured with strict up-to-date enforcement: the Python 3.10–3.14 test matrix, `windows-python314-smoke`, and `report-print-regression`. Future changes need an eligible independent reviewer; documentation does not substitute for the active ruleset. The connected repository app can read the ruleset but cannot change administration settings.

## Independently labeled real-world detection evaluation

This repository contains synthetic regression corpora. They are not independent real-world evidence. The tooling is ready to evaluate an authorized sanitized JSONL corpus; see [evaluation instructions](../evaluation/README.md). No production logs or fabricated labels are supplied by this handoff.

To complete independent evaluation, an authorized data owner and reviewer must supply source population and sampling information, independently adjudicated expected categories at the selected severity threshold, benign/negative controls, authorized sanitization, exclusions and source format coverage. Keep independent test labels separate from rule tuning. Record dataset hash and exact code commit. Review false-positive and false-negative cases, not only headline scores. The evaluator measures category presence per case; individual rule severity and correlation require additional reviewed labels/tests.

Required evidence metadata and the fail-closed optional manifest generator are documented in [evaluation instructions](../evaluation/README.md). A provenance string alone does not establish independence or data authorization.

## Physical Windows usability

Hosted Windows jobs cover package installation, command navigation and report identity; renderer tests cover terminal dimensions. They do not inspect a user's physical screen or prove every terminal/emulator, PATH setup and channel-permission combination.

Before claiming broader fresh-PC support, exercise the published wheel/ZIP on a clean user account using CMD, PowerShell and Windows Terminal, including a path with spaces/non-ASCII characters, ordinary-user System/Application access, expected Security-channel denial, optional administrator Security access, start/back/quit, report opening and a sustained append/rotate monitor session. Record version, terminal size, steps and failures with sanitized diagnostics. Existing sources must remain unchanged. This is manual acceptance work, not a claim that these environments were already independently tested.
