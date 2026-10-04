# AegisLog first investigation demo

SYNTHETIC TRAINING DATA. All events, accounts and documentation-range addresses are fictional. This pack does not test every AegisLog capability or measure real-world detection accuracy.

## Files

- first-investigation.log: nine ISO-timestamped text records, including six authentication failures, one timeout, and two informational records.
- clean-baseline.log: three informational records with no matching detector findings. Zero findings is not a clean-system verdict.
- expected-results.json: expected static-analysis counts and rule titles.
- README.md: these instructions.

## Start

Extract the ZIP. Run `aegislog start` (or open the Windows executable), choose 01, and paste the full path to first-investigation.log. Use O Reports or R at home to open the summary and follow its full-evidence link.

Expected: 9 records, 9 recognized, 2 findings (HIGH 1 / MEDIUM 1), and 1 incident group. Six failed logins become one authentication-burst finding; finding counts are not raw-event counts. Timestamps span 12:01–12:04 UTC on 4 October 2026.

Repeat with clean-baseline.log: 3 recognized records, 0 findings, 0 incident groups. Review coverage even when there are no matches.

## Explore

- 06 Incidents: select the same log to review its grouped leads.
- S Workbench: select the log, inspect Details and Timeline, filter retained evidence, and export.
- F Folder: select the extracted folder and choose log files; analyze them separately.
- Reports: use both generated HTML files together; print from the report to save PDF.
- Live: monitoring a static fixture produces no new events. Use a separate copy, monitor it, and append synthetic lines yourself to explore updates. Do not append to your only original copy.

Native collection, permissions, Docker availability, historical case searches, and real-world detection quality require separate checks on your own environment. This fixture does not simulate them.

MADE BY HR-PRESENTS
