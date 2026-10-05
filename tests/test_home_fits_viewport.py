from io import StringIO

import pytest
from rich.console import Console

from aegislog.commands_v145 import _HomeViewport


@pytest.mark.parametrize('width,height', [(125, 30), (140, 30), (120, 27), (100, 24), (80, 27), (60, 27), (80, 24), (120, 40), (200, 50)])
def test_laptop_home_keeps_all_actions_visible(width, height):
    console = Console(file=StringIO(), width=width, height=height + 3, color_system=None)
    view = _HomeViewport(width, height).prepare(console, console.options)
    text = '\n'.join(''.join(segment.text for segment in line) for line in view.lines)
    assert view.maximum == 0
    for key in ['01', '02', '03', '04', '05', '06', '07', '08', '09', 'C', 'F', 'R', 'A', 'G']:
        assert f'[{key}]' in text
    assert 'HR-PRESENTS' in text
    assert 'READ-ONLY' in text
    assert 'UTC' in text
    assert 'Q Exit' in text
    assert all(sum(segment.cell_length for segment in line) <= width for line in view.lines)


def test_regular_laptop_keeps_ascii_logo_and_configuration_hint():
    console = Console(file=StringIO(), width=125, color_system=None)
    view = _HomeViewport(125, 30).prepare(console, console.options)
    text = '\n'.join(''.join(segment.text for segment in line) for line in view.lines)
    assert '/_/' in text
    assert '08 Health shows the full path' in text
    assert 'QUICK INFO' in text
