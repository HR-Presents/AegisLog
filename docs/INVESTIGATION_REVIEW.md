# Reviewing collections and sharing results

Check Computer (C) offers 100, 300, 1000 or 2000 events within the chosen time
window. The scope states the requested limit, returned count, and whether the
limit was reached. Fewer events do not establish complete host coverage.

Summary service charts preserve complete provider names. Each rarity signal shows
its occurrence count and retained sample size beside its score. A high rarity
score describes frequency in that sample, not attack probability or severity.

Windows incident groups use provider, Event ID, observed host/account, and a
maximum five-minute span. Missing host/account remain unresolved; they are not
inferred. Events without a resolved timezone are not treated as a timed sequence.
Legacy non-Windows grouping keeps its prior fallback behavior without this time
constraint. Grouping never proves a shared cause.

Check Computer saves activity-baseline.json beside its reports. This file is a
private local metrics snapshot, not a copy of the log. V in the result menu compares
it with a previous snapshot for the same source/time-window label. Counts and
percentages of the sample are shown; these are not time-normalized event rates.
Different event limits, available evidence, or host changes can affect comparisons.
No change does not establish safety. Comparison does not modify detection severity.

S creates share-summary.json with aggregate counts and anonymous provider labels.
It omits source/provider names, paths, timestamps, accounts, addresses, and raw
evidence; it does not include a reversal map. It refuses to overwrite existing
files. Only this sharing copy has these omissions: activity-baseline.json, full
reports, and evidence.json remain private evidence and may contain identifiers.
