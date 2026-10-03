"""Local report navigation and a plain-language product guide."""
from pathlib import Path

from rich.console import Group
from rich.text import Text

from .navigation import Prompt
from .theme import ACCENT, MUTED, NEUTRAL

INTRODUCTION = (
    'AegisLog investigates log files and native telemetry to highlight findings, incidents, and unusual activity.',
    'Choose 01 to analyze a file, 02/03/05 to monitor, or P for a recorded demo. Sources are handled read-only.',
    'R opens saved reports; S opens investigation tools; A explains the workflows. Enter selects; B returns; Q quits.',
)


def guide_view():
    return Group(Text('WHAT AEGISLOG DOES / HOW TO USE IT', style=f'bold {ACCENT}'),
                 *[Text(line, style=NEUTRAL) for line in INTRODUCTION],
                 Text('\n01 Analyze: choose a log path or demo; inspect findings and generate an HTML report.\n'
                      '02 Live / 03 Multi-source: watch appended events and compare sources.\n'
                      '04 Native logs / 05 Native monitor: select Windows, Linux journald, or Docker where available.\n'
                      '06 Incidents: review grouped evidence; grouping is not proof of a shared cause.\n'
                      '07 Demo / P Replay: explore synthetic or recorded activity.\n'
                      '08 Health: check runtime and collector availability. 09 Help: command reference.\n'
                      'S Workbench: filter evidence, inspect D Details and T Timeline, export JSON, and open reports.\n'
                      'C Check Computer: discover accessible native logs and select a time window.\n'
                      'D Local Dashboard: beginner/analyst browser views, text size and exports.\n'
                      'F Scan Folder: discover text logs and analyze selected files separately.\n'
                      'R Reports: open locally generated HTML reports in your browser.\n'
                      'Live views: B/Escape stops; Q quits. Home: PgUp/PgDn scroll; Home/End jump.\n'
                      'Findings and rarity scores require context; they do not prove an attack.', style=MUTED))


def report_candidates(root):
    if not root.exists():
        return []
    return sorted((p for p in [*root.glob('*.html'), *root.glob('folder-scan/*/*/*.html'), *root.glob('computer-checks/*/*.html'), *root.glob('desktop/*/*.html')] if p.is_file() and not p.name.endswith('-appendix.html')),
                  key=lambda p: p.stat().st_mtime_ns, reverse=True)[:20]


def open_saved_reports(console, root=None):
    from .commands_security import open_report
    root = root or Path.cwd() / 'aegislog-reports'
    try:
        reports = report_candidates(root)
    except OSError as exc:
        console.print(Text(f'Could not list reports: {exc}', style=MUTED))
        return
    console.print(Text('SAVED REPORTS / newest first', style=f'bold {ACCENT}'))
    console.print(Text(str(root.resolve()), style=MUTED))
    if not reports:
        console.print(Text('No saved HTML reports here. Use 01 Analyze or S Workbench → O to generate one.', style=NEUTRAL))
        return
    for number, path in enumerate(reports, 1):
        console.print(Text(f'{number:02d}  SUMMARY  |  {path.relative_to(root)}', style=NEUTRAL))
    choice = Prompt.ask('Report number', choices=[str(n) for n in range(1, len(reports) + 1)], default='1', console=console)
    selected = reports[int(choice) - 1]
    console.print(Text(f'Opening {selected.name}', style=ACCENT))
    open_report(selected)
