"""Observed Windows context, independent of message language."""
import re
from .parsers import WINDOWS_EVENT
from .safe_json import loads


def windows_context(evidence):
    original = evidence.split('; latest=', 1)[-1].strip()
    match = WINDOWS_EVENT.match(original)
    if not match:
        return ()
    fields = {}
    _, marker, encoded = original.rpartition(' | AEGIS_EVENT_DATA=')
    if marker:
        try:
            parsed = loads(encoded)
        except (ValueError, TypeError, RecursionError):
            pass
        else:
            if isinstance(parsed, dict):
                fields = parsed
    account = fields.get('TargetUserName') or fields.get('SubjectUserName')
    if match.group('event_id') in {'4728', '4732'}:
        account = fields.get('MemberName') or fields.get('MemberSid')
    if not account:
        found = re.search(r'\baccount=([^\s;|]+)', evidence)
        account = found.group(1) if found else None
    values = {'provider': match.group('provider').strip(), 'event_id': match.group('event_id'),
              'timestamp': match.group('timestamp'), 'host': fields.get('Computer'), 'account': account}
    if match.group('event_id') in {'4728', '4732'}:
        values['group_sid'] = fields.get('TargetSid')
        values['group_name'] = fields.get('TargetUserName')
    return tuple((key, str(value)[:512]) for key, value in values.items() if isinstance(value, (str, int)) and str(value) not in {'', '-'})
