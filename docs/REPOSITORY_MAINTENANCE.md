# Repository maintenance

## Main branch controls

The repository owner should enable a main-branch ruleset requiring pull requests, passing CI and Security checks, and prohibiting force pushes and branch deletion. Add Windows executable validation where the required status is emitted reliably. Apply rules to administrators if that matches the team's release policy. These administration settings cannot be changed by the connected repository app; this file does not enable them.

## Historical release workflows

Version-specific release files include historical retired markers and draft/publication infrastructure. All version-specific release, publication and release-note update jobs are now disabled with explicit job guards; historical markers and bodies preserve regression history. Do not count every file as an active publishing pipeline or dispatch old publication workflows against an already published release. Current routine checks are CI, Security, Windows executable builds, dependency-lock audits and demo-pack validation.

A future release should consolidate draft preparation and publication into a reviewed reusable workflow with an explicit tag, build commit and draft check. Preserve existing immutable published assets and tags. A reusable future-release workflow is still pending; the audit fixes do not rebuild the published v2.1.11 executable.

## External validation

Authenticode signing requires an organization-controlled certificate and credentials. Real-world precision and recall require an independently labeled, authorized dataset. Synthetic regression results do not satisfy either requirement.
