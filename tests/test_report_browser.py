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


def test_report_picker_excludes_evidence_appendices(tmp_path):
    from aegislog.report_browser import report_candidates
    summary = tmp_path / 'case-report.html'
    summary.write_text('summary')
    (tmp_path / 'case-report-appendix.html').write_text('full evidence')
    assert report_candidates(tmp_path) == [summary]


def test_older_report_is_reachable_after_first_page(tmp_path, monkeypatch):
    from aegislog import report_browser, commands_security
    for number in range(25):
        (tmp_path / f'{number}.html').write_text('report')
    reports = report_browser.report_candidates(tmp_path)
    assert len(reports) == 25
    replies = iter(['n', '25'])
    opened = []
    monkeypatch.setattr(report_browser.Prompt, 'ask', lambda *a, **kw: next(replies))
    monkeypatch.setattr(commands_security, 'open_report', opened.append)
    console = Console(file=StringIO(), record=True)
    open_saved_reports(console, tmp_path)
    assert opened == [reports[24]]
    assert 'Page 2/2' in console.export_text()


def test_report_actions_open_without_copying_path(tmp_path, monkeypatch):
    from aegislog import report_browser, commands_security
    replies = iter(['o', 'b'])
    opened = []
    monkeypatch.setattr(report_browser.Prompt, 'ask', lambda *a, **kw: next(replies))
    monkeypatch.setattr(commands_security, 'open_report', opened.append)
    report_browser.report_actions(Console(file=StringIO()), tmp_path / 'report.html')
    assert opened == [tmp_path / 'report.html']
