# Folder report and native terminal refinements

Folder reports retain the light background, dark text and AegisLog logo. Browser tables can scroll horizontally; printed overviews use a separate five-column source appendix. Browser search does not remove sources from the printed appendix. Batch summaries explain unique sources, duplicates, failed/cancelled/pending entries, scan mode and format coverage. Operational matches and security/other leads are separated; neither is a confirmed-attack count. Disable browser headers and footers when saving a shareable PDF.

Windows Event 4672 for the exact built-in service SIDs S-1-5-18/19/20 remains retained as informational baseline evidence. A display name alone does not downgrade a finding. Other events and unknown SIDs keep their existing detection priorities. Review unexpected privileges and correlated activity; informational classification does not establish safety.

Terminal findings are grouped by severity, category, title and recommendation. The original panels and palette are retained; their width follows the viewport. The medium-or-higher share is explicitly labelled as a finding fraction, not a compromise score. Activity shows consecutive minutes from the retained sample, including empty buckets; retained-sample zeros do not prove the source had no activity.

Native snapshots identify the Windows channel, journald or Docker source and disclose the collection bound. Result controls open the current report or its folder directly. The home clears the restored terminal buffer before using its alternate screen. Real Windows screen redraw behavior still needs interactive user confirmation; CI exercises command execution and native snapshot collection.

The existing v2.1.4 draft release is immutable and predates these changes. Use the reviewed patch commit or its workflow artifact when testing these refinements.
