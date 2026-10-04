"""Guided local investigations for the terminal."""
from .report_paths import default_report_dir
from dataclasses import asdict, replace
from pathlib import Path
import json
import os
import platform
import tempfile
from html import escape
from collections import Counter

from .dashboard import analyze_dashboard
from .native_collectors import CollectorError, collect
from .reporting import _recommendation, write_html_report
from .sanitize import redact_sensitive

SOURCE_HELP = {
    'System': 'Service, driver, startup and operating-system events.',
    'Application': 'Events recorded by applications and application services.',
    'Security': 'Auditing of accounts, authentication and security changes; access may require elevation.',
    'journald': 'Linux systemd journal events visible to your account.',
}


def discover_sources():
    system = platform.system()
    choices = [('windows', channel) for channel in ('System', 'Application', 'Security')] if system == 'Windows' else [('journald', '')] if system == 'Linux' else []
    rows = []
    for source, channel in choices:
        label = channel or source
        try:
            lines = collect(source, channel=channel or 'System', limit=1)
            status, detail = 'readable', 'Read-only probe succeeded; no events returned.' if not lines else 'Read-only probe succeeded.'
        except (CollectorError, OSError) as error:
            status, detail = 'unavailable', redact_sensitive(str(error))[:500]
        rows.append(dict(source=source, channel=channel, label=label, description=SOURCE_HELP[label], status=status, detail=detail))
    known = ([('Windows servicing', Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'Logs' / 'DISM' / 'dism.log'),
              ('Windows component servicing', Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'Logs' / 'CBS' / 'CBS.log')]
             if system == 'Windows' else [('Linux authentication', Path('/var/log/auth.log')), ('Linux system log', Path('/var/log/syslog')),
                                         ('Nginx errors', Path('/var/log/nginx/error.log')), ('Apache errors', Path('/var/log/apache2/error.log'))]
             if system == 'Linux' else [])
    for label, path in known:
        if not path.exists() or path.is_symlink():
            continue
        try:
            with path.open('rb') as stream:
                sample = stream.read(4096)
            status = 'unavailable' if b'\x00' in sample else 'readable'
            detail = 'Export UTF-8 text first.' if status == 'unavailable' else 'Known local log path is readable.'
        except OSError as error:
            status, detail = 'unavailable', str(error)[:500]
        rows.append(dict(source='file', channel='', path=str(path), label=label, description='Known application/system log file; file analysis uses the full file rather than the native time window.', status=status, detail=detail))
    return rows


def explain_finding(finding):
    operational = finding.category in {'error', 'service'}
    if finding.category == 'diagnostic':
        return dict(classification='Diagnostic record', reason=f'Local rules identified: {finding.title}.',
                    impact='Troubleshooting information; verify original event time and user impact.',
                    alternative='Expected diagnostic reporting may produce this record.',
                    next_step=_recommendation(finding), confidence='Record classification; no measured probability of compromise.')
    return dict(
        classification='Operational issue' if operational else 'Security investigation lead',
        reason=f'Local detection rules matched evidence for: {finding.title}.',
        impact='The event may indicate degraded service or application reliability.' if operational else 'The activity may affect account, service or data security; validate the surrounding context.',
        alternative='A transient failure, dependency issue or expected maintenance can produce this event.' if operational else 'Authorized administration, testing or ordinary user activity may produce similar signals.',
        next_step=_recommendation(finding),
        confidence='Rule match; no measured probability of compromise.',
    )


def investigate_path(path, output, *, cancel=None, progress=None):
    path = Path(path).expanduser()
    if str(path).startswith(('\\\\', '//')):
        raise ValueError('Choose a local file; network shares are not part of this workflow.')
    if not path.is_file() or path.is_symlink():
        raise ValueError('Choose an existing regular local log file.')
    if path.stat().st_size > 100_000_000:
        raise ValueError('This guided workflow accepts files up to 100 MB. Use a smaller export.')
    with path.open('rb') as stream:
        if b'\x00' in stream.read(4096):
            raise ValueError('Binary or UTF-16 input detected. Export a UTF-8 text log first.')
    return finish_investigation(analyze_dashboard(path, cancel=cancel, progress=progress), output)


def check_computer(source, channel, minutes, limit, output):
    if source not in {'windows', 'journald'}:
        raise ValueError('Choose a discovered Windows or journald source.')
    if minutes not in {60, 1440, 10080} or not 1 <= limit <= 2000:
        raise ValueError('Choose 1 hour, 24 hours or 7 days and 1–2000 events.')
    lines = collect(source, channel=channel or 'System', limit=limit, since_minutes=minutes)
    limit_note = ('Count limit reached; earlier events may be excluded.' if len(lines) >= limit
                  else 'Collector returned fewer events than the limit; this does not establish complete host coverage.')
    descriptor, name = tempfile.mkstemp(prefix='aegislog-check-', suffix='.log')
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.writelines(lines)
        data = replace(analyze_dashboard(Path(name)), source=f'{source}-{channel or "journal"}-{minutes}min.log')
        return finish_investigation(data, output, scope=f'Latest {limit} accessible events within {minutes} minutes. Returned {len(lines)} events. {limit_note} A count limit can exclude earlier events in this window.')
    finally:
        Path(name).unlink(missing_ok=True)


def finish_investigation(data, output, scope='Selected file; activity charts use bounded retained evidence.'):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    from .output_safety import ensure_distinct_output
    ensure_distinct_output(data.source, output / 'evidence.json')
    report = write_html_report(data, output)
    formats = Counter(event.source for event in data.events)
    context = f'<p class="caveat">Collection scope: {escape(scope)} Retained formats: {escape(str(dict(formats)))}. Generic parsing is fallback coverage.</p>'
    for html_path in [report, report.with_name(report.stem + '-appendix.html')]:
        html = html_path.read_text(encoding='utf-8')
        html = html.replace('<div class="scope">', '<div class="scope">' + context, 1) if '<div class="scope">' in html else html.replace('<div class="footer">', context + '<div class="footer">', 1)
        html_path.write_text(html, encoding='utf-8')
    payload = dict(source=data.source, events=data.records, lines_processed=data.lines, recognized_records=data.recognized_records, findings=[dict(**asdict(item), explanation=explain_finding(item)) for item in data.findings],
                   incidents=[asdict(item) for item in data.incidents], severities=data.severities,
                   coverage=dict(scope=scope, status=data.coverage_status, format_counts=data.format_counts, recognized=data.recognized_records, invalid_records=data.invalid_records, note=data.coverage_note, retention=data.retention_note, retained_formats=dict(formats),
                                 generic_retained=sum(event.source == 'generic' for event in data.events),
                                 caveat='Format counts cover retained events. Generic parsing is fallback coverage, not proof that every field was understood. No findings does not establish a clean system.'),
                   summary=str(report.resolve()), evidence_report=str(report.with_name(report.stem + '-appendix.html').resolve()))
    from .triage import finding_groups, windows_session_context
    payload['triage_groups'] = finding_groups(data.findings, data.timestamp_year_hint)
    payload['windows_session_context'] = windows_session_context(data.raw_lines)
    # Export is credential-redacted; filenames/usernames/IPs can still identify people or hosts.
    export = output / 'evidence.json'
    export.write_text(redact_sensitive(json.dumps(payload, ensure_ascii=False, default=str)), encoding='utf-8')
    payload['export'] = str(export.resolve())
    from .activity_review import save_activity
    payload['activity_baseline'] = str(save_activity(data, output, scope).resolve())
    from .case_catalog import save_case
    save_case(data, output, report, scope)
    return payload


def guided_check(console):
    from .navigation import Prompt
    rows = discover_sources()
    for number, row in enumerate(rows, 1):
        console.print(f'{number}. {row["label"]} / {row["status"]}: {row["description"]}\n{row["detail"]}', markup=False)
    ready = {str(i): row for i, row in enumerate(rows, 1) if row['status'] == 'readable'}
    if not ready:
        console.print('No native source is readable here. Use 01 Analyze Log or F Scan Folder.')
        return
    row = ready[Prompt.ask('Source number', choices=list(ready), console=console)]
    minutes = int(Prompt.ask('Time window in minutes', choices=['60', '1440', '10080'], default='1440', console=console)) if row['source'] != 'file' else None
    limit = int(Prompt.ask('Maximum events', choices=['100', '300', '1000', '2000'], default='300', console=console)) if row['source'] != 'file' else None
    try:
        root = default_report_dir() / 'computer-checks'
        root.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix='check-', dir=root))
        result = investigate_path(row['path'], output) if row['source'] == 'file' else check_computer(row['source'], row['channel'], minutes, limit, output)
    except (CollectorError, OSError, ValueError) as error:
        console.print(str(error), markup=False)
        return
    console.print(f'{result["lines_processed"]} physical lines / {result["events"]} records / {result["recognized_records"]} recognized / {len(result["findings"])} findings', markup=False)
    console.print(result['coverage']['scope'])
    console.print(result['coverage']['retention'])
    console.print(f'Summary: {result["summary"]}', markup=False)
    console.print(result['coverage']['note'])
    groups = result.get('triage_groups', [])
    actions = set()
    for group in groups[:3]:
        explanation = group['explanation']
        console.print(f'{group["severity"]}: {group["title"]} / {group["count"]} occurrence(s) / {explanation["classification"]}', markup=False)
        console.print(f'First: {group["first"] or "unresolved"} / Last: {group["last"] or "unresolved"}', markup=False)
        action = explanation['next_step']
        if action not in actions:
            console.print(f'Why: {explanation["impact"]}\nAlternative: {explanation["alternative"]}\nNext: {action}', markup=False)
            actions.add(action)
    console.print(f'Showing {min(3, len(groups))}/{len(groups)} finding groups; all retained findings remain in the reports.')
    if result.get('windows_session_context'):
        console.print(f'{len(result["windows_session_context"])} retained Windows session context links. Use review <log> for details; links do not establish compromise.')
    from .report_browser import report_actions
    report_actions(console, Path(result['summary']))
