"""Presentation groups and bounded context links, never new threat conclusions."""
from collections import defaultdict
from bisect import bisect_left, bisect_right
from datetime import timedelta
import re
from .engine import _parse_timestamp
from .parsers import parse_line
from .product import explain_finding
from .windows_security import parse_windows_security_line

RANK = {'CRITICAL': 5, 'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'INFO': 1}


def finding_groups(findings, year_hint=None):
    groups = defaultdict(list)
    ordered = sorted(findings, key=lambda item: (-RANK.get(item.severity, 0), item.category, item.title))
    for index, finding in enumerate(ordered, 1):
        event = parse_line(finding.evidence)
        # Do not merge distinct providers, accounts or source addresses just because
        # their detector titles match. Evidence references retain original order.
        context = dict(finding.context)
        key = (finding.severity, finding.category, finding.title, finding.recommendation,
               context.get('provider', event.service), context.get('host'), context.get('account'), context.get('source_ip'))
        groups[key].append((index, finding))
    result = []
    for key, members in groups.items():
        times = [stamp for _, finding in members if (stamp := _parse_timestamp(finding.evidence, year_hint))]
        result.append(dict(severity=key[0], category=key[1], title=key[2], provider=key[4],
                           count=len(members), references=[f'F-{index:03d}' for index, _ in members],
                           first=min(times).isoformat() if times else None,
                           last=max(times).isoformat() if times else None,
                           unresolved_timestamps=len(members)-len(times),
                           explanation=explain_finding(members[0][1])))
    return sorted(result, key=lambda row: (-RANK.get(row['severity'], 0), -row['count'], row['title']))


def windows_session_context(lines, *, limit=100):
    """Link same-host, same-ID events within five minutes of a successful logon.

    Require explicit host/session fields; account names alone are insufficient.
    Only retained lines participate; reused IDs outside the window do not link.
    """
    if not 1 <= limit <= 100:
        raise ValueError('Context limit must be between 1 and 100.')
    sessions = defaultdict(list)
    for index, line in enumerate(lines, 1):
        event = parse_windows_security_line(line)
        if event and event.event_id in {4624, 4672, 4688} and event.host and event.logon_id:
            stamp = _parse_timestamp(event.timestamp)
            explicit_zone = re.search(r'(?:Z|[+-]\d{2}:?\d{2})$', event.timestamp)
            if stamp and explicit_zone and event.logon_id.casefold() not in {'0x0', '0', '-'}:
                sessions[(event.host.casefold(), event.logon_id.casefold())].append((stamp, index, event.event_id))
    links = []
    for (host, session), events in sessions.items():
        events.sort()
        related_events = [(when, number, kind) for when, number, kind in events if kind != 4624]
        related_times = [when for when, _, _ in related_events]
        for stamp, index, kind in events:
            if kind != 4624:
                continue
            start = bisect_left(related_times, stamp)
            end = bisect_right(related_times, stamp + timedelta(minutes=5))
            related = [(number, event_id) for _, number, event_id in related_events[start:min(end, start+1000)]]
            if related:
                links.append(dict(host=host, logon_id=session, logon_record=index,
                                  related_records=[number for number, _ in related],
                                  event_ids=sorted({kind for _, kind in related}),
                                  omitted_context_records=max(0, end-start-1000),
                                  basis='Explicit host and logon ID; within five minutes of logon. Context link, not proof of compromise.'))
                if len(links) == limit:
                    return links
    return links
