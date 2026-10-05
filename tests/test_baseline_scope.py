import json
from types import SimpleNamespace

import pytest

from aegislog.activity_review import compare_activity, compare_signals, read_activity, save_activity


def baseline(root, scope, records=100):
    root.mkdir()
    data = SimpleNamespace(source='windows-System.log', records=records, recognized_records=records,
                           services={'app': records}, levels={'ERROR': records},
                           severities={}, incidents=[], findings=[])
    return save_activity(data, root, scope)


@pytest.mark.parametrize('compare', [compare_activity, compare_signals])
@pytest.mark.parametrize('scope', ['Latest 100 accessible events within 1440 minutes.',
                                 'Latest 300 accessible events within 60 minutes.', 'Another collection mode'])
def test_different_collection_settings_are_not_comparable(tmp_path, compare, scope):
    a = baseline(tmp_path / 'a', 'Latest 300 accessible events within 1440 minutes.')
    b = baseline(tmp_path / 'b', scope)
    with pytest.raises(ValueError, match='time window and event limit'):
        compare(a, b)


@pytest.mark.parametrize('compare', [compare_activity, compare_signals])
def test_returned_counts_and_limit_notices_do_not_change_settings(tmp_path, compare):
    a = baseline(tmp_path / 'a', 'Latest 300 accessible events within 1440 minutes. Returned 100 events.', 100)
    b = baseline(tmp_path / 'b', 'Latest 300 accessible events within 1440 minutes. Returned 300 events. Count limit reached.', 300)
    assert isinstance(compare(a, b), list)


@pytest.mark.parametrize('scope', [None, 42, 'bad\x1b[2Jscope', 'x' * 4097])
def test_invalid_scope_is_rejected(tmp_path, scope):
    path = baseline(tmp_path / 'a', 'valid')
    obj = json.loads(path.read_text()); obj['scope'] = scope
    path.write_text(json.dumps(obj))
    with pytest.raises(ValueError, match='collection scope'):
        read_activity(path)
