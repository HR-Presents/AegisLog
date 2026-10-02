from io import StringIO
from rich.console import Console
from aegislog.report_browser import open_saved_reports, guide_view


def test_report_option_opens_selected_local_html(tmp_path, monkeypatch):
    from aegislog import report_browser, commands_security
    path = tmp_path / 'report.html'
    path.write_text('<html>local report</html>')
    opened = []
    monkeypatch.setattr(report_browser.Prompt, 'ask', lambda *a, **kw: '1')
    monkeypatch.setattr(commands_security, 'open_report', opened.append)
    open_saved_reports(Console(file=StringIO()), tmp_path)
    assert opened == [path]


def test_empty_reports_folder_explains_how_to_generate(tmp_path):
    console = Console(file=StringIO(), record=True)
    open_saved_reports(console, tmp_path)
    assert 'No saved HTML reports' in console.export_text()


def test_guide_explains_workflows_and_controls():
    console = Console(file=StringIO(), width=120, record=True)
    console.print(guide_view())
    text = console.export_text()
    assert '01 Analyze' in text and 'R Reports' in text
    assert 'B/Escape stops' in text and 'Q quits' in text
