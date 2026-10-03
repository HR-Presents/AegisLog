# AegisLog v2.1.5

This patch improves folder-report printing and native terminal investigations.

- Light reports with dark text and a readable five-column printed source appendix.
- Explicit unique/duplicate counts, format coverage, and operational versus security leads.
- Grouped repeated terminal findings, responsive panels, native channel labels and current-report actions.
- Consecutive minute charts preserve time gaps within the bounded retained sample.
- Windows 4672 events with verified built-in service account SIDs remain available as informational baseline evidence. Other privileged logons retain their severity.
- The D browser dashboard remains removed.

Regenerate existing HTML/PDF reports after upgrading. Real Windows interactive redraw needs user confirmation. Synthetic regression tests do not establish real-world detection accuracy.

The Windows executable is unsigned. Build provenance is separate from Authenticode signing. This workflow prepares an immutable draft for review and does not replace existing releases.
