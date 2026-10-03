"""Optional first-investigation walkthrough using explicitly synthetic evidence."""
from pathlib import Path
from tempfile import TemporaryDirectory

from rich.text import Text

from .navigation import Prompt
from .theme import ACCENT, MUTED, NEUTRAL


def beginner_walkthrough(console):
    from . import commands_v11
    from .commands_v12 import _DEMO_LOG

    console.print(Text('FIRST INVESTIGATION / BEGINNER WALKTHROUGH', style=f'bold {ACCENT}'))
    console.print(Text(
        'AegisLog reads logs, highlights investigation leads, and creates local reports. '
        'It leaves source logs and host settings unchanged. B returns; Q exits to your terminal.', style=NEUTRAL))
    console.print(Text(
        '\n1 / CHOOSE A WORKFLOW\n'
        '01 Analyze: investigate a file you already have.\n'
        'C Check Computer: inspect accessible operating-system logs.\n'
        'F Scan Folder: investigate several selected files.\n'
        '02/03/05 Monitor: watch new events from supported sources.\n'
        'R Reports: open saved investigations. A Guide: read workflow explanations.', style=NEUTRAL))
    console.print(Text(
        '\n2 / TRY SYNTHETIC EVIDENCE\n'
        'This optional demo uses fictional authentication failures and a service timeout. '
        'It does not inspect your computer or represent a finding about your system. '
        'Running it creates local reports.', style=NEUTRAL))
    choice = Prompt.ask('Run the synthetic demo? Y Yes / N Return', choices=['y', 'n'], default='n', console=console)
    if choice.lower() != 'y':
        return

    # A dedicated temporary file guarantees the walkthrough never substitutes a
    # similarly named file from the user's working directory for synthetic data.
    with TemporaryDirectory(prefix='aegislog-beginner-') as directory:
        source = Path(directory) / 'demo_auth.log'
        source.write_text(_DEMO_LOG, encoding='utf-8')
        commands_v11.dashboard(source, timestamp_year=None)

    if commands_v11.last_report is None:
        console.print(Text('No report was created. Review the analysis message before retrying.', style=MUTED))
        return
    console.print(Text(
        '\n3 / READ THE RESULTS\n'
        'Start with coverage: records processed, recognized formats, and retained evidence. '
        'The built-in demo has an authentication investigation lead and an operational error. '
        'Severity means priority for review, not proof of an attack. '
        'Yearless timestamps do not establish elapsed time.', style=NEUTRAL))
    console.print(Text(
        '\n4 / OPEN YOUR FIRST REPORT\n'
        'At the next prompt, O opens this summary and F opens its report folder. '
        'Inside the summary, open the full retained-evidence report for details. '
        'Use the separate summary or complete-report print actions to save a PDF.\n'
        'B returns home. Next try 01 with your own readable log or C for native logs. '
        'The temporary demo source has been removed; generated reports remain available through R.', style=NEUTRAL))
