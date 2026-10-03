---
name: Feature request
about: Propose a defensive, local-first improvement
title: "[feature] "
labels: enhancement
---

## Problem or use case

What defensive analysis or investigation problem would this solve? Describe the user and workflow rather than only the proposed implementation.

## Current version and source format

Which AegisLog version and log format/source are involved? Check docs/ROADMAP.md for proposed priorities.

## Proposed outcome

What should AegisLog do, and what would a successful result look like?

## Example workflow

```text
Show an example command, control-center path, or sanitized input/output when useful.
```

## Security and privacy boundaries

Could this change log collection, local data storage, redaction, external data transfer, privileges, or system state? AegisLog features should remain defensive, read-only, and local-first; remote AI is not part of the supported public product surface.

## Alternatives

What workarounds or alternative designs have you considered?

## Additional context

Do not include credentials, tokens, private production logs, customer data, or personal information. Report exploitable vulnerabilities privately through `SECURITY.md` instead of this template.
