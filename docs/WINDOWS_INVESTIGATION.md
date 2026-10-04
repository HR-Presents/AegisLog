# Windows investigation accuracy

Native collection requests the latest bounded set within the selected time window,
then orders that set by event time before analysis. The event count limit still
applies: this is not a guarantee that every event in the time window was collected.

Reports distinguish Windows provider and Event ID from syslog service and process
ID. Security collectors use named XML EventData/UserData fields and numeric levels
to avoid relying on translated message labels. Target identity and initiating
identity are kept separate; group membership events use MemberName/MemberSid.
Legacy text inputs retain their existing message parsing fallback. Missing
structured target fields are left unresolved rather than inferred from the actor.

Windows operational incidents are scoped by provider. One isolated structured
operational error remains a finding; repeated errors within the same provider
may form an incident group. Grouping does not establish a shared cause and does
not currently apply a time-window constraint to operational incidents.

Static file investigations preserve the strongest observed timestamped
authentication window per source IP across the processed input, instead of losing
earlier bursts when newer events expire the rolling state. Peaks have a capacity
limit and dropped results are counted. This does not retain every separate burst
from the same IP, or separate accounts behind one IP. Windows snapshots are ordered
chronologically; arbitrary file input older than the active window can still be
ignored by the streaming correlation state. Missing timestamps retain the bounded
event-order fallback. Rolling/live consumers keep the current-window behavior.

Rarity remains frequency within retained evidence, not attack probability. Source
logs remain read-only. Reports contain retained excerpts, not a full forensic copy.
