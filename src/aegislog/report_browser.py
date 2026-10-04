"""Local report navigation and a plain-language product guide."""
from pathlib import Path

from rich.console import Group
from rich.text import Text

from .navigation import Prompt
from .report_paths import report_search_roots
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
                      'C Check Computer: choose a time window and event count; known files use their full contents.\n'
                      'Completed computer checks: V compares a prior local activity baseline; S creates an aggregate sharing copy.\n'
                      'F Scan Folder: select likely logs; skip identical content; open a searchable batch overview.\n'
                      'G Beginner: optional guided synthetic demo and first-report walkthrough.\n'
                      'R Reports: browse all saved summaries and batches with N/P pages. O opens reports; F opens their folder.\n'
                      'Live views: B/Escape stops; Q quits. Home: PgUp/PgDn scroll; Home/End jump.\n'
                      'Unknown formats and zero findings do not establish a clean system. Findings and rarity scores require context; they do not prove an attack.', style=MUTED))


def report_candidates(root):
    if not root.exists():
        return []
    return sorted((p for p in [*root.glob('*.html'), *root.glob('folder-scan/*/*/*.html'), *root.glob('folder-scan/*/batch-index.html'), *root.glob('computer-checks/*/*.html'), *root.glob('desktop/*/*.html')] if p.is_file() and not p.name.endswith('-appendix.html')),
                  key=lambda p: p.stat().st_mtime_ns, reverse=True)


def open_saved_reports(console, root=None):
    from .commands_security import open_report
    roots = [Path(root)] if root is not None else report_search_roots()
    reports = []
    for directory in roots:
        try:
            reports.extend(report_candidates(directory))
        except OSError as exc:
            console.print(Text(f'Could not list reports in {directory}: {exc}', style=MUTED))
    reports = sorted(reports, key=lambda path: path.stat().st_mtime_ns, reverse=True)
    console.print(Text('SAVED REPORTS / newest first', style=f'bold {ACCENT}'))
    console.print(Text(' / '.join(str(directory) for directory in roots), style=MUTED))
    if not reports:
        console.print(Text('No saved HTML reports here. Use 01 Analyze or S Workbench → O to generate one.', style=NEUTRAL))
        return
    page = 0
    while True:
        start = page * 20
        console.print(Text(f'Page {page + 1}/{(len(reports) + 19) // 20} · {len(reports)} reports · N Next / P Previous', style=MUTED))
        for number, path in enumerate(reports[start:start + 20], start + 1):
            kind = 'BATCH' if path.name == 'batch-index.html' else 'SUMMARY'
            console.print(Text(f'{number:02d}  {kind}  |  {path.parent.name}/{path.name}', style=NEUTRAL))
        choice = Prompt.ask('Report number / N / P', default=str(start + 1), console=console).strip().lower()
        if choice == 'n':
            page = min(page + 1, (len(reports) - 1) // 20)
        elif choice == 'p':
            page = max(0, page - 1)
        elif choice.isdigit() and 1 <= int(choice) <= len(reports):
            selected = reports[int(choice) - 1]
            console.print(Text(f'Opening {selected.name}', style=ACCENT))
            open_report(selected)
            return
        else:
            console.print(Text('Choose a report number, N or P.', style=MUTED))


def report_actions(console, path):
    """Open completed reports without copying wrapped terminal paths."""
    import os
    import webbrowser
    from .commands_security import open_report
    while True:
        activity = (path.parent / 'activity-baseline.json').is_file()
        menu = 'O Report / F Folder / V Compare baseline / S Share summary / Enter Back' if activity else 'O Open report / F Open folder / Enter Back'
        choice = Prompt.ask(menu, default='b', console=console).strip().lower()
        if choice in {'', 'b', 'back'}:
            return
        try:
            if choice == 'o':
                open_report(path)
            elif choice == 'f':
                if os.name == 'nt':
                    os.startfile(str(path.resolve().parent))  # nosec B606 -- open generated report directory, no shell command
                else:
                    webbrowser.open(path.resolve().parent.as_uri())
            elif choice in {'v', 's'}:
                from .activity_review import compare_activity, share_activity
                baseline = path.parent / 'activity-baseline.json'
                if not baseline.is_file():
                    console.print('Generate this report through C Check Computer to use activity comparisons and sharing.')
                    continue
                if choice == 's':
                    destination = path.parent / 'share-summary.json'
                    share_activity(baseline, destination)
                    console.print(f'Sharing summary: {destination}. Raw evidence and identifiers omitted.', markup=False)
                else:
                    from pathlib import Path
                    previous = Path(Prompt.ask('Previous activity-baseline.json path', console=console).strip().strip('"')).expanduser()
                    changes = compare_activity(previous, baseline)
                    console.print('Local sample comparison; normalized shares are not event rates or proof of an attack.')
                    for item in changes[:20]:
                        console.print(f'{item["provider"]}: {item["previous"]} → {item["current"]} records; {item["previous_percent"]}% → {item["current_percent"]}% of sample', markup=False)
                    console.print(f'{len(changes)} provider changes; showing up to 20. No change does not establish safety.')
            else:
                console.print(Text('Choose O, F, V, S or B.', style=MUTED))
        except (OSError, ValueError) as exc:
            console.print(Text(f'Could not complete report action: {exc}', style=MUTED))
