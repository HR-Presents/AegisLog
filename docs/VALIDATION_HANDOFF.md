# Remaining owner and independent validation work

## Repository protection

On 2026-10-05 the GitHub branch API reported `main` as unprotected. The connected repository app has no administration capability. Repository documentation and CI do not enable a ruleset.

An owner can open Settings → Rules → Rulesets, create a branch ruleset targeting `main`, activate it, require pull requests and passing status checks, block force pushes and deletion, and require branches to be current before merging where appropriate. Select the actual emitted CI matrix jobs, Security checks, package verification and Windows executable checks from recent runs. Include the Python 3.14 and isolated Windows wheel jobs. Avoid bypass permissions if review is meant to apply to administrators. Verify the rule through a test PR and a protection/ruleset read before calling protection enabled.

## Independently labeled real-world detection evaluation

This repository contains synthetic regression corpora. They are not independent real-world evidence. The tooling is ready to evaluate an authorized sanitized JSONL corpus; see [evaluation instructions](../evaluation/README.md). No production logs or fabricated labels are supplied by this handoff.

To complete independent evaluation, an authorized data owner and reviewer must supply source population and sampling information, independently adjudicated expected categories at the selected severity threshold, benign/negative controls, authorized sanitization, exclusions and source format coverage. Keep independent test labels separate from rule tuning. Record dataset hash and exact code commit. Review false-positive and false-negative cases, not only headline scores. The evaluator measures category presence per case; individual rule severity and correlation require additional reviewed labels/tests.

Required evidence metadata and the fail-closed optional manifest generator are documented in [evaluation instructions](../evaluation/README.md). A provenance string alone does not establish independence or data authorization.

## Physical Windows usability

Hosted Windows jobs cover package installation, command navigation and report identity; renderer tests cover terminal dimensions. They do not inspect a user's physical screen or prove every terminal/emulator, PATH setup and channel-permission combination.

Before claiming broader fresh-PC support, exercise the published wheel/ZIP on a clean user account using CMD, PowerShell and Windows Terminal, including a path with spaces/non-ASCII characters, ordinary-user System/Application access, expected Security-channel denial, optional administrator Security access, start/back/quit, report opening and a sustained append/rotate monitor session. Record version, terminal size, steps and failures with sanitized diagnostics. Existing sources must remain unchanged. This is manual acceptance work, not a claim that these environments were already independently tested.
