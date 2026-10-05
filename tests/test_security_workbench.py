from pathlib import Path
import hashlib
import json
from dataclasses import replace
from io import StringIO

import pytest
from rich.console import Console
from typer.testing import CliRunner

from aegislog.commands_security import demo_events, timeline_view, write_security_report
from aegislog.entry import app
from aegislog.security_workbench import (
    Filters, Tuning, check_integrity, export_evidence, extra_signals,
    investigate_file, load_watchlist, make_record, observed_indicators, record_integrity,
)
from aegislog.collector_health import CollectorHealth
from aegislog.native_collectors import CollectorError
from aegislog.native_live import NativeLivePoller
from aegislog.realtime import RealtimeState, initial_cursor
from aegislog.multisource import poll_sources


@pytest.fixture
def demo(tmp_path):
    path = tmp_path / 'demo.log'
    path.write_text(demo_events())
    return path


def login_signals(lines, tuning=None):
    return [s for s in extra_signals([make_record(n, line) for n, line in enumerate(lines, 1)], tuning or Tuning(), set())
            if s.finding.title == 'Successful login after repeated failures']


def logins(account='alice', ip='203.0.113.9', host='node1'):
    return [f'2026-10-02T12:00:{n:02d}Z sshd: Failed password for alice from 203.0.113.9 host=node1' for n in range(5)] + [
        f'2026-10-02T12:00:30Z sshd: Accepted password for {account} from {ip} host={host}']


def test_login_sequence_has_exact_line_references():
    signals = login_signals(logins())
    assert len(signals) == 1
    assert signals[0].lines == (1, 2, 3, 4, 5, 6)
    assert 'does not prove compromise' in signals[0].finding.recommendation


@pytest.mark.parametrize('account,ip,host', [('bob','203.0.113.9','node1'), ('alice','203.0.113.10','node1'), ('alice','203.0.113.9','node2')])
def test_unrelated_account_ip_host_never_correlates(account, ip, host):
    assert not login_signals(logins(account, ip, host))


def test_missing_or_expired_timestamps_do_not_imply_sequence():
    lines = logins()
    lines[-1] = lines[-1].replace('12:00:30', '12:10:30')
    assert not login_signals(lines)
    assert not login_signals([line.split(' ', 1)[1] for line in logins()])


def test_out_of_order_sequence_and_tuning():
    lines = logins()
    assert login_signals([lines[-1], *reversed(lines[:-1])])
    assert not login_signals(lines, Tuning(login_failure_threshold=6))


def test_success_resets_failure_sequence():
    lines = logins()
    lines.append(lines[-1].replace('12:00:30','12:00:31'))
    assert len(login_signals(lines)) == 1


def test_windows_login_sequence_requires_explicit_target_host():
    lines = [f'2026-10-02T12:00:{n:02d}Z Microsoft-Windows-Security-Auditing[4625]: INFO Account Name: alice Source Network Address: 203.0.113.9 Workstation Name: node1' for n in range(5)]
    lines.append('2026-10-02T12:00:30Z Microsoft-Windows-Security-Auditing[4624]: INFO Account Name: alice Source Network Address: 203.0.113.9 Workstation Name: node1')
    assert not login_signals(lines)


def test_workbench_preserves_windows_findings(demo):
    result = investigate_file(demo)
    assert {'account','privilege','process','audit'} <= {s.finding.category for s in result.signals}
    assert any('Successful login' in s.finding.title for s in result.signals)


def test_filters_share_event_and_finding_scope(demo):
    result = investigate_file(demo)
    records, signals = result.select(Filters(severity='HIGH', category='authentication'))
    assert signals and all(s.finding.severity == 'HIGH' and s.finding.category == 'authentication' for s in signals)
    assert {r.line for r in records} == {n for s in signals for n in s.lines}
    assert result.select(Filters(service='missing')) == ([], [])
    records, _ = result.select(Filters(since='2026-10-02T14:02:00+02:00', until='2026-10-02T12:02:02Z'))
    assert len(records) == 3
    assert result.select(Filters(source='windows'))[0]


@pytest.mark.parametrize('filters', [Filters(since='2026-10-02T12:00:00'), Filters(since='bad'), Filters(since='2026-10-02T13:00:00Z',until='2026-10-02T12:00:00Z'),Filters(severity='bad')])
def test_invalid_filter_is_rejected(filters):
    with pytest.raises(ValueError):
        filters.validate()


def test_timestamp_formats():
    assert make_record(1, '192.0.2.1 - - [02/Oct/2026:14:00:00 +0200] "GET / HTTP/1.1" 200').timestamp.startswith('2026-10-02T12:00')
    assert make_record(1, '{"timestamp":"2026-10-02T12:00:00Z","service":"api","message":"ok"}').timestamp


def test_watchlist_matches_exact_normalized_indicators(tmp_path):
    path = tmp_path / 'watch.txt'
    path.write_text('# supplied by analyst\n203.0.113.9\n2001:db8::1\nexample.test\n')
    indicators = load_watchlist(path)
    assert observed_indicators('url=https://example.test/path src=203.0.113.9 [2001:0db8:0:0:0:0:0:1]') & indicators == indicators
    assert not (observed_indicators('url=https://notexample.test.example/ ip=203.0.113.90') & indicators)
    path.write_text('not a valid indicator')
    with pytest.raises(ValueError):load_watchlist(path)


def test_suppression_remains_in_export_and_report(demo, tmp_path):
    tune = tmp_path / 'tune.json'
    tune.write_text(json.dumps({'exceptions':[{'category':'audit','contains':'demo-admin','reason':'Authorized demo audit clearing'}]}))
    result = investigate_file(demo, Tuning.load(tune))
    suppressed = [s for s in result.signals if s.suppression_reason]
    assert suppressed and suppressed[0].finding.category == 'audit'
    assert 'audit' not in result.dashboard(Filters()).categories
    output = tmp_path / 'evidence.json'; export_evidence(result, Filters(), output)
    payload = json.loads(output.read_text())
    assert any(s['suppression_reason'] for s in payload['findings'])
    assert all('token=DEMO_ONLY' not in event['evidence'] for event in payload['events'])
    assert payload['source_fingerprint_at_export']['sha256'] == hashlib.sha256(demo.read_bytes()).hexdigest()
    report = write_security_report(result, Filters(), tmp_path / 'reports')
    assert 'Authorized demo audit clearing' in report.with_name(report.stem + '-appendix.html').read_text()


@pytest.mark.parametrize('obj', [{'login_failure_threshold':True},{'login_window_seconds':0},{'unexpected':1},{'exceptions':[{'category':'web','contains':'','reason':'okay'}]}])
def test_bad_tuning_rejected(tmp_path,obj):
    path=tmp_path/'tune.json';path.write_text(json.dumps(obj))
    with pytest.raises(ValueError):Tuning.load(path)


def test_integrity_detects_growth_and_does_not_overwrite(demo,tmp_path):
    baseline=tmp_path/'baseline.json';before=demo.read_bytes()
    record_integrity(demo,baseline)
    assert check_integrity(demo,baseline)['status']=='UNCHANGED'
    with pytest.raises(FileExistsError):record_integrity(demo,baseline)
    with pytest.raises(ValueError):record_integrity(demo,demo)
    demo.write_bytes(before+b'new line\n')
    assert check_integrity(demo,baseline)['status']=='CHANGED'
    other=tmp_path/'other.log';other.write_bytes(demo.read_bytes())
    with pytest.raises(ValueError):check_integrity(other,baseline)


def test_export_refuses_overwrite_and_redacts_secrets(tmp_path):
    source=tmp_path/'secret.log';source.write_text('2026-10-02T12:00:00Z ERROR api: timeout password=VERY_SECRET token=OTHER_SECRET\n')
    result=investigate_file(source);output=tmp_path/'export.json'
    export_evidence(result,Filters(),output)
    assert 'VERY_SECRET' not in output.read_text() and 'OTHER_SECRET' not in output.read_text()
    with pytest.raises(FileExistsError):export_evidence(result,Filters(),output)
    with pytest.raises(ValueError):export_evidence(result,Filters(),source)


def test_report_escapes_timeline_fields(demo,tmp_path):
    result=investigate_file(demo)
    result.records[0]=replace(result.records[0],action='account created',account='<script>bad</script>')
    report=write_security_report(result,Filters(),tmp_path/'reports')
    text=report.with_name(report.stem + '-appendix.html').read_text()
    assert '<script>bad</script>' not in text and '&lt;script&gt;bad&lt;/script&gt;' in text
    console=Console(file=StringIO(),width=40,record=True)
    console.print(timeline_view(result.records))
    assert max(map(len,console.export_text().splitlines()))<=40


def test_retained_evidence_is_bounded(tmp_path):
    path=tmp_path/'big.log';path.write_text('2026-10-02T12:00:00Z INFO api: okay\n'*10010)
    result=investigate_file(path)
    assert len(result.records)==10000 and result.sampled_lines==10
    path.write_text('x'*20000+'\n')
    assert investigate_file(path).truncated_lines==1


def test_native_health_failure_and_recovery(monkeypatch):
    from aegislog import native_live
    calls=iter([CollectorError('Permission denied token=SECRET'),[],['event']])
    def collect(*a,**kw):
        result=next(calls)
        if isinstance(result,Exception):raise result
        return result
    monkeypatch.setattr(native_live,'collect',collect)
    poller=NativeLivePoller('windows')
    with pytest.raises(CollectorError):poller.poll()
    assert poller.health.status=='UNAVAILABLE' and 'SECRET' not in poller.health.detail
    assert poller.poll()==[] and poller.health.status=='AVAILABLE'
    assert poller.health.last_success and poller.health.failures==1
    assert poller.poll()==['event']


def test_multisource_health_keeps_other_sources_running(tmp_path,monkeypatch):
    from aegislog import multisource
    a,b=tmp_path/'a.log',tmp_path/'b.log';a.write_text('a\n');b.write_text('b\n')
    cursors={a:initial_cursor(a,from_start=True),b:initial_cursor(b,from_start=True)}
    original=multisource.read_new_lines_cursor
    def read(path,cursor):
        if path==a:raise PermissionError('permission denied')
        return original(path,cursor)
    monkeypatch.setattr(multisource,'read_new_lines_cursor',read)
    health={};batches,_=poll_sources((a,b),cursors,health)
    assert batches==[(b,['b\n'])]
    assert health[str(a)].status=='UNAVAILABLE' and health[str(b)].status=='AVAILABLE'


def test_live_state_includes_login_sequence():
    state=RealtimeState('demo',window_size=50)
    state.ingest(logins())
    assert any(f.title=='Successful login after repeated failures' for f in state.findings)


def test_health_empty_success_is_not_failure():
    health=CollectorHealth();health.success(0)
    assert health.status=='AVAILABLE' and health.events==0 and health.last_success


def test_cli_security_export_integrity_and_replay(demo,tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner=CliRunner();output=tmp_path/'evidence.json'
    result=runner.invoke(app,['security',str(demo),'--severity','HIGH','--export',str(output)])
    assert result.exit_code==0,result.output
    assert output.exists() and 'SECURITY WORKBENCH' in result.output
    baseline=tmp_path/'baseline.json'
    assert runner.invoke(app,['integrity-record',str(demo),str(baseline)]).exit_code==0
    assert runner.invoke(app,['integrity-check',str(demo),str(baseline)]).exit_code==0
    demo.write_text(demo.read_text()+'INFO new\n')
    assert runner.invoke(app,['integrity-check',str(demo),str(baseline)]).exit_code==1
    result=runner.invoke(app,['replay','--interval','0.05','--limit','2'])
    assert result.exit_code==0 and 'DEMO REPLAY' in result.output


def test_multisource_health_renders_without_state_attribute_errors(tmp_path):
    from aegislog.multisource import MultiSourceState
    from aegislog.command_center_ui import render_multisource_command_center
    path=tmp_path/'a.log';path.write_text('INFO healthy\n')
    state=MultiSourceState((path,),window_size=50)
    item=CollectorHealth();item.success(1);state.collector_health[str(path)]=item
    state.ingest(path,['INFO healthy\n'])
    console=Console(file=StringIO(),width=80,record=True)
    console.print(render_multisource_command_center(state))
    assert 'COLLECTOR HEALTH' in console.export_text()


def test_multisource_sequence_never_combines_separate_sources(tmp_path):
    from aegislog.multisource import MultiSourceState
    a,b=tmp_path/'a.log',tmp_path/'b.log'
    state=MultiSourceState((a,b),window_size=50)
    lines=logins();state.ingest(a,lines[:-1]);state.ingest(b,[lines[-1]])
    assert not any(f.title=='Successful login after repeated failures' for f in state.findings)


def test_replay_leaves_source_bytes_unchanged(demo,monkeypatch):
    from aegislog import commands_security
    before=demo.read_bytes()
    monkeypatch.setattr(commands_security,'console',Console(file=StringIO(),width=80))
    commands_security.replay_file(demo,interval=0.001,limit=2)
    assert demo.read_bytes()==before


def test_source_service_filter_handles_service_first_iso(tmp_path):
    path=tmp_path/'auth.log';path.write_text(logins()[0]+'\n')
    result=investigate_file(path)
    records,_=result.select(Filters(service='sshd'))
    assert len(records)==1 and records[0].source=='iso-service'


def test_uppercase_action_uses_canonical_choice(monkeypatch):
    from rich.prompt import Prompt as RichPrompt
    from aegislog.navigation import Prompt, shell_navigation
    monkeypatch.setattr(RichPrompt,'ask',classmethod(lambda cls,*a,**kw:'F'))
    with shell_navigation():
        assert Prompt.ask('Action',choices=['f','r'])=='f'


def test_report_opens_local_file_uri(demo,tmp_path,monkeypatch):
    from aegislog import commands_security
    report=write_security_report(investigate_file(demo),Filters(),tmp_path/'reports')
    calls=[]
    monkeypatch.setattr(commands_security.webbrowser,'open',lambda uri:calls.append(uri) or True)
    commands_security.open_report(report)
    assert calls==[report.resolve().as_uri()]


def test_default_view_preserves_previous_dashboard_before_controls(demo,monkeypatch):
    from aegislog import commands_security
    from aegislog.dashboard_v213 import render_dashboard
    investigation=investigate_file(demo)
    console=Console(file=StringIO(),width=120,record=True)
    monkeypatch.setattr(commands_security,'console',console)
    console.print(commands_security.workbench_view(investigation,Filters()))
    actual=console.export_text()
    original=Console(file=StringIO(),width=120,record=True)
    original.print(render_dashboard(investigation.dashboard(Filters()),screen_width=120))
    assert actual.startswith(original.export_text())
    assert 'SECURITY WORKBENCH / SAVED FILE' not in actual
    assert '[V Scope]' in actual


def test_finding_details_show_evidence_recommendation_and_filter_scope(demo):
    from aegislog.commands_security import finding_details
    investigation = investigate_file(demo)
    console = Console(file=StringIO(), width=120, record=True)
    console.print(finding_details(investigation, Filters()))
    output = console.export_text()
    assert 'Next investigation:' in output and 'Source line references:' in output
    assert 'Verify account ownership' in output and 'Line ' in output
    console.print(finding_details(investigation, Filters(category='does-not-exist')))
    assert 'No findings match' in console.export_text()


def test_collector_health_distinguishes_empty_success_and_failure():
    from aegislog.collector_health import render_collector_health
    health = CollectorHealth()
    console = Console(file=StringIO(), width=120, record=True)
    health.success(0)
    console.print(render_collector_health({'demo': health}))
    assert 'no events returned' in console.export_text()
    health.success(2)
    console.print(render_collector_health({'demo': health}))
    assert 'events returned' in console.export_text()
    health.failure(OSError('source missing'))
    console.print(render_collector_health({'demo': health}))
    assert 'collection unavailable' in console.export_text()


def test_fingerprint_uses_handle_metadata_for_path_recheck(demo, monkeypatch):
    from aegislog.security_workbench import fingerprint
    original = Path.stat
    def divergent_stat(path, *args, **kwargs):
        from types import SimpleNamespace
        result = original(path, *args, **kwargs)
        if path == demo:
            return SimpleNamespace(st_size=result.st_size, st_mtime_ns=result.st_mtime_ns, st_ctime_ns=result.st_ctime_ns + 1, st_ino=0)
        return result
    monkeypatch.setattr(Path, 'stat', divergent_stat)
    assert fingerprint(demo)['sha256'] == hashlib.sha256(demo.read_bytes()).hexdigest()
