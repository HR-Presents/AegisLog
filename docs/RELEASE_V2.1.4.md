# AegisLog v2.1.4 — prepared release notes

Status: prepared, not published. Existing v2.1.3 assets and tags must remain unchanged.

## Changes

- Remove D Local Dashboard while preserving the original terminal home and charts.
- Improve responsive navigation, help, report opening and source discovery.
- Add guided computer checks and bounded folder scans with batch reports.
- Improve structured-record parsing, coverage summaries and grouped findings.
- Harden output/source separation, terminal sanitization and input bounds.
- Refine light HTML reports with dark readable text, evidence and printing.

## Validation

Audited code: `3fa654012458ca91e38ca40dd31e25d016dec70a`.
515 tests passed; seven PR workflows passed, including Windows executable build and read-only native System collection. Synthetic detection evaluation passed; it is not a production accuracy measurement. Owner tested Windows Security collection and report opening. Python CI covers 3.10–3.13.

## Verified development download

[Windows ZIP](https://github.com/HR-Presents/AegisLog-AI/actions/runs/37114547828/artifacts/11271098131) (GitHub sign-in may be required).

ZIP SHA-256: `1f7fbca6b74cb8bd3cde8a4ed51640a0b9175956bc4d0eb5d828dfeaafba2510`

Executable SHA-256: `45c9430106f7843ef16ef44d2d499a666872ead6abedc5f703daa0c4e3db0f7f`

The ZIP contains the executable, matching checksum, quick start and three demo files. Both hashes were recomputed from the downloaded artifact. This artifact still reports 2.1.3 and is unsigned; it must not be relabeled as the v2.1.4 binary.

## Remaining release preparation

Before publishing v2.1.4, bump package/runtime version together, adapt the immutable versioned release workflow for the new tag, rerun validation and build new assets from that exact commit. Verify new hashes and provenance before attaching them to a draft release. Do not reuse the development hashes above for rebuilt assets.

## Scope

Local read-only investigation; findings are leads, not proof of compromise. Native snapshots and retained charts are bounded. Security logs may require administrator access. Unsupported records and zero findings do not establish a clean system. See LIMITATIONS.md and FINAL_AUDIT.md for remaining constraints.
