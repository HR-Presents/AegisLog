"""Search bounded local case metadata without loading raw evidence or HTML."""
import json
from datetime import datetime, timezone
from pathlib import Path

from .safe_json import loads
from .sanitize import terminal_safe, redact_sensitive

SCHEMA = 'aegislog-case-1'


def save_case(data, output, report, scope):
    path = Path(output) / (Path(report).stem + '-case.json')
    from .output_safety import ensure_distinct_output
    ensure_distinct_output(data.source, path)
    payload = dict(schema=SCHEMA, source=redact_sensitive(data.source),
                   generated=datetime.now(timezone.utc).isoformat(), report=Path(report).name,
                   records=data.records, severities=data.severities, scope=scope,
                   titles=sorted({redact_sensitive(f.title) for f in data.findings})[:500])
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return path


def search_cases(roots, *, query='', severity='', since='', limit=100):
    if not 1 <= limit <= 500:
        raise ValueError('Choose a limit between 1 and 500.')
    severity = severity.upper()
    if severity and severity not in {'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'}:
        raise ValueError('Unknown severity.')
    if since:
        datetime.strptime(since, '%Y-%m-%d')
    rows, seen = [], set()
    # Restrict depth to known report workflows; never recursively read arbitrary logs.
    for root in roots:
        root = Path(root)
        for pattern in ('*-case.json', '*/*-case.json', '*/*/*-case.json', '*/*/*/*-case.json'):
            for path in root.glob(pattern):
                if len(seen) >= 10000:
                    break
                if path in seen:
                    continue
                seen.add(path)
                try:
                    if path.is_symlink() or path.stat().st_size > 200000:
                        continue
                    row = loads(path.read_text(encoding='utf-8'))
                    if not isinstance(row, dict) or row.get('schema') != SCHEMA:
                        continue
                    if not all(isinstance(row.get(key), str) for key in ('source', 'generated', 'report')):
                        continue
                    datetime.fromisoformat(row['generated'])
                    if Path(row['report']).name != row['report'] or not row['report'].endswith('.html'):
                        continue
                    report = path.parent / row['report']
                    if report.is_symlink() or not report.is_file():
                        continue
                    if not isinstance(row.get('severities'), dict) or not isinstance(row.get('titles'), list):
                        continue
                    if any(not isinstance(title, str) for title in row['titles']):
                        continue
                    if severity and not row['severities'].get(severity):
                        continue
                    if since and row['generated'][:10] < since:
                        continue
                    if query.casefold() not in (row['source'] + ' ' + ' '.join(row['titles'])).casefold():
                        continue
                    rows.append({**row, 'source': terminal_safe(row['source']), 'path': str(report.resolve())})
                except (OSError, ValueError, TypeError, RecursionError):
                    continue
    return sorted(rows, key=lambda row: row['generated'], reverse=True)[:limit]
