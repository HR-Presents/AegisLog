# Roadmap

Current published release: **v2.1.6**. This roadmap describes priorities, not delivery promises or features already available.

## Released

- Terminal file analysis, single/multi-source live monitoring and supported native collectors.
- Deterministic findings, incident groups, bounded retained evidence and rarity signals.
- Guided computer checks, folder discovery/deduplication, reports and investigation tools.
- Summary/full-evidence HTML printing, dark readable text, demo labels and timestamp limitations.
- Windows executable, Python packages, checksums and CI/release validation.

The D browser dashboard is removed. The Windows executable is unsigned. Synthetic evaluation is regression evidence; findings and rarity do not establish compromise.

## Proposed priorities

| Priority | Work | Acceptance evidence |
|---|---|---|
| 1 | Fresh-PC installation and clearer onboarding | Reproducible Windows installation checks, PATH troubleshooting and beginner feedback |
| 2 | Broader structured log coverage | Sanitized fixtures for each documented format, explicit partial/unsupported coverage |
| 3 | Reduce noisy findings without hiding evidence | Context-aware regressions covering benign and concerning events; visible tuning decisions |
| 4 | Improve report portability and print pagination | Browser/PDF checks for small and large investigations, complete retained references |
| 5 | Expand platform/version validation | Python 3.14 and terminal compatibility jobs before claiming support |
| 6 | Windows signing | Secure certificate integration and validated Authenticode signatures before claiming signed binaries |
| 7 | Independent real-world evaluation | Authorized sanitized datasets, independent labels and measured limitations |

## Feedback

Open a feature request describing the user problem, supported source, expected result and a safe example. Issues do not imply scheduled implementation. No dates are committed here. Read-only defensive scope remains central; automatic remediation and host control are outside the current product direction.
