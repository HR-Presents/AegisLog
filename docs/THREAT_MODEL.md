# Threat model

## Assets and inputs

Source logs, credentials accidentally embedded in telemetry, local investigation reports, SQLite case history, and user configuration. Untrusted input includes log content, paths, collector output, and installed declarative rule packs.

## Implemented mitigations

- Deterministic local processing; no supported public AI/provider workflow or automatic remediation.
- Common-secret redaction and terminal escape/control sanitization for normal evidence paths.
- HTML escaping of log-derived report fields.
- Bounded file-line ingestion, retained dashboard samples, live reads/windows, and detection/correlation state.
- Read-only native collection with fixed argument lists, validated channel names, timeouts, and bounded requested record counts.
- Parameterized database queries and explicit local persistence.
- Regression tests for malformed telemetry, terminal safety, timestamp handling, streaming, and evidence reporting.
- Dependency auditing, hashed toolchain locks, package and Windows builds, and guarded release workflows.

## Residual risks

Redaction is best effort; restrict report/database access and use sanitized data in public issues. Files or sources outside the analyzed retention window can contain missed evidence. Some legacy commands load complete files. Native collector subprocess output can still contain large individual messages. Trusted custom regular expressions can hang on pathological input; do not install untrusted rule packs.

Synthetic regression accuracy is not independent real-world validation. Analysts must validate findings against source evidence and operational context before acting.

The Windows release is unsigned. Check release SHA-256 and provenance; successful builds and terminal-width tests do not replace real Windows runtime and visual review.
