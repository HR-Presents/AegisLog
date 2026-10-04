# Investigation reports

AegisLog generates a compact HTML summary and a separate full retained-evidence report locally. Open **R Reports** from Mission Control, or use **O Report / F Folder** after a guided investigation.

## Read the report

| Area | What to review |
|---|---|
| Header | Source, report ID, generation time, formats, and synthetic-data label where applicable |
| Assessment | Observed priority lead and review guidance |
| Metrics | Processed records, finding occurrences, incident groups, and recognized records |
| Findings | Representative evidence, observed fields, why it matters, and next action |
| Incidents | Groups of related retained signals; grouping does not prove a shared cause |
| Supporting activity | Direct counts for small samples, or distributions and timestamp-supported activity |
| Coverage | Recognition, retained excerpts, collection bounds, missing time information, and source handling |

Report ID identifies an analysis output. Source SHA-256 identifies bytes read during collection, including truncated tails; it does not certify an unchanged or complete live source.

## Activity and missing time

The report timeline uses resolved timestamps normalized to UTC. It displays up to 12 occupied minute buckets, with displayed and retained counts. Gaps are not shown as elapsed-time spacing. Missing timestamps are disclosed. With fewer than two occupied minute buckets, the report explains the limitation instead of inventing a trend. Rarity describes the retained sample, not attack probability.

## Print and save PDF

Use **Print summary / Save PDF** for the short overview. Use **Print complete report / Save PDF** for full retained evidence. Disable browser **Headers and footers** to remove browser-added local paths and dates.

The full report is separate from the summary. Keep both HTML files together so local links work. Preserve original logs separately; neither a summary nor retained evidence is a complete source archive.

## Visual identity

Current main uses a larger transparent approved logo, black body text, light sea-blue accents, a compact metrics strip, and evidence/next-action sections separated by rules. It ends with **MADE BY HR-PRESENTS**. Print styling retains readable supporting text and evidence.

Browser QA covers desktop and a 390-pixel mobile viewport, disclosures, chart visibility without background printing, and PDF pagination. Fixtures include empty, missing-time, many-findings, Windows, and fault-report samples. Page counts vary with evidence; the small built-in demo summary is guarded against an orphan signature page.

## Updating

See [Installation](INSTALL.md#latest-reviewed-report-design-on-main). Published release assets can predate changes merged on main. Update the installed copy and generate a new report; saved HTML/PDF files do not update automatically.

Counts and severities are investigation metrics. Repeated Windows fault-report submissions are not distinct confirmed failures. Validate original event time, dumps, service context, and user impact before escalating.

**MADE BY HR-PRESENTS**
