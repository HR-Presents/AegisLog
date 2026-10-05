# Compatibility and coverage

| Input | Current handling | Limits |
| --- | --- | --- |
| Windows native logs | System, Application and Security snapshots; provider, event ID, level and message normalization | Channel access, event cap and selected time window affect coverage |
| Linux journald | Read-only journalctl snapshots in short-iso format | journalctl and journal access required; bounded count/window |
| Docker | Existing terminal collectors for a named container | Docker CLI, engine and container access required; not auto-discovered by the guided dashboard |
| RFC3164/syslog text | Service/message extraction and supported time handling | Yearless timestamps need context; generic fallback for unmatched layouts |
| ISO service logs | Recognized timestamp/level/service layouts | Arbitrary application conventions are not guaranteed |
| Web access logs | Recognized common request/status patterns | Custom field layouts may fall back to generic text |
| JSON/JSONL | Scalar message/msg/MESSAGE records, JSON arrays or an events array | Whole-file containers capped at 8 MB; arbitrary vendor fields remain unrecognized |
| Header-based CSV | Timestamp, message/msg, service and level columns; recognized network flow columns | Header is metadata, not an event; unmatched schemas show limited coverage |
| Zeek conn TSV/JSON | ts, id.orig_h/id.resp_h and connection metadata | Connection states alone do not prove an attack; other Zeek schemas may be unrecognized |
| Suricata EVE | Alert signature/severity mapped to an upstream IDS finding; flow telemetry preserved | Upstream alerts require validation; not independent packet inspection |
| TXT and unknown structures | Generic line rules only | Not complete structured interpretation; zero findings does not mean clean |
| EVTX, compressed archives, UTF-16 or binary data | Not supported by the guided file workflow | Export readable UTF-8 text first |
| macOS | File investigations and terminal investigations | No macOS native log collector is provided |

Python package: Python 3.10+; automated compatibility checks currently cover 3.10–3.14. The Windows executable is built with Python 3.12. A newer installed Python version is not equivalent to a tested compatibility guarantee.

Source discovery checks actual bounded read access and checks existing known Windows DISM/CBS or Linux auth/syslog/Nginx/Apache log paths. It does not discover every application log location on a computer. Folder discovery is recursive and bounded, skips symlinks, and lists candidate extensions. Each source is analyzed separately.

The terminal dashboard and guided check expose retained parser-format counts, generic fallback and retention notes. Generic parsing can still match rules but should not be interpreted as complete structured understanding. No findings is not evidence of complete coverage or absence of compromise.

Detection regressions use the synthetic labeled fixture in evaluation/labeled_events.jsonl. Production-effectiveness claims require independent external evidence as described in EXTERNAL_DETECTION_EVIDENCE.md. No benchmark here is a claim of universal precision or recall.

Folder scans default to likely log candidates. Include other text/configuration files explicitly when needed. Identical SHA-256 content can share one report while retaining every selected relative source path. A searchable batch overview and JSON manifest distinguish completed, duplicate, failed, cancelled and pending sources. B/Escape/Ctrl+C cancels safely; completed reports remain available. R lists all saved summaries and batch overviews in pages of 20. O opens a completed report; F opens its folder.

Physical line counts, record counts and recognized record counts are separate. Coverage describes recognized structure, not detection recall. CSV headers and Zeek metadata are excluded from record totals. Malformed and truncated inputs are disclosed.

JSON input nesting is capped at 64 levels. CSV fields are capped at the configured line limit (1 MB by default); malformed records are flagged and parsing proceeds where the CSV reader can recover. The report CLI uses the same bounded structured analysis as the terminal dashboard. Security Workbench, streaming and live monitors normalize known single-object JSON log records while retaining line-oriented detection scope; they are not universal schema importers. Docker snapshots retain both stdout and stderr; separately captured streams do not preserve exact interleaving. Local custom regex packs are trusted user configuration and are not an execution-time sandbox.

Python 3.14 has a hash-locked Linux validation lane and Windows command smoke coverage. Windows checks cover installation, terminal start/quit, diagnostics, report identity and the portable streaming benchmark; they do not establish every terminal emulator or every native channel permission combination. The single executable remains built with Python 3.12.
