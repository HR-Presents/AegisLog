# AegisLog documentation

Welcome to the AegisLog documentation hub. Start with the user guide for the complete workflow, or jump directly to the area you need.

> **Project posture:** AegisLog is defensive, terminal-first, local-first, read-only by default, and deterministic for detection and correlation. AI Analyst and remote-provider workflows are not part of the supported public product surface.

## Start here

| Goal | Guide |
|---|---|
| Current release / upgrade | [v2.1.7 notes](RELEASE_V2.1.7.md) / [Upgrade](INSTALL.md#upgrade-and-verify) |
| Proposed improvements | [Roadmap](ROADMAP.md) |
| Install AegisLog | [Installation](INSTALL.md) |
| Run your first analysis | [Quick Start](QUICKSTART.md) |
| Learn the complete workflow | [User Guide](USER_GUIDE.md) |
| Find a command | [Command Reference](COMMANDS.md) |
| Try safe synthetic data | [Demo](DEMO.md) |
| Fix a problem | [Troubleshooting](TROUBLESHOOTING.md) / [FAQ](FAQ.md) |

## Detection and investigation

- [Detection pipeline](DETECTION_PIPELINE.md) — how telemetry moves through the analysis path
- [Parsers](PARSERS.md) — normalization and supported input structures
- [Rules](RULES.md) — declarative detection behavior
- [Collectors](COLLECTORS.md) — supported native telemetry sources
- [Incidents](INCIDENTS.md) — correlation and incident handling
- [Anomalies](ANOMALIES.md) — anomaly-scoring context and limitations
- [Watch Mode](WATCH.md) — live monitoring behavior
- [Report schema](REPORT_SCHEMA.md) — structured report output

## Security and data handling

- [Threat model](THREAT_MODEL.md)
- [Security notes](SECURITY_NOTES.md)
- [Privacy](PRIVACY.md)
- [Why local-first](WHY_LOCAL_FIRST.md)
- [No automatic remediation](NO_AUTOREMEDIATION.md)

Older AI/provider documents may remain in repository history for traceability, but they do not define the supported v2 product surface.

## Product and operator experience

- [User Guide](USER_GUIDE.md) — Mission Control and direct CLI workflows
- [Commands](COMMANDS.md) — supported CLI entry points
- [Screenshot capture](SCREENSHOT_CAPTURE.md) — requirements for verified public product screenshots
- [Community reviews](COMMUNITY_REVIEWS.md) — transparent public feedback policy
- [Support](../SUPPORT.md) — choosing the right help or reporting path

Public screenshots should come from a verified build and sanitized or synthetic telemetry. Automated rendering checks do not, by themselves, establish visual acceptance on Windows.

## Engineering

- [Architecture](ARCHITECTURE.md)
- [Design principles](DESIGN_PRINCIPLES.md)
- [Configuration](CONFIGURATION.md)
- [Testing](TESTING.md)
- [Performance](PERFORMANCE.md)
- [Limitations](LIMITATIONS.md)
- [Project status](PROJECT_STATUS.md)
- [Roadmap](ROADMAP.md)
- [Versioning](VERSIONING.md)
- [Maintainer guide](MAINTAINERS.md)
- [Release checklist](RELEASE_CHECKLIST.md)
- [External evaluation runbook](EXTERNAL_EVALUATION.md)

## Release status

- **Published stable:** [v2.1.7 release notes](RELEASE_V2.1.7.md)
- **Build commit:** `e7af0798c731720690f298c093deec74f42fa56a`
- **Downloads and matching checksums:** [v2.1.7 release](https://github.com/HR-Presents/AegisLog-AI/releases/tag/v2.1.7)
- **Upgrade:** [Installation](INSTALL.md#upgrade-and-verify) / [Upgrading](UPGRADING.md)
- **History:** [Changelog](../CHANGELOG.md)

The Windows executable is unsigned. CI artifacts are validation outputs; published release assets are the customer distribution channel.

## Contributing

Want to improve AegisLog? Read [CONTRIBUTING.md](../CONTRIBUTING.md) before opening a pull request. Keep changes focused, defensive, testable, and free of real credentials or sensitive production telemetry.
