"""Bounded, read-only discovery and batch investigation of local log files."""
from .report_paths import default_report_dir
from pathlib import Path
import os
import tempfile

from rich.table import Table

from .dashboard import analyze_dashboard
from .navigation import Prompt
from .reporting import write_html_report

LOG_SUFFIXES = {'.log', '.txt', '.jsonl', '.ndjson', '.json', '.csv'}


def discover_logs(root: Path, *, limit=200, max_entries=10000, include_other=False):
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError('Enter an existing folder path.')
    found, skipped, visited = [], 0, 0
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    visited += 1
                    if visited > max_entries:
                        return sorted(found), skipped, True
                    if entry.is_symlink():
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name not in {".git", ".venv", "node_modules", "aegislog-reports"}:
                                pending.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False) and Path(entry.name).suffix.lower() in LOG_SUFFIXES:
                            with open(entry.path, 'rb') as stream:
                                sample = stream.read(4096)
                            if not sample or b'\x00' in sample:
                                skipped += 1
                                continue
                            if not include_other and not likely_log(Path(entry.path), sample):
                                skipped += 1
                                continue
                            found.append(Path(entry.path))
                            if len(found) >= limit:
                                return sorted(found), skipped, True
                    except OSError:
                        skipped += 1
        except OSError:
            skipped += 1
    return sorted(found), skipped, False


def likely_log(path, sample):
    import csv
    import json
    from .structured_input import normalize_object
    from .parsers import parse_line
    text = sample.decode('utf-8', errors='replace').lstrip('\ufeff')
    if path.suffix.lower() in {'.log', '.jsonl', '.ndjson'}:
        return True
    if path.suffix.lower() == '.csv':
        header = [name.strip().lower() for name in next(csv.reader(text.splitlines()), [])]
        return bool({'message','msg'} & set(header)) or {'id.orig_h','id.resp_h'} <= set(header) or ('src_ip' in header and bool({'dst_ip','dest_ip'} & set(header)))
    if path.suffix.lower() == '.json':
        try:
            obj = json.loads(text)
            records = obj if isinstance(obj, list) else obj.get('events', [obj]) if isinstance(obj, dict) else [obj]
            return any(normalize_object(row)[0] is not None for row in records[:5]) if isinstance(records, list) else False
        except json.JSONDecodeError:
            return any('"'+field+'"' in text for field in ('message','MESSAGE','event_type','id.orig_h'))
    return any(parse_line(line).source != 'generic' for line in text.splitlines()[:10])


def select_logs(raw, candidates):
    if raw.strip().lower() == 'all':
        return candidates
    indexes = list(dict.fromkeys(int(value.strip()) for value in raw.split(',')))
    if not indexes or any(value < 1 or value > len(candidates) for value in indexes):
        raise ValueError('Select displayed file numbers, separated by commas, or ALL.')
    return [candidates[value - 1] for value in indexes]


def _digest(path, poll):
    import hashlib
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            poll()
            digest.update(chunk)
    return digest.hexdigest()


def write_batch(destination, root, rows, stopped=''):
    import json
    from html import escape
    from .reporting import _summary_brand
    completed = [row for row in rows if row['status'] == 'complete']
    total_findings = sum(row.get('findings', 0) for row in completed)
    groups = {}
    for row in completed:
        for group in row.get('groups', []):
            key = (group['severity'], group['title'], group['recommendation'])
            groups[key] = groups.get(key, 0) + group['count']
    recommendations = set()
    group_html = ''
    rank = {'CRITICAL': 5, 'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'INFO': 1}
    for (severity, title, action), count in sorted(groups.items(), key=lambda value: (-rank.get(value[0][0], 0), -value[1]))[:6]:
        group_html += f'<li><strong>{escape(severity)} · {escape(title)} · {count} occurrences</strong>'
        if action not in recommendations:
            group_html += f'<p>{escape(action)}</p>'
            recommendations.add(action)
        group_html += '</li>'
    table = ''
    for row in rows:
        row['detail'] = row.get('error') or ('Identical to ' + row['duplicate_of'] if row.get('duplicate_of') else '')
        report = row.get('report')
        link = f'<a href="{escape(report, quote=True)}">Open report</a>' if report else '—'
        table += '<tr>' + ''.join(f'<td>{escape(str(row.get(key, "—")))}</td>' for key in ('source','status','lines','records','recognized','coverage','findings','detail')) + f'<td>{link}</td></tr>'
    html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AegisLog Folder Investigation</title><style>
    body{{font:17px/1.6 system-ui,sans-serif;background:#f3f7fd;color:#172b4d;margin:0}}main{{max-width:1250px;margin:auto;padding:24px}}section{{background:white;border:1px solid #c4d6ef;padding:22px;border-radius:12px;margin:18px 0}}.summary-brand{{display:flex;gap:12px;align-items:center}}.summary-logo{{width:54px;height:58px}}.summary-wordmark{{font-size:30px;font-weight:bold}}.summary-wordmark span,a{{color:#1258b5}}.summary-tagline,.brand-sub{{font-size:12px}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border-bottom:1px solid #c4d6ef;text-align:left;vertical-align:top;overflow-wrap:anywhere}}.table-wrap{{overflow:auto}}input,button{{font:inherit;padding:10px}}input{{max-width:90%}}@media print{{input,button{{display:none}}body{{background:white}}thead{{display:table-header-group}}}}
    </style><main>{_summary_brand()}<h1>Folder investigation overview</h1><p>{escape(str(root))}</p><section><strong>{len(completed)}/{len(rows)} sources analyzed · {total_findings} findings from unique analyzed sources</strong><p>{escape(stopped or 'Batch completed.')}</p><p>Each source was analyzed independently. Groups summarize similar labels; they are not cross-file incident correlation. Duplicate content may share a report. No findings does not establish safety; review format coverage.</p><button onclick="window.print()">Print overview / Save PDF</button></section><section><h2>Top finding groups</h2><ul>{group_html or '<li>No rules matched in completed sources. Review coverage below.</li>'}</ul></section><section><h2>All selected sources</h2><label>Filter sources <input id="filter" placeholder="Path, status or coverage"></label><div class="table-wrap"><table><thead><tr><th>Relative source</th><th>Status</th><th>Physical lines</th><th>Records</th><th>Recognized</th><th>Coverage</th><th>Findings</th><th>Details</th><th>Report</th></tr></thead><tbody>{table}</tbody></table></div></section></main><script>document.getElementById('filter').addEventListener('input',function(){{const query=this.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(row=>row.hidden=!row.textContent.toLowerCase().includes(query));}});</script></html>'''
    index = destination / 'batch-index.html'
    index.write_text(html, encoding='utf-8')
    (destination / 'batch-manifest.json').write_text(json.dumps(dict(root=str(root), stopped=stopped, sources=rows), indent=2, ensure_ascii=False), encoding='utf-8')
    return index


def run_folder_scan(console):
    from .navigation import KeyboardReader, WorkspaceBack, WorkspaceQuit
    from .report_browser import report_actions
    raw = Prompt.ask('Folder path', console=console)
    broad = Prompt.ask('Include other text/configuration files?', choices=['no', 'yes'], default='no', console=console).lower() == 'yes'
    try:
        root = Path(raw.strip().strip('"')).expanduser().resolve()
        candidates, skipped, capped = discover_logs(root, include_other=broad)
    except (ValueError, OSError) as error:
        console.print(str(error), style='yellow')
        return
    table = Table('No.', 'Relative source path')
    for index, path in enumerate(candidates, 1):
        table.add_row(str(index), str(path.relative_to(root)))
    console.print(table)
    console.print(f'{len(candidates)} candidates / {skipped} excluded, empty, binary or inaccessible entries. Candidates still require format validation.')
    if capped:
        console.print('Discovery limit reached (200 files or 10,000 entries). Choose a smaller folder for the rest.')
    if not candidates:
        return
    while True:
        try:
            selected = select_logs(Prompt.ask('Select numbers (1,2) or ALL', console=console), candidates)
            break
        except ValueError:
            console.print('Enter valid displayed numbers separated by commas, or ALL.', style='yellow')
    skip_duplicates = Prompt.ask('Identical content: skip repeated analysis or analyze every copy?', choices=['skip','analyze'], default='skip', console=console) == 'skip'
    try:
        batch_root = default_report_dir() / 'folder-scan'
        batch_root.mkdir(parents=True, exist_ok=True)
        destination = Path(tempfile.mkdtemp(prefix='batch-', dir=batch_root))
    except OSError as error:
        console.print(f'Could not create reports: {error}', markup=False)
        return
    rows = [dict(source=str(path.relative_to(root)), status='pending') for path in selected]
    fingerprints, stopped, quit_after = {}, '', False
    console.print('Analyzing read-only. B / Esc / Ctrl+C cancels; Q quits. Completed reports are preserved.')
    with KeyboardReader() as keys:
        def poll():
            key = keys.poll()
            if key and key.lower() in {'q', '\x04'}:
                raise WorkspaceQuit()
            if key and key.lower() in {'b', '\x1b', '\x03'}:
                raise WorkspaceBack()
        for number, path in enumerate(selected, 1):
            row = rows[number - 1]
            try:
                poll()
                if path.is_symlink() or not path.is_file():
                    raise ValueError('Source is no longer a regular file.')
                before = path.stat()
                digest = _digest(path, poll)
                hashed = path.stat()
                if (before.st_size, before.st_mtime_ns) != (hashed.st_size, hashed.st_mtime_ns):
                    raise ValueError('Source changed while hashing; retry a stable copy.')
                if skip_duplicates and digest in fingerprints:
                    previous = fingerprints[digest]
                    row.update(status='duplicate', duplicate_of=previous['source'], report=previous['report'], sha256=digest)
                    continue
                console.print(f'[{number}/{len(selected)}] {row["source"]}', markup=False)
                data = analyze_dashboard(path, cancel=poll)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise ValueError('Source changed during the batch; retry a stable copy.')
                report = write_html_report(data, destination / f'{number:03d}')
                from .reporting import _finding_groups
                row.update(status='complete', lines=data.lines, records=data.records, recognized=data.recognized_records, coverage=data.coverage_status,
                           formats=data.format_counts, findings=len(data.findings), report=str(report.relative_to(destination)), sha256=digest,
                           groups=[dict(severity=key[0], title=key[2], recommendation=key[3], count=len(members)) for key, members in _finding_groups(data)])
                fingerprints[digest] = row
                console.print(f'  {data.lines} lines / {data.records} records / {data.recognized_records} recognized / {len(data.findings)} findings', markup=False)
            except (WorkspaceBack, KeyboardInterrupt):
                row['status'] = 'cancelled'
                stopped = 'Cancelled by user. Completed reports preserved; remaining sources are pending.'
                break
            except WorkspaceQuit:
                row['status'], stopped, quit_after = 'cancelled', 'Quit requested; completed reports preserved.', True
                break
            except (OSError, ValueError) as error:
                row.update(status='failed', error=str(error))
                console.print(f'  Skipped: {error}', markup=False)
    try:
        index = write_batch(destination, root, rows, stopped)
    except OSError as error:
        console.print(f'Could not save the batch overview: {error}', markup=False)
        if quit_after:
            raise WorkspaceQuit()
        return
    completed = sum(row['status'] == 'complete' for row in rows)
    duplicates = sum(row['status'] == 'duplicate' for row in rows)
    console.print(f'Batch: {completed} analyzed / {duplicates} duplicate copies / {len(rows)} selected. AegisLog did not modify sources.')
    console.print(f'Batch overview: {index.resolve()}', markup=False)
    if quit_after:
        raise WorkspaceQuit()
    report_actions(console, index)
