from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console
from rich.prompt import Prompt as RichPrompt

from aegislog import commands_v144, commands_v145
from aegislog.navigation import Prompt, WorkspaceBack, WorkspaceQuit, shell_navigation, wait_for_navigation


@pytest.mark.parametrize('value,exception', [('b', WorkspaceBack), ('back', WorkspaceBack), ('q', WorkspaceQuit)])
def test_navigation_works_at_choice_prompts(monkeypatch, value, exception):
    monkeypatch.setattr(RichPrompt, 'ask', classmethod(lambda cls, *a, **kw: value))
    with shell_navigation(), pytest.raises(exception):
        Prompt.ask('Profile', choices=['security', 'web'])


def test_navigation_scope_does_not_change_standalone_prompts(monkeypatch):
    monkeypatch.setattr(RichPrompt, 'ask', classmethod(lambda cls, *a, **kw: 'back'))
    with shell_navigation(), pytest.raises(WorkspaceBack):
        Prompt.ask('Path')
    assert Prompt.ask('Path') == 'back'


@pytest.mark.parametrize('key,exception', [('b', KeyboardInterrupt), ('q', WorkspaceQuit), ('\x1b', KeyboardInterrupt)])
def test_live_navigation_interrupts_wait_immediately(key, exception):
    class Reader:
        enabled = True
        def poll(self):
            return key
    with pytest.raises(exception):
        wait_for_navigation(Reader(), 30, sleep=lambda _: pytest.fail('must not sleep'))


def test_home_redraws_while_typing_and_preserves_input(monkeypatch):
    keys = iter([None, '0', '2', '\x08', '1', '\r'])
    frames = []
    class Reader:
        enabled = True
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def poll(self):
            return next(keys)
    class Live:
        def __init__(self, frame, **kw):
            frames.append(frame)
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def update(self, frame, **kw):
            frames.append(frame)
    console = Console(file=StringIO(), force_terminal=True, width=100, height=50)
    monkeypatch.setattr(commands_v145.legacy, 'console', console)
    monkeypatch.setattr(commands_v145, 'KeyboardReader', Reader)
    monkeypatch.setattr(commands_v145, 'Live', Live)
    monkeypatch.setattr(commands_v145.time, 'sleep', lambda _: None)
    assert commands_v145._read_home_choice() == '01'
    assert len(frames) >= 5


def test_refresh_reanalyzes_same_source_then_back(monkeypatch):
    analyzed = []
    choices = iter(['r', 'b'])
    monkeypatch.setattr(commands_v144, 'console', Console(file=StringIO()))
    monkeypatch.setattr(commands_v144, 'dashboard', lambda path, **kw: analyzed.append(path))
    monkeypatch.setattr(RichPrompt, 'ask', classmethod(lambda cls, *a, **kw: next(choices)))
    with shell_navigation(), pytest.raises(WorkspaceBack):
        commands_v144._run_analysis_workspace(Path('demo.log'), 'Analyze', 'Saved file')
    assert analyzed == [Path('demo.log'), Path('demo.log')]



def test_short_home_keeps_original_logo_and_scrolls_to_panels():
    console = Console(file=StringIO(), width=140, height=14, record=True, color_system=None)
    console.print(commands_v145._HomeViewport(140, 13, 0))
    top = console.export_text()
    assert "DEFENSIVE LOG INVESTIGATION" in top and "HR-PRESENTS" in top
    console.print(commands_v145._HomeViewport(140, 13, 9))
    middle = console.export_text()
    assert "INVESTIGATE" in middle and "SYSTEM" in middle
    console.print(commands_v145._HomeViewport(140, 13, 100))
    bottom = console.export_text()
    assert "UTILITIES" in bottom and "Q Exit" in bottom


def test_short_laptop_layout_fits_all_panels_without_losing_brand():
    console = Console(file=StringIO(), width=140, color_system=None)
    lines = console.render_lines(commands_v145._home(140, 39), console.options)
    output = "\n".join("".join(segment.text for segment in line) for line in lines)
    assert len(lines) <= 39
    for label in ("DEFENSIVE LOG INVESTIGATION", "SYSTEM", "QUICK INFO", "UTILITIES", "Q Exit"):
        assert label in output


def test_scroll_clamps_after_bottom_and_resize():
    console = Console(file=StringIO(), width=140, height=14)
    view = commands_v145._HomeViewport(140, 12, 1000000).prepare(console, console.options)
    assert view.offset == view.maximum > 0
    previous = view.offset
    view.offset -= 1
    view.prepare(console, console.options)
    assert view.offset == previous - 1
    view.height = 100
    view.prepare(console, console.options)
    assert view.offset == view.maximum == 0
