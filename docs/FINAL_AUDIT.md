# Final terminal build audit — 3 October 2026

This is an engineering review of the current review branch, not an independent penetration test or production detection certification. The original terminal design and HTML reports remain. The optional browser dashboard and desktop command are removed.

## Scope and evidence

| Area | Verification | Practical boundary |
| --- | --- | --- |
| CLI and navigation | All 41 command help pages; Back/Quit, responsive layouts and browser-command removal regressions | Terminal font and rendering still depend on the user's host |
| Installed distribution | Wheel built and installed outside the source checkout with hash-locked runtime dependencies; version, doctor, terminal dashboard, HTML report and start/Quit smoke commands passed | Local installation checks used Python 3.12; compatibility CI covers 3.10–3.13 |
| Analysis | 515 tests, including structured inputs, malformed records, retention and source preservation | Recognition of a schema does not measure detection recall |
| Detection | 18 labeled synthetic cases pass the existing regression gate | No production accuracy or zero-false-positive claim |
| Native sources | Windows argument/channel restrictions and access-denied tests; journald format and Docker stderr/timestamp tests; packaged Windows System snapshot smoke added to CI | Security-channel access depends on host permissions; Docker needs its engine and container access |
| Folder scans | Selection, relative paths, identical-content sharing, completed/cancelled/pending states and searchable overview tests | Each source is analyzed independently; discovery remains bounded |
| Reports | Source/symlink/hardlink collision protection; structured CLI reports, grouped evidence and escaping tests; summary/full-evidence links and print QA | Reports contain retained derived evidence, not complete original telemetry |
| Presentation | Demo: 957 records, 44 findings, 22 incident groups; summary prints to three A4 pages in Chromium | Pagination can differ by browser and printer settings |
| Resource behavior | 250,000-line synthetic streaming check completed in 6.64 seconds in this environment; large CSV regression exercises the corrected text parser | This stream benchmark is not a performance guarantee for every command or log mix |
| Static checks | Ruff and Bandit pass; dependency and lock audits run in CI | Static scanners are not proof of vulnerability absence |

## Confirmed issues corrected

- Report/export targets could alias source files through matching paths, symlinks or hard links. Shared preflight checks now reject source collisions, including the guided evidence.json export and the report CLI.
- Docker snapshots omitted stderr. They now retain stdout and stderr, reject option-like container names and normalize timestamped records for terminal service/activity views. Separately captured streams do not preserve exact interleaving.
- CSV fields above the parser's previous default threshold could stop processing before later findings. Fields now use the configured line limit; errors are counted and parsing proceeds where the CSV reader can recover. Extra cells in invalid rows remain in retained evidence, and duplicate headers are flagged.
- Excessive JSON nesting could raise uncaught recursive parsing/redaction errors. Supported input parsing caps nesting at 64 levels; unsupported deep inputs are disclosed, and fallback credential redaction handles quoted keys.
- An unanchored web-log regex was slow on large unmatched text. Common access-log matching now starts at the beginning of the line; existing syslog web parsing remains available.
- Structured terminal activity could use original raw fields instead of normalized timestamps. It now uses normalized retained event timestamps, including Zeek epoch timestamps.
- Message-bearing JSON without a timestamp could lose its service metadata. Valid scalar service metadata is retained; object-valued metadata is treated as unknown.
- Standard journald short-iso host/service records now receive explicit parsing. Parsed event output also removes terminal control sequences.
- The report CLI previously used a separate whole-file, line-only route. It now shares bounded structured dashboard analysis, provides coverage/counts in JSON, and uses the current branded summary/evidence pair for HTML.
- Additional local rule-pack processing no longer reads the entire input into a list before applying rules.

## Remaining limits and release requirements

1. Independent authorized real-log datasets and reviewers are needed to establish detection effectiveness. The current rules, incident grouping and rarity scoring do not prove an attack or a clean system.
2. Folder reports remain independent investigations. Cross-file attribution and unified vendor-schema workflows require additional implementation and validation.
3. Live monitors and the Security Workbench retain their documented line-oriented scope. They are not universal structured-schema importers.
4. JSON containers are capped at 8 MB, nesting at 64 levels, CSV fields/physical line prefixes at the configured default 1 MB, and retained dashboard evidence at 10,000 records/8 MB. Check the displayed coverage and retention notes.
5. Some older commands, including baseline and indicator extraction, can still load a complete file. Use bounded stream/file workflows for large inputs.
6. Custom regex rule packs are trusted local configuration. Their patterns are not executed in a timeout sandbox; poorly chosen patterns can be slow. Test a pack on bounded samples before using it.
7. Review builds remain unsigned. A trusted signing identity, reviewed release tag and real-user acceptance are required before claiming a polished commercial release. Windows Security permissions are not bypassed or changed.

See COMPATIBILITY.md, LIMITATIONS.md, SECURITY_WORKBENCH.md and RELEASE_SECURITY.md for detailed operating boundaries. Passing the documented checks is evidence for the reviewed behavior, not a claim that every possible input or host environment has been tested.
