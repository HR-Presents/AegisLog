# First-user feedback checklist

Ask a few Windows users to try this independently. This checklist prepares feedback collection; it does not claim those sessions have happened.

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

Share feedback through a [GitHub issue](https://github.com/HR-Presents/AegisLog-AI/issues). Do not upload real logs without permission and review. AegisLog's aggregate sharing summary omits identifiers and raw evidence, but review any exported file before posting it.

## Launch decision

Resolve installation failures, crashes, missing reports and misleading coverage first. Record the tested environment and outcome. Several successful sessions are useful usability evidence; they do not establish real-world security detection accuracy.
