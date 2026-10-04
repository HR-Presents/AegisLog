"""Bounded, read-only discovery and batch investigation of local log files."""
from .safe_json import loads as safe_json_loads
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
            obj = safe_json_loads(text)
            records = obj if isinstance(obj, list) else obj.get('events', [obj]) if isinstance(obj, dict) else [obj]
            return any(normalize_object(row)[0] is not None for row in records[:5]) if isinstance(records, list) else False
        except (ValueError, RecursionError):
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


def write_batch(destination, root, rows, stopped='', *, scan_mode='Likely logs only'):
    import json
    from collections import Counter
    from html import escape
    from .reporting import _summary_brand
    completed = [row for row in rows if row['status'] == 'complete']
    status = Counter(row['status'] for row in rows)
    total_findings = sum(row.get('findings', 0) for row in completed)
    groups = {}
    categories = Counter()
    def coverage_label(row):
        if row['status'] == 'duplicate':
            return 'Shared report'
        if row['status'] != 'complete':
            return 'Not analyzed'
        recognized, records = row.get('recognized', 0), row.get('records', 0)
        return 'Recognized' if records and recognized == records else 'Partial' if recognized else 'Generic only'
    coverage = Counter(coverage_label(row) for row in completed)
    for row in completed:
        for group in row.get('groups', []):
            key = (group['severity'], group['title'], group['recommendation'])
            groups[key] = groups.get(key, 0) + group['count']
            category = group.get('category', 'unspecified')
            categories['Operational' if category in {'error', 'service'} else 'Security / other leads'] += group['count']
    rank = {'CRITICAL': 5, 'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'INFO': 1}
    group_html = ''
    for (severity, title, action), count in sorted(groups.items(), key=lambda value: (-rank.get(value[0][0], 0), -value[1]))[:6]:
        word = 'occurrence' if count == 1 else 'occurrences'
        group_html += f'<li><strong>{escape(severity)} · {escape(title)} · {count} {word}</strong><p>{escape(action)}</p></li>'
    table, appendix = '', ''
    for row in rows:
        row['detail'] = row.get('error') or ('Identical to ' + row['duplicate_of'] if row.get('duplicate_of') else '')
        report = row.get('report')
        link = f'<a href="{escape(report, quote=True)}">Open report</a>' if report else '—'
        table += '<tr>' + ''.join(f'<td>{escape(str(row.get(key, "—")))}</td>' for key in ('source','status','lines','records','recognized','coverage','findings','detail')) + f'<td>{link}</td></tr>'
        detail = f'<small>{escape(row["detail"])}</small>' if row['detail'] else ''
        appendix += f'<tr><td>{escape(row["source"])}{detail}</td><td>{escape(row["status"])}</td><td>{coverage_label(row)}</td><td>{row.get("recognized", "—")} / {row.get("records", "—")}</td><td>{row.get("findings", "—")}</td></tr>'
    leaders = ''.join(f'<li>{escape(row["source"])} — {row.get("findings", 0)} findings ({coverage_label(row)})</li>' for row in sorted(completed, key=lambda row: -row.get('findings', 0))[:5] if row.get('findings'))
    counts = f'{len(completed)} unique sources analyzed + {status["duplicate"]} duplicate copies; {status["failed"]} failed, {status["cancelled"]} cancelled, {status["pending"]} pending / {len(rows)} selected'
    html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AegisLog Folder Investigation</title><style>
    body{{font:17px/1.6 system-ui,sans-serif;background:#f3f7fd;color:#172b4d;margin:0}}main{{max-width:1250px;margin:auto;padding:24px}}section{{background:white;border:1px solid #c4d6ef;padding:22px;border-radius:12px;margin:18px 0}}.summary-brand{{display:flex;gap:12px;align-items:center}}.summary-logo{{width:54px;height:58px}}.summary-wordmark{{font-size:30px;font-weight:bold}}.summary-wordmark span,a{{color:#1258b5}}.summary-tagline,.brand-sub{{font-size:12px}}table{{border-collapse:collapse;width:100%;min-width:1100px}}th,td{{padding:10px;border-bottom:1px solid #c4d6ef;text-align:left;vertical-align:top}}td:first-child{{overflow-wrap:anywhere;min-width:240px}}.table-wrap{{overflow:auto}}input,button{{font:inherit;padding:10px}}input{{max-width:90%}}.print-only{{display:none}}small{{display:block;color:#405675}}
    @page{{size:A4;margin:14mm}}@media print{{body{{font-size:10pt;line-height:1.35;background:white}}main{{padding:0;max-width:none}}section{{border:0;padding:0;margin:12pt 0;border-radius:0}}h1{{font-size:20pt}}h2{{font-size:14pt}}.screen-only{{display:none!important}}.print-only{{display:block}}table{{min-width:0;table-layout:fixed}}th,td{{padding:5pt;overflow-wrap:normal}}td:first-child{{min-width:0;overflow-wrap:anywhere}}th:nth-child(1){{width:44%}}th:nth-child(2){{width:14%}}th:nth-child(3){{width:16%}}th:nth-child(4){{width:16%}}th:nth-child(5){{width:10%}}thead{{display:table-header-group}}tr{{break-inside:avoid}}h2{{break-after:avoid}}small{{font-size:8pt}}}}
    </style><main>{_summary_brand()}<h1>Folder investigation overview</h1><p>{escape(str(root))}</p><section><strong>{counts}</strong><p>{escape(stopped or 'Batch completed.')}</p><p>Scan mode: {escape(scan_mode)}. Sources are analyzed independently; similar labels are not cross-file incident correlation.</p><p>{total_findings} rule matches from unique analyzed sources: {categories['Operational']} operational issues; {categories['Security / other leads']} security / other leads. These are not confirmed attacks.</p><p>Coverage: {coverage['Recognized']} recognized, {coverage['Partial']} partial, {coverage['Generic only']} generic-only sources. Generic rules can match unrecognized text. Zero findings does not establish safety.</p><div class="screen-only"><button onclick="window.print()">Print overview / Save PDF</button><p>For sharing, disable browser headers and footers in the print dialog.</p></div></section><section><h2>Top finding groups</h2><ul>{group_html or '<li>No rules matched. Review coverage.</li>'}</ul><h2>Sources with most findings</h2><ul>{leaders or '<li>No retained findings.</li>'}</ul></section><section class="screen-only"><h2>All selected sources</h2><label>Filter sources <input id="filter" placeholder="Path, status or coverage"></label><div class="table-wrap"><table><thead><tr><th>Relative source</th><th>Status</th><th>Physical lines</th><th>Records</th><th>Recognized</th><th>Coverage</th><th>Findings</th><th>Details</th><th>Report</th></tr></thead><tbody>{table}</tbody></table></div></section><section class="print-only"><h2>Source appendix</h2><p>Recognized / records describes format coverage. Duplicate rows refer to their shared report. Individual HTML reports remain available in the original folder.</p><table><thead><tr><th>Source</th><th>Status</th><th>Coverage</th><th>Recognized / records</th><th>Findings</th></tr></thead><tbody>{appendix}</tbody></table></section></main><script>document.getElementById('filter').addEventListener('input',function(){{const query=this.value.toLowerCase();document.querySelectorAll('.screen-only tbody tr').forEach(row=>row.hidden=!row.textContent.toLowerCase().includes(query));}});</script></html>'''
    index = destination / 'batch-index.html'
    index.write_text(html, encoding='utf-8')
    (destination / 'batch-manifest.json').write_text(json.dumps(dict(root=str(root), stopped=stopped, scan_mode=scan_mode, sources=rows), indent=2, ensure_ascii=False), encoding='utf-8')
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
                last_progress = [0.0]
                def progress(lines, records):
                    import time
                    now = time.monotonic()
                    if now - last_progress[0] >= 1:
                        console.print(f'  Progress: {lines:,} physical lines / {records:,} records processed', markup=False)
                        last_progress[0] = now
                data = analyze_dashboard(path, cancel=poll, progress=progress)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise ValueError('Source changed during the batch; retry a stable copy.')
                report = write_html_report(data, destination / f'{number:03d}')
                from .case_catalog import save_case
                save_case(data, report.parent, report, 'Folder scan; independent source analysis.')
                from .reporting import _finding_groups
                row.update(status='complete', lines=data.lines, records=data.records, recognized=data.recognized_records, coverage=data.coverage_status,
                           formats=data.format_counts, findings=len(data.findings), report=str(report.relative_to(destination)), sha256=digest,
                           groups=[dict(severity=key[0], category=key[1], title=key[2], recommendation=key[3], count=len(members)) for key, members in _finding_groups(data)])
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
        index = write_batch(destination, root, rows, stopped, scan_mode="Other text/configuration included" if broad else "Likely logs only")
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
