import hashlib
import json
from types import SimpleNamespace

import pytest

from aegislog.plugins import _compile_rule, apply_rules, load_rules
from aegislog.structured_input import Coverage, iter_records


def rule(pattern='danger-event'):
    return dict(id='probe', severity='HIGH', category='custom', title='Signal',
                pattern=pattern, recommendation='Review evidence.')


def test_growing_json_container_streams_after_actual_byte_limit(tmp_path, monkeypatch):
    path = tmp_path / 'growing.json'
    content = ('x' * 900 + '\n') * 10000
    path.write_text(content)
    monkeypatch.setattr(type(path), 'stat', lambda *args, **kwargs: SimpleNamespace(st_size=1))
    def forbid_whole_parse(raw):
        raise AssertionError('oversized growing JSON must not enter whole-container parser')
    monkeypatch.setattr('aegislog.structured_input.safe_json_loads', forbid_whole_parse)
    coverage = Coverage()
    assert sum(1 for _ in iter_records(path, coverage)) == 10000
    assert coverage.lines == 10000
    assert coverage.source_sha256 == hashlib.sha256(content.encode()).hexdigest()


@pytest.mark.parametrize('pattern', ['(a+)+$', 'a*a*a*$', '(a|aa)+$', r'(a)\1', r'(?=a)a'])
def test_backtracking_custom_patterns_rejected_before_execution(pattern):
    with pytest.raises(ValueError):
        _compile_rule(rule(pattern), 'probe')


def test_fixed_token_patterns_and_literal_metacharacters_work():
    compiled = _compile_rule(rule(r'^ERROR [0-9][0-9]|literal\+\(event\)$'), 'probe')
    assert len(apply_rules(['ERROR 42', 'literal+(event)', 'ordinary'], [compiled])) == 2


def test_pack_read_enforces_actual_bytes_and_rejects_atomically(tmp_path):
    (tmp_path / 'large.json').write_bytes(b' ' * 1_000_001)
    (tmp_path / 'mixed.json').write_text(json.dumps([rule(), rule('(a+)+$')]))
    rules, errors = load_rules(tmp_path)
    assert not rules
    assert len(errors) == 2
    assert any('bytes' in error for error in errors)
    assert any('disabled' in error for error in errors)


def test_rule_and_pack_counts_are_bounded(tmp_path):
    (tmp_path / 'too-many.json').write_text(json.dumps([rule()] * 101))
    rules, errors = load_rules(tmp_path)
    assert not rules and 'count limit' in errors[0]
    (tmp_path / 'too-many.json').unlink()
    for index in range(33):
        (tmp_path / f'{index:02}.json').write_text('[]')
    rules, errors = load_rules(tmp_path)
    assert not rules and 'pack limit' in errors[0]


def test_nested_pack_is_reported_without_crashing(tmp_path):
    (tmp_path / 'nested.json').write_text('[' * 70 + '0' + ']' * 70)
    rules, errors = load_rules(tmp_path)
    assert not rules and errors
