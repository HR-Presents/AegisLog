# AegisLog v2.1.6

This patch includes the latest report export and interpretation fixes.

- Visible synthetic-data labeling for the built-in demo, identified by content rather than filename.
- Clear timestamp limitations for yearless syslog and event-order correlation.
- Summary-only PDF labeling and a complete-report print action.
- Compact printed metrics, readable dark text on light backgrounds, and preserved AegisLog branding.
- Print sections stay together where they fit.
- Includes the folder report, grouped findings, native channel labels and responsive terminal fixes from v2.1.5.

Regenerate existing reports after upgrading. Disable browser Headers and footers when saving PDFs to remove browser-added local file paths. Full evidence refers to retained derived evidence; preserve original telemetry separately. Synthetic regression evidence does not establish real-world detection accuracy. The user reported completing the Windows workflow checks; automated checks additionally validate commands and native System collection.

The Windows executable is unsigned. Build provenance is separate from Authenticode signing. v2.1.6 is published with fresh checksums and preserves earlier releases. Upgrade using the published wheel or replace the standalone executable; see [installation and upgrade instructions](INSTALL.md#upgrade-and-verify).
