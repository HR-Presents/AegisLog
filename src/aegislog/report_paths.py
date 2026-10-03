"""Writable default report storage with a user-folder fallback."""
from pathlib import Path
import os
import tempfile


def report_search_roots():
    local = Path.cwd() / 'aegislog-reports'
    user = (Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))) / 'AegisLog' / 'reports'
            if os.name == 'nt' else Path.home() / '.aegislog' / 'reports')
    return list(dict.fromkeys([local, user]))


def default_report_dir():
    for root in report_search_roots():
        try:
            root.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=root):
                pass
            return root
        except OSError:
            continue
    raise OSError('Cannot write reports in the current or user report folder. Start AegisLog from a writable folder.')
