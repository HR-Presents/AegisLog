"""Optional local count comparisons and identifier-free aggregate sharing."""
import json
import os
import stat
import re
from collections import Counter
from pathlib import Path
from .safe_json import loads
from .sanitize import terminal_safe

SCHEMA = 'aegislog-activity-baseline-1'


def save_activity(data, output, scope):
    payload = dict(schema=SCHEMA, source=data.source, scope=scope, records=data.records,
                   recognized=data.recognized_records, services=data.services, levels=data.levels,
                   severities=data.severities, incidents=len(data.incidents))
    payload['signals'] = dict(Counter(
        f'{item.severity}|{item.category}|{item.title}' for item in getattr(data, 'findings', ())))
    path = Path(output) / 'activity-baseline.json'
    from .output_safety import ensure_distinct_output
    ensure_distinct_output(data.source, path)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return path


def read_activity(path):
    path = Path(path)
    limit = 2_000_000
    if path.is_symlink() or not path.is_file():
        raise ValueError('Choose a regular baseline JSON smaller than 2 MB.')
    with path.open('rb') as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
            raise ValueError('Choose a regular baseline JSON smaller than 2 MB.')
        # The file can grow after fstat; bound the read itself before decoding.
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Choose a regular baseline JSON smaller than 2 MB.')
    obj = loads(raw.decode('utf-8'))
    if not isinstance(obj, dict) or obj.get('schema') != SCHEMA or not isinstance(obj.get('source'), str):
        raise ValueError('Choose an AegisLog activity-baseline.json file.')
    scope = obj.get('scope')
    if not isinstance(scope, str) or len(scope) > 4096 or terminal_safe(scope) != scope:
        raise ValueError('Invalid baseline collection scope.')
    for key in ['records', 'recognized', 'incidents']:
        if type(obj.get(key)) is not int or obj[key] < 0:
            raise ValueError('Invalid baseline counts.')
    if obj['recognized'] > obj['records']:
        raise ValueError('Invalid recognized count.')
    for key in ['services', 'levels', 'severities']:
        values = obj.get(key)
        if not isinstance(values, dict) or len(values) > 5000:
            raise ValueError('Invalid baseline metrics.')
        if any(not isinstance(name, str) or len(name) > 512 or type(count) is not int or count < 0 for name, count in values.items()):
            raise ValueError('Invalid baseline metrics.')
        if any(terminal_safe(name) != name for name in values):
            raise ValueError('Baseline names contain unsupported control characters.')
    return obj


def _collection_settings(scope):
    # Returned counts and limit-hit notices describe the sample, not settings.
    native = re.match(r'^Latest (\d+) accessible events within (\d+) minutes\.', scope)
    if native:
        return ('native', int(native[1]), int(native[2]))
    return ('explicit', scope)


def _require_comparable(before, after):
    if before['source'] != after['source'] or _collection_settings(before['scope']) != _collection_settings(after['scope']):
        raise ValueError('Choose baselines for the same source, time window and event limit.')


def compare_signals(previous, current):
    """New/recurring/not observed labels describe samples, not incident resolution."""
    before, after = read_activity(previous), read_activity(current)
    _require_comparable(before, after)
    if not before['records'] or not after['records']:
        raise ValueError('Both samples need records.')
    for obj in (before, after):
        signals = obj.get('signals')
        if not isinstance(signals, dict) or len(signals) > 5000 or any(
            not isinstance(key, str) or len(key) > 1024 or terminal_safe(key) != key
            or type(count) is not int or count < 0 for key, count in signals.items()
        ):
            raise ValueError('Signal comparison requires newly generated activity baselines.')
    return [dict(signal=key, previous=before['signals'].get(key, 0), current=after['signals'].get(key, 0),
                 status='newly observed' if key not in before['signals'] else 'not observed in current sample'
                 if key not in after['signals'] else 'recurring')
            for key in sorted(set(before['signals']) | set(after['signals']))]


def compare_activity(previous, current):
    before, after = read_activity(previous), read_activity(current)
    _require_comparable(before, after)
    if not before['records'] or not after['records']:
        raise ValueError('Both samples need records for a meaningful comparison.')
    changes = []
    for name in sorted(set(before['services']) | set(after['services'])):
        old, new = before['services'].get(name, 0), after['services'].get(name, 0)
        old_share, new_share = old / before['records'], new / after['records']
        if old != new or old_share != new_share:
            changes.append(dict(provider=name, previous=old, current=new, previous_percent=round(old_share * 100, 2),
                                current_percent=round(new_share * 100, 2), change_percentage_points=round((new_share-old_share)*100, 2)))
    return sorted(changes, key=lambda row: abs(row['change_percentage_points']), reverse=True)


def preview_share(baseline):
    """Omit source, provider names, timestamps and all raw evidence; no reversal map."""
    data = read_activity(baseline)
    allowed = {'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'}
    severity = {key: value for key, value in data['severities'].items() if key in allowed}
    payload = dict(schema='aegislog-shared-summary-1', records=data['records'], recognized=data['recognized'],
                   findings_by_severity=severity, incidents=data['incidents'],
                   provider_counts=[dict(label=f'Provider {i}', records=count)
                                    for i, count in enumerate(sorted(data['services'].values(), reverse=True), 1)],
                   note='Aggregate sharing copy. Source, provider names, accounts, addresses, paths, timestamps and raw evidence are omitted. Counts are investigation metrics, not proof of compromise.')
    return payload


def share_activity(baseline, output):
    payload = preview_share(baseline)
    output = Path(output)
    if output.resolve() == Path(baseline).resolve():
        raise ValueError('Sharing output must differ from the private baseline.')
    with output.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2)
    return output
