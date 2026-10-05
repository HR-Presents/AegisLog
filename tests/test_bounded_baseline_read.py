import json
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from aegislog import activity_review


def test_growing_baseline_is_rejected_even_when_size_metadata_is_stale(tmp_path, monkeypatch):
    path = tmp_path / 'baseline.json'
    obj = dict(schema=activity_review.SCHEMA, source='synthetic.log', scope='scope', records=1,
               recognized=1, incidents=0, services={}, levels={}, severities={}, note='x' * 2_000_001)
    path.write_text(json.dumps(obj))
    original_stat = Path.stat

    def stale_stat(self, *args, **kwargs):
        if self == path:
            return SimpleNamespace(st_size=0, st_mode=stat.S_IFREG)
        return original_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'stat', stale_stat)
    monkeypatch.setattr(activity_review.os, 'fstat', lambda fd: SimpleNamespace(st_size=0, st_mode=stat.S_IFREG))
    with pytest.raises(ValueError, match='smaller than 2 MB'):
        activity_review.read_activity(path)


def test_baseline_directory_is_rejected_with_regular_file_guidance(tmp_path):
    with pytest.raises(ValueError, match='regular baseline JSON'):
        activity_review.read_activity(tmp_path)
