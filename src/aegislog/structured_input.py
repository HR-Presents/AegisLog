"""Bounded schema-aware records; unknown structures remain explicitly unrecognized."""
from .safe_json import loads as safe_json_loads
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import csv
import json

from .ingestion import iter_bounded_lines
from .parsers import parse_line, PRIORITY_LEVELS


@dataclass
class Coverage:
    lines: int = 0
    records: int = 0
    recognized: int = 0
    invalid: int = 0
    truncated: int = 0
    metadata: int = 0
    formats: Counter = field(default_factory=Counter)

    @property
    def status(self):
        if not self.records:
            return 'No analyzable records'
        if not self.recognized:
            return 'Unrecognized format / generic fallback only'
        if self.recognized < self.records or self.invalid or self.truncated:
            return 'Partial format coverage'
        return 'Recognized record formats; detection scope remains limited'


def _stamp(value):
    if isinstance(value, (float, int)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
        try:
            return datetime.fromtimestamp(float(value), timezone.utc).isoformat().replace('+00:00', 'Z')
        except (ValueError, OverflowError, OSError):
            return ''
    return str(value or '')[:80]


def normalize_object(obj):
    """Return canonical text and schema name without interpreting arbitrary business data."""
    if not isinstance(obj, dict):
        return None, 'unknown-json'
    if obj.get('event_type') and ('src_ip' in obj or 'dest_ip' in obj or 'alert' in obj):
        kind = str(obj['event_type'])
        alert = obj.get('alert')
        if kind == 'alert' and isinstance(alert, dict) and alert.get('signature'):
            try:
                priority = int(alert.get('severity', 3))
            except (TypeError, ValueError):
                priority = 3
            level = 'HIGH' if priority == 1 else 'MEDIUM' if priority == 2 else 'LOW'
            message = f'SURICATA ALERT priority={level} signature={alert["signature"]} signature_id={alert.get("signature_id", "unknown")} category={alert.get("category", "unknown")} action={alert.get("action", "unknown")}'
        else:
            message = f'Suricata {kind} telemetry'
        return f'{_stamp(obj.get("timestamp"))} suricata: {message} src_ip={obj.get("src_ip", "unknown")} dest_ip={obj.get("dest_ip", "unknown")}', 'suricata-eve'
    if 'id.orig_h' in obj and 'id.resp_h' in obj and 'ts' in obj:
        message = ' '.join(f'{key}={obj[key]}' for key in ('uid','id.orig_h','id.orig_p','id.resp_h','id.resp_p','proto','service','conn_state','duration','orig_bytes','resp_bytes') if key in obj)
        return f'{_stamp(obj["ts"])} zeek: Connection telemetry {message}', 'zeek-conn'
    if ('src_ip' in obj and ('dest_ip' in obj or 'dst_ip' in obj)) and any(key in obj for key in ('timestamp', 'ts', 'time')):
        message = ' '.join(f'{key}={obj[key]}' for key in ('src_ip','dest_ip','dst_ip','src_port','dest_port','dst_port','proto','protocol','action') if key in obj)
        return f'{_stamp(obj.get("timestamp") or obj.get("ts") or obj.get("time"))} network: Flow observation {message}', 'network-flow'
    message = obj.get('MESSAGE') or obj.get('message') or obj.get('msg')
    if isinstance(message, (str, int, float)):
        stamp = _stamp(obj.get('timestamp') or obj.get('time') or obj.get('ts'))
        service_value = obj.get('service') or obj.get('SYSLOG_IDENTIFIER') or obj.get('_SYSTEMD_UNIT') or 'application'
        service = str(service_value)[:128] if isinstance(service_value, (str, int, float)) else 'unknown'
        level = str(PRIORITY_LEVELS.get(str(obj.get('PRIORITY'))) or obj.get('level') or '').upper()[:32]
        return f'{stamp} {service}: {level} {message}', 'json-message'
    return None, 'unknown-json'


def iter_records(path: Path, coverage: Coverage, max_line_bytes=1_000_000, cancel=None):
    def lines():
        for item in iter_bounded_lines(path, max_line_bytes):
            if cancel:
                cancel()
            coverage.lines += 1
            coverage.truncated += int(item.truncated)
            yield item.text
    def emit(raw, text, kind, known):
        if cancel:
            cancel()
        if len(raw.encode("utf-8")) > max_line_bytes or len(text.encode("utf-8")) > max_line_bytes:
            raw = raw.encode("utf-8")[:max_line_bytes].decode("utf-8", errors="replace") + " [TRUNCATED]"
            text = text.encode("utf-8")[:max_line_bytes].decode("utf-8", errors="replace") + " [TRUNCATED]"
            coverage.truncated += 1
        coverage.records += 1
        coverage.recognized += int(known)
        coverage.formats[kind] += 1
        return raw, text, kind, known
    suffix = path.suffix.lower()
    if suffix == '.csv':
        previous_limit = csv.field_size_limit()
        csv.field_size_limit(max(previous_limit, max_line_bytes))
        line_source = iter(lines())
        reader = csv.reader(line_source, strict=True)
        try:
            try:
                header = next(reader, [])
            except csv.Error:
                coverage.invalid += 1
                for _ in line_source:
                    pass
                return
            coverage.metadata += 1 if header else 0
            header = [name.strip().lstrip('\ufeff').lower() for name in header]
            while True:
                try:
                    row = next(reader)
                except StopIteration:
                    break
                except csv.Error:
                    coverage.invalid += 1
                    yield emit('[INVALID CSV RECORD]', '[INVALID CSV RECORD]', 'invalid-csv', False)
                    continue
                if not row or not any(row):
                    continue
                raw = json.dumps(dict(zip(header, row)) if len(row) == len(header) else row, ensure_ascii=False)
                if len(row) != len(header) or len(set(header)) != len(header):
                    coverage.invalid += 1
                    yield emit(raw, raw, 'invalid-csv', False)
                    continue
                text, kind = normalize_object(dict(zip(header, row)))
                yield emit(raw, text or raw, 'csv-' + kind, text is not None)
        finally:
            csv.field_size_limit(previous_limit)
        return
    # Whole JSON containers are supported up to 8 MB. Larger containers fall back visibly.
    if suffix == '.json' and path.stat().st_size <= 8_000_000:
        raw_lines = list(lines())
        raw = '\n'.join(raw_lines)
        try:
            obj = safe_json_loads(raw)
        except (ValueError, RecursionError):
            obj = None
        if obj is not None:
            records = obj if isinstance(obj, list) else obj.get('events') if isinstance(obj, dict) and isinstance(obj.get('events'), list) else [obj]
            for record in records:
                text, kind = normalize_object(record)
                original = json.dumps(record, ensure_ascii=False)
                yield emit(original, text or original, kind, text is not None)
            return
        # Count physical lines once even when the JSON container is malformed/JSONL.
        source = iter(raw_lines)
    else:
        source = lines()
    fields, separator, zeek_header = None, '\t', False
    for raw in source:
        stripped = raw.strip().lstrip('\ufeff')
        if not stripped:
            continue
        if stripped.startswith('#separator '):
            zeek_header = True
            encoded = stripped.split(' ', 1)[1]
            separator = '\t' if encoded == r'\x09' else ' ' if encoded == r'\x20' else '\t'
            coverage.metadata += 1
            continue
        if stripped.startswith('#fields'):
            fields = stripped[len('#fields'):].lstrip().split(separator)
            coverage.metadata += 1
            continue
        if (fields is not None or zeek_header) and stripped.startswith('#'):
            coverage.metadata += 1
            continue
        if fields is not None:
            values = raw.split(separator)
            text, kind = normalize_object(dict(zip(fields, values))) if len(fields) == len(values) else (None, 'invalid-zeek')
            if len(fields) != len(values):
                coverage.invalid += 1
            yield emit(raw, text or raw, kind, text is not None)
            continue
        if stripped.startswith(('{', '[')):
            try:
                obj = safe_json_loads(stripped)
                text, kind = normalize_object(obj)
            except (ValueError, RecursionError):
                text, kind = None, 'invalid-json'
                coverage.invalid += 1
            yield emit(raw, text or raw, kind, text is not None)
            continue
        event = parse_line(raw)
        yield emit(raw, raw, event.source, event.source != 'generic')
