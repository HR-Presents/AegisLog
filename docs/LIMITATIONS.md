# Current limitations

AegisLog provides local deterministic defensive log investigation. It is not a SIEM replacement, does not inspect packet contents, and does not perform remediation or prove compromise.

## Detection and evaluation

Rules cover selected authentication, privilege, web, firewall, service, and Windows Security events. Unknown formats and tactics may be missed. Timestamp-free authentication events use bounded event order; syslog timestamps without a year need explicit year context. Anomaly scores measure rare concerning event classes in the retained sample, not a trained historical machine-learning model.

Maintained evaluation datasets are synthetic regression evidence. Passing them does not establish real-world effectiveness, deployment-specific false-positive rates, or adversarial robustness.

## Resource and evidence limits

File ingestion retains at most 1,000,000 bytes per line by default; oversized tails are discarded in bounded chunks before decoding. Content beyond that prefix cannot be detected.

The analysis dashboard processes all bounded lines but keeps at most 10,000 recent event lines and 8,000,000 encoded bytes for activity charts and anomaly scoring. Service distributions aggregate across the file, with excess distinct services grouped after 2,048 keys and log levels after 32 keys. Dashboard service labels are capped at 128 characters and level labels at 32; retained authentication identifiers are capped at 256 characters. Detection state separately caps findings, authentication sources, and events. Terminal summaries and HTML reports disclose truncation, event sampling, and evidence eviction. Retained findings and incident views are not complete copies of original telemetry; preserve source logs.

Live monitoring uses rolling line/byte windows and bounded reads. Rotation, collection permissions, source availability, and unsupported log formats affect coverage. Baseline and indicator extraction use bounded recent samples; they do not inspect all records in large files. Whole JSON containers are limited during reading to 8 MB; larger or growing containers fall back to line-oriented parsing with explicit format coverage.

## Product and release boundaries

AI Analyst and remote providers are not part of the supported public v2 command surface. Historical provider modules remain for compatibility tests.

Windows native telemetry and the packaged executable require Windows for final runtime and visual acceptance. A successful executable build does not establish visual acceptance. The published executable is unsigned; compare its release checksum before use.

The development Security Workbench analyzes a bounded recent sample and supports additional failure-to-success and process-review signals. See [its detection, retention, tuning and integrity limits](SECURITY_WORKBENCH.md). Live monitors use default sequence thresholds; supplied watchlists and tuning are currently workbench-scoped.
