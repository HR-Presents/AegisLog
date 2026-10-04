# Investigation improvements

These additions are merged on main and being packaged for v2.1.10. The existing v2.1.9 downloads remain unchanged.

## Review and prioritise

```powershell
aegislog review "C:\Logs\application.log" --limit 20
```

Review orders presentation groups by severity, then occurrence count. Groups keep distinct provider, host, account and source-address context when available, show first/last resolved evidence timestamps and explain impact, possible ordinary causes and next steps. Frequency does not increase detector severity or establish a common cause. First/last refer to retained finding excerpts, not necessarily every source event. Unresolved timestamps remain unresolved. The complete report retains evidence; its approved layout is unchanged.

Windows session context links successful logon (4624), privilege assignment (4672) and process creation (4688) records only when explicit host, logon ID and resolved timestamps are available. Links cover at most five minutes following a successful logon, within the retained sample. At most 100 links and 1,000 related records per link are presented, with omitted context counts recorded. Successful logons are informational. Audit settings and protected-source access determine available evidence; AegisLog does not enable auditing or change permissions.

## Search saved investigations

```powershell
aegislog cases --query timeout --severity MEDIUM --since 2026-10-01
aegislog cases --query timeout --open-number 1
```

Static analysis, guided computer checks and folder scans create local case metadata alongside new reports. Search matches source labels and finding titles, with optional date/severity filters. Metadata contains identifiers and should be treated as private. Search reads up to 10,000 metadata candidates and returns up to 500 results; default 100. Old reports are still accessible through R Reports, which also accepts `search <filename text>`; their finding titles are not automatically indexed. No HTML evidence is loaded for metadata search.

## Compare and share

After a computer check, V compares provider counts and normalized sample shares. Newly generated baselines also classify detector signal labels as newly observed, recurring or not observed in the current sample. Choose the same source/time-window label and comparable collection limits, source availability and workload. These are sample comparisons, not event rates. Not observed does not mean resolved. Older baselines support provider comparison but require regeneration for signal comparison.

S shows the complete aggregate sharing JSON before offering to save it. The default is to decline. Source names, provider names, paths, timestamps, accounts, addresses, raw evidence and signal titles are omitted. Aggregate counts may still reveal sensitive operational patterns. Existing sharing files are never overwritten.

## Collection and formats

Static analysis shows processed line/record counts; folder scans show periodic counts and per-file status. Counts describe work completed, not a percentage or predicted remaining time. Cancellation also polls while discarding oversized line tails. Folder cancellation preserves completed reports and marks cancelled/pending sources separately. Native collector subprocesses remain bounded snapshots; they do not expose per-event progress while collecting.

Two explicit application adapters are added: Docker `json-file` records (`time`, `stream`, `log`) and Elastic Common Schema message records (`@timestamp`, `message`, optional `service.name`/`log.level`). Existing deterministic rules apply to normalized messages. These adapters do not add Docker infrastructure monitoring or comprehensive ECS field interpretation. Unknown schemas remain unrecognized; format recognition does not establish complete detection coverage.

## Troubleshooting and updates

```powershell
aegislog diagnostics --output support.json
aegislog update-check
```

Diagnostics exports only tool/Python versions, OS family, architecture and packaged-runtime status. It omits environment variables, configuration, paths, usernames, hostnames, logs and evidence. No existing file is overwritten. This is a basic support snapshot rather than a complete failure diagnosis.

Update check contacts the fixed public GitHub latest-release endpoint only when invoked. It uses a ten-second timeout and bounded response, rejects redirects, sends no logs or configuration and never installs or executes downloads. GitHub can observe the request's network address. Offline failure leaves the installed application unchanged. Use release checksums when downloading packages.

## Validation and remaining external work

```bash
PYTHONPATH=src python benchmarks/investigation_benchmark.py --records 10000
PYTHONPATH=src python tools/evaluate_detections.py evaluation/labeled_events.jsonl --dataset-kind synthetic
```

The benchmark measures synthetic static parsing, grouped presentation, retained context, throughput and peak Python allocations; it excludes native/process RSS and is not an SLA. CI exercises the new commands in the Windows executable. Regression tests cover false session links, timestamps, input coverage, cancellation, privacy and malformed metadata. Independent accuracy evaluation, broader device acceptance, support commitments and a signing certificate remain external work; these features do not establish enterprise assurance.
