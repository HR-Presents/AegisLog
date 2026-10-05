# Detection rules

AegisLog uses deterministic rules for authentication failures, selected Windows security events, suspicious privilege and web activity, operational failures and recognized Suricata alerts. Parsing a format does not mean every possible threat in that format is detected.

Authentication correlation uses extracted account, host and source context. Resolved timestamps support time windows; yearless syslog requires an explicit year hint. Without one, bounded event-order grouping does not establish elapsed time.

Windows incident grouping includes provider, Event ID, account/host context and a maximum five-minute span. Generic fallback grouping has no time-window guarantee. Incident IDs use the same correlation implementation in reports and investigation commands.

`analyze` includes enabled local declarative rule packs in the displayed findings and HTML report. Use `--no-plugins` to exclude them. Rule packs are trusted operator configuration; review their patterns and severity choices. Findings are investigation leads, not proof of compromise. Synthetic tests verify supported examples, not real-world accuracy.
