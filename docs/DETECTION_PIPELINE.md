# Detection pipeline

1. Read bounded physical lines and normalize supported record formats.
2. Redact recognized secrets and remove terminal control sequences.
3. Apply deterministic rules with bounded retained findings and authentication state.
4. Correlate signals using shared context; use resolved timestamps where available.
5. Score rarity within the retained sample, not attack probability.
6. Generate the local summary, retained evidence appendix and case metadata after checking output/source collisions.
7. Open investigation commands using the same incident IDs as the report.

Known JSON log objects are normalized for line-oriented collectors too. JSON containers and CSV schemas still require the static file adapter; they are not interchangeable with an appended JSONL stream. Parsing coverage, detection coverage and retained evidence are distinct metrics.

Public workflows use local deterministic analysis. Original telemetry remains authoritative; reports contain derived retained evidence. No matching rule establishes a clean system.
