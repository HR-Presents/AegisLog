# First-user feedback checklist

Use this checklist for independent Windows trials and record each environment and outcome.

1. Follow [Quickstart](QUICKSTART.md) from a fresh terminal. Record whether you used the executable or Python/pipx and whether the command opened.
2. Extract the [demo pack](demo/README.md), analyze first-investigation.log, and compare the result with expected-results.json.
3. Open the summary and complete evidence report. Check text readability, navigation, and PDF output at your usual screen size.
4. Analyze clean-baseline.log. Confirm the interface describes coverage and does not call the system clean.
5. Press B, then Q. Confirm the normal terminal prompt returns.
6. Optionally try C Check Computer. Record channel availability; denied Security access is an expected permissions outcome without elevation.

## Feedback template

- Windows version and terminal:
- Installation method:
- Step that failed or felt confusing:
- Expected behavior:
- Actual behavior:
- Error text (remove account names, addresses, paths and raw evidence):
- Report readability / print issue:
- Whether you could return to your terminal:

Share feedback through a [GitHub issue](https://github.com/HR-Presents/AegisLog/issues). Do not upload real logs without permission and review. AegisLog's aggregate sharing summary omits identifiers and raw evidence, but review any exported file before posting it.

## Launch decision

Resolve installation failures, crashes, missing reports and misleading coverage first. Record the tested environment and outcome. Several successful sessions are useful usability evidence; they do not establish real-world security detection accuracy.

## Current validation record

On 5 October 2026 (Asia/Dubai), the project owner reported that the guided demo workflow completed successfully and subsequently confirmed that everything was working. This is user-reported acceptance feedback; individual tester counts, Windows versions and installation methods were not supplied.

The reviewed launch changes passed 596 automated tests, package and Windows executable checks, security checks, and demo verification. The downloadable pack was rebuilt byte for byte against its checked sources and SHA-256 checksum. The main demo produced 9 recognized records, 2 findings and 1 incident group; the baseline produced 3 recognized records and no matching findings.

The quickstart, demo ZIP, supported-input guidance and announcement draft are published in the repository. Successful trials validate the exercised workflows; they do not establish universal compatibility or real-world detection accuracy.
