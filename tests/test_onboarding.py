from io import StringIO

import pytest
from rich.console import Console

from aegislog import commands_v11, onboarding
from aegislog.commands_v12 import _DEMO_LOG
from aegislog.navigation import WorkspaceBack, WorkspaceQuit, shell_navigation


def test_declining_walkthrough_never_analyzes(monkeypatch):
    monkeypatch.setattr(onboarding.Prompt, 'ask', lambda *args, **kwargs: 'n')
    monkeypatch.setattr(commands_v11, 'dashboard', lambda *args, **kwargs: pytest.fail('Analysis was not requested'))
    output = StringIO()
    onboarding.beginner_walkthrough(Console(file=output, width=100))
    assert 'fictional' in output.getvalue()
    assert 'creates local reports' in output.getvalue()


def test_walkthrough_uses_exact_synthetic_data_and_preserves_report(monkeypatch, tmp_path):
    monkeypatch.setattr(onboarding.Prompt, 'ask', lambda *args, **kwargs: 'y')
    report = tmp_path / 'summary.html'
    captured = []

    def analyze(source, timestamp_year):
        assert source.read_text() == _DEMO_LOG
        assert timestamp_year is None
        captured.append(source)
        report.write_text('report')
        commands_v11.last_report = report

    monkeypatch.setattr(commands_v11, 'dashboard', analyze)
    monkeypatch.setattr(commands_v11, 'last_report', None)
    output = StringIO()
    onboarding.beginner_walkthrough(Console(file=output, width=100))
    assert not captured[0].exists()
    assert report.exists()
    assert commands_v11.last_report == report
    assert 'O opens this summary' in output.getvalue()
    assert 'not proof of an attack' in output.getvalue()


@pytest.mark.parametrize('key, exception', [('b', WorkspaceBack), ('q', WorkspaceQuit)])
def test_walkthrough_back_and_quit_before_analysis(monkeypatch, key, exception):
    monkeypatch.setattr(commands_v11, 'dashboard', lambda *args, **kwargs: pytest.fail('Analysis was not requested'))
    console = Console(file=StringIO(), width=100)
    monkeypatch.setattr(console, 'input', lambda *args, **kwargs: key)
    with shell_navigation(), pytest.raises(exception):
        onboarding.beginner_walkthrough(console)


def test_walkthrough_does_not_promise_report_after_failure(monkeypatch):
    monkeypatch.setattr(onboarding.Prompt, 'ask', lambda *args, **kwargs: 'y')
    monkeypatch.setattr(commands_v11, 'dashboard', lambda *args, **kwargs: None)
    monkeypatch.setattr(commands_v11, 'last_report', None)
    output = StringIO()
    onboarding.beginner_walkthrough(Console(file=output, width=100))
    assert 'No report was created' in output.getvalue()
    assert 'O opens this summary' not in output.getvalue()
