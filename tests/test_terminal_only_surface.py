from io import StringIO

from rich.console import Console
from typer.testing import CliRunner

from aegislog.entry import app
from aegislog.commands_v145 import _home
from aegislog.report_browser import guide_view


def test_terminal_commands_remain_without_browser_dashboard():
    result = CliRunner().invoke(app, ['--help'])
    assert result.exit_code == 0
    assert 'desktop' not in result.stdout
    assert 'dashboard' in result.stdout and 'check-computer' in result.stdout


def test_home_and_guide_omit_browser_dashboard():
    console = Console(file=StringIO(), width=125, record=True)
    console.print(_home(125, 33))
    console.print(guide_view())
    output = console.export_text()
    assert 'LOCAL DASHBOARD' not in output and 'D Local Dashboard' not in output
    for label in ('CHECK COMPUTER', 'SCAN FOLDER', 'REPORTS', 'ANALYZE LOG'):
        assert label in output
