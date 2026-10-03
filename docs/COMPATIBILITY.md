# Compatibility and coverage

| Input | Current handling | Limits |
| --- | --- | --- |
| Windows native logs | System, Application and Security snapshots; provider, event ID, level and message normalization | Channel access, event cap and selected time window affect coverage |
| Linux journald | Read-only journalctl snapshots in short-iso format | journalctl and journal access required; bounded count/window |
| Docker | Existing terminal collectors for a named container | Docker CLI, engine and container access required; not auto-discovered by the guided dashboard |
| RFC3164/syslog text | Service/message extraction and supported time handling | Yearless timestamps need context; generic fallback for unmatched layouts |
| ISO service logs | Recognized timestamp/level/service layouts | Arbitrary application conventions are not guaranteed |
| Web access logs | Recognized common request/status patterns | Custom field layouts may fall back to generic text |
| One JSON object per line | message/service fields and journald-style fields | Whole-file JSON arrays and vendor-specific schemas are not general importers |
| CSV/TXT discovered in folders | Candidate text files scanned by existing line rules | CSV columns are not mapped by a dedicated schema importer |
| EVTX, compressed archives, UTF-16 or binary data | Not supported by the guided file workflow | Export readable UTF-8 text first |
| macOS | File investigations and local graphical interface | No macOS native log collector is provided |

Python package: Python 3.10+; automated compatibility checks currently cover 3.10–3.13. The Windows executable is built with Python 3.12. A newer installed Python version is not equivalent to a tested compatibility guarantee.

Source discovery checks actual bounded read access and checks existing known Windows DISM/CBS or Linux auth/syslog/Nginx/Apache log paths. It does not discover every application log location on a computer. Folder discovery is recursive and bounded, skips symlinks, and lists candidate extensions. Each source is analyzed separately.

The dashboard and guided check expose retained parser-format counts, generic fallback and retention notes. Generic parsing can still match rules but should not be interpreted as complete structured understanding. No findings is not evidence of complete coverage or absence of compromise.

Detection regressions use the synthetic labeled fixture in evaluation/labeled_events.jsonl. Production-effectiveness claims require independent external evidence as described in EXTERNAL_DETECTION_EVIDENCE.md. No benchmark here is a claim of universal precision or recall.
