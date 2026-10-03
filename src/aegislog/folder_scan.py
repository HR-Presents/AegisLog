"""Bounded, read-only discovery and batch investigation of local log files."""
from pathlib import Path
import os
import tempfile

from rich.table import Table

from .dashboard import analyze_dashboard
from .navigation import Prompt
from .reporting import write_html_report

LOG_SUFFIXES = {'.log', '.txt', '.jsonl', '.ndjson', '.json', '.csv'}


def discover_logs(root: Path, *, limit=200, max_entries=10000):
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
                            pending.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False) and Path(entry.name).suffix.lower() in LOG_SUFFIXES:
                            with open(entry.path, 'rb') as stream:
                                sample = stream.read(4096)
                            if not sample or b'\x00' in sample:
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


def select_logs(raw, candidates):
    if raw.strip().lower() == 'all':
        return candidates
    indexes = list(dict.fromkeys(int(value.strip()) for value in raw.split(',')))
    if not indexes or any(value < 1 or value > len(candidates) for value in indexes):
        raise ValueError('Select displayed file numbers, separated by commas, or ALL.')
    return [candidates[value - 1] for value in indexes]


def run_folder_scan(console):
    raw = Prompt.ask('Folder path', console=console)
    try:
        root = Path(raw.strip().strip('"')).expanduser().resolve()
        candidates, skipped, capped = discover_logs(root)
    except (ValueError, OSError) as error:
        console.print(str(error), style='yellow')
        return
    console.print(f'SCAN FOLDER / {root}', markup=False)
    console.print('Text log candidates; file extensions do not guarantee supported event formats.')
    table = Table('No.', 'File')
    for index, path in enumerate(candidates, 1):
        table.add_row(str(index), str(path.relative_to(root)))
    console.print(table)
    console.print(f'{len(candidates)} candidates / {skipped} empty, binary or inaccessible entries skipped.')
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
    # Keep sources separate so findings retain their origin and unrelated events are not correlated.
    batch_root = Path('aegislog-reports') / 'folder-scan'
    batch_root.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix='batch-', dir=batch_root))
    completed = 0
    for index, path in enumerate(selected, 1):
        try:
            if path.is_symlink() or not path.is_file():
                raise ValueError('Source is no longer a regular file.')
            data = analyze_dashboard(path)
            report = write_html_report(data, destination / f'{index:03d}')
            console.print(f'{path.name}: {data.lines} events / {len(data.findings)} findings', markup=False)
            console.print(f'Report: {report.resolve()}', markup=False)
            completed += 1
        except (OSError, ValueError) as error:
            console.print(f'Skipped {path}: {error}', markup=False)
    console.print(f'Batch complete: {completed}/{len(selected)} reports. Sources unchanged.')
    Prompt.ask('Enter to return', default='', console=console)
