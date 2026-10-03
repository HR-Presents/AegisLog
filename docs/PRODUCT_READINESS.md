# Product readiness

## Implemented

- Existing terminal retained with guided C Check Computer, F Scan Folder and D Local Dashboard.
- Local graphical snapshot investigations with beginner/analyst views, adjustable text, keyboard controls, labeled severity counts, source descriptions and access probes.
- Native time-window selection and bounded event counts; collection scope/retention shown explicitly.
- Practical finding explanations, operational/security classification and alternative explanations in the guided interface.
- Local summary/full evidence reports plus credential-redacted JSON for integration with other tools.
- No automatic telemetry uploads; existing public issue templates and feedback links.
- Build checks, synthetic detection regression gate, dependency/security checks, executable checksum generation and signing/verification adapters.

## External requirements before a signed stable release

A trusted Windows code-signing identity/certificate and its protected credentials must be supplied by the project owner. Existing signing/Authenticode adapters must be used with that identity; unsigned PR artifacts are not signed releases. Do not label them as such.

A stable release requires choosing and publishing a reviewed version/tag. The review-branch pipx URL is convenient for testing but changes as commits land. For reproducibility use an immutable commit archive or a verified release tag. Existing release-security checks remain authoritative.

Independent authorized real-log datasets and reviewers are needed to validate detection effectiveness. Do not manufacture accuracy figures from synthetic fixtures. See EXTERNAL_DETECTION_EVIDENCE.md.

## Remaining product work

- Dedicated native desktop packaging/installer; the current graphical UI opens in a browser.
- Broader application discovery beyond native channels, known DISM/CBS/auth/syslog/Nginx/Apache paths and explicit folder scans.
- Unified cross-file investigations with preserved origin; current folder scanning generates independent reports.
- Broader vendor-schema integrations, localization, accessible-user trials, and long-session field validation.
- A narrated public product tour; a short silent browser demo and GETTING_STARTED.md walkthrough are provided with this update.

These are explicit limits, not reasons to hide working features. Keep release claims aligned with the tested build.
