"""Bounded, evidence-oriented investigation tools; no response actions."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .anomaly import score_events
from .dashboard import DashboardData
from .engine import AnalysisState, Finding, AUTH_FAILURE_RE, _auth_event, _parse_timestamp
from .incidents import correlate
from .ingestion import iter_bounded_lines
from .parsers import parse_line
from .sanitize import redact_sensitive
from .windows_security import parse_windows_security_line, signal_for_event


@dataclass(frozen=True)
class Tuning:
    login_failure_threshold: int = 5
    login_window_seconds: int = 300
    exceptions: tuple[dict, ...] = ()

    @classmethod
    def load(cls, path: Path | None):
        if path is None:
            return cls()
        if path.stat().st_size > 100_000:
            raise ValueError("Tuning file exceeds 100 KB")
        obj = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(obj, dict) or set(obj) - {"login_failure_threshold", "login_window_seconds", "exceptions"}:
            raise ValueError("Unsupported tuning fields")
        threshold = obj.get("login_failure_threshold", 5)
        window = obj.get("login_window_seconds", 300)
        if type(threshold) is not int or not 2 <= threshold <= 100:
            raise ValueError("Login failure threshold must be 2..100")
        if type(window) is not int or not 30 <= window <= 3600:
            raise ValueError("Login window must be 30..3600 seconds")
        exceptions = obj.get("exceptions", [])
        if not isinstance(exceptions, list) or len(exceptions) > 50:
            raise ValueError("At most 50 exceptions are supported")
        for item in exceptions:
            if not isinstance(item, dict) or set(item) != {"category", "contains", "reason"}:
                raise ValueError("Each exception needs category, contains, and reason")
            if any(not isinstance(v, str) or not v.strip() or len(v) > 256 for v in item.values()):
                raise ValueError("Exception fields must be nonempty strings of at most 256 characters")
        return cls(threshold, window, tuple(exceptions))


@dataclass(frozen=True)
class Record:
    line: int
    timestamp: str | None
    source: str
    service: str
    level: str
    evidence: str
    account: str | None = None
    source_ip: str | None = None
    host: str | None = None
    action: str | None = None


@dataclass(frozen=True)
class Signal:
    finding: Finding
    lines: tuple[int, ...]
    suppression_reason: str | None = None


@dataclass(frozen=True)
class Filters:
    severity: str = ""
    category: str = ""
    service: str = ""
    source: str = ""
    since: str = ""
    until: str = ""

    def validate(self):
        if any(len(value) > 4096 for value in asdict(self).values()):
            raise ValueError("Filter values exceed the supported length")
        if self.severity and self.severity.upper() not in {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise ValueError("Unknown severity")
        start, end = parse_boundary(self.since), parse_boundary(self.until)
        if start and end and start > end:
            raise ValueError("Since must precede until")


def parse_boundary(value: str):
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Time filters need ISO timestamps with a timezone") from exc
    if stamp.tzinfo is None:
        raise ValueError("Time filters need an explicit timezone, such as Z")
    return stamp.astimezone(timezone.utc)


def _timestamp(line: str, year: int | None):
    stamp = _parse_timestamp(line, year)
    if stamp is None and line.lstrip().startswith("{"):
        try:
            obj = json.loads(line)
            value = obj.get("timestamp") or obj.get("time")
            if isinstance(value, str):
                stamp = parse_boundary(value)
        except (ValueError, AttributeError):
            pass
    if stamp is None:
        match = re.search(r"\[(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})\]", line)
        if match:
            try:
                stamp = datetime.strptime(match.group(1), "%d/%b/%Y:%H:%M:%S %z")
            except ValueError:
                pass
    return stamp.astimezone(timezone.utc).isoformat() if stamp else None


def make_record(number: int, line: str, year: int | None = None):
    safe = redact_sensitive(line)
    event = parse_line(safe)
    auth = _auth_event(safe, year)
    win = parse_windows_security_line(safe)
    action = None
    account, ip, host = auth.account, auth.source_ip, auth.host
    if win:
        account, ip, host = win.account, win.source_ip, win.workstation
        action = {4625: "login failure", 4624: "login success", 4720: "account created",
                  4728: "global group changed", 4732: "local group changed",
                  4672: "privileged session", 4740: "account locked", 1102: "audit log cleared",
                  4688: "process created"}.get(win.event_id)
    elif re.search(r"\bAccepted (?:password|publickey) for\b", safe, re.I):
        match = re.search(r"\bAccepted (?:password|publickey) for (\S+)", safe, re.I)
        account = match.group(1)[:256] if match else None
        action = "login success"
    elif AUTH_FAILURE_RE.search(safe):
        action = "login failure"
    if ip:
        try:
            ip = str(ipaddress.ip_address(ip))
        except ValueError:
            ip = None
    return Record(number, _timestamp(safe, year), event.source, event.service or "unknown",
                  (event.level or "unknown").upper(), safe,
                  account[:256] if account else None, ip, host[:256] if host else None, action)


def load_watchlist(path: Path | None):
    indicators = set()
    if path is None:
        return indicators
    if path.stat().st_size > 200_000:
        raise ValueError("Watchlist exceeds 200 KB")
    for item in iter_bounded_lines(path, 512):
        value = item.text.strip().lower()
        if not value or value.startswith("#"):
            continue
        if item.truncated:
            raise ValueError("Watchlist entry exceeds 512 bytes")
        try:
            value = str(ipaddress.ip_address(value))
        except ValueError:
            value = value.rstrip(".")
            if not re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", value):
                raise ValueError("Watchlist entries must be exact IP addresses or ASCII domains")
        indicators.add(value)
        if len(indicators) > 2000:
            raise ValueError("At most 2000 indicators are supported")
    return indicators


def observed_indicators(text: str):
    values = set()
    for token in re.findall(r"https?://[^\s\"'<>]+|[A-Za-z0-9_.:\[\]-]+", text):
        if token.startswith(("http://", "https://")):
            try:
                token = urlsplit(token).hostname or ""
            except ValueError:
                continue
        token = token.strip("[]().,;").lower()
        if re.fullmatch(r"[A-Za-z0-9.-]+:\d+", token):
            token = token.rsplit(":", 1)[0]
        try:
            values.add(str(ipaddress.ip_address(token)))
        except ValueError:
            if "." in token:
                values.add(token)
    return values


def extra_signals(records: list[Record], tuning: Tuning, indicators: set[str]):
    signals = []
    failures = defaultdict(list)
    for record in sorted((r for r in records if r.timestamp), key=lambda r: (r.timestamp, r.line)):
        if not record.account or not record.source_ip:
            continue
        key = (record.account, record.source_ip, record.host or "")
        stamp = parse_boundary(record.timestamp)
        if record.action == "login failure":
            failures[key].append(record)
        elif record.action == "login success":
            matches = [r for r in failures[key] if 0 <= (stamp - parse_boundary(r.timestamp)).total_seconds() <= tuning.login_window_seconds]
            if len(matches) >= tuning.login_failure_threshold:
                retained_matches = matches[-100:]
                evidence = f"account={record.account}; source={record.source_ip}; {len(matches)} preceding failures within {tuning.login_window_seconds}s; success={record.timestamp}; references=last {len(retained_matches)} failures + success; lines=" + ",".join(str(r.line) for r in retained_matches + [record])
                signals.append(Signal(Finding("HIGH", "authentication", "Successful login after repeated failures", evidence,
                    "Verify account ownership, approved access and surrounding activity. This sequence does not prove compromise."), tuple(r.line for r in retained_matches + [record])))
            failures[key] = []
    for record in records:
        matches = sorted(observed_indicators(record.evidence) & indicators)
        if matches:
            signals.append(Signal(Finding("HIGH", "indicator", "Supplied watchlist indicator observed",
                f"line={record.line}; indicators={','.join(matches)}; {record.evidence[:350]}",
                "Validate the supplied indicator's provenance and context; matching alone does not prove malicious activity."), (record.line,)))
        if record.action == "process created" and re.search(r"(?:powershell(?:\.exe)?\b.*(?:-enc(?:odedcommand)?\b|downloadstring\b)|certutil(?:\.exe)?\b.*-urlcache\b)", record.evidence, re.I):
            signals.append(Signal(Finding("HIGH", "process", "Process command line needs review", record.evidence[:500],
                "Validate the complete command line, initiating account and approved administrative activity."), (record.line,)))
    return signals


@dataclass
class Investigation:
    path: Path
    records: list[Record]
    signals: list[Signal]
    total_lines: int
    truncated_lines: int
    sampled_lines: int
    tuning: Tuning
    omitted_signals: int = 0

    def select(self, filters: Filters):
        filters.validate()
        since, until = parse_boundary(filters.since), parse_boundary(filters.until)
        candidates = []
        for record in self.records:
            stamp = parse_boundary(record.timestamp) if record.timestamp else None
            if filters.service and record.service.casefold() != filters.service.casefold():
                continue
            if filters.source and filters.source.casefold() not in {record.source.casefold(), str(self.path).casefold(), self.path.name.casefold()}:
                continue
            if (since or until) and (stamp is None or (since and stamp < since) or (until and stamp > until)):
                continue
            candidates.append(record)
        ids = {r.line for r in candidates}
        signals = [s for s in self.signals if set(s.lines) & ids
                   and (not filters.category or s.finding.category.casefold() == filters.category.casefold())
                   and (not filters.severity or s.finding.severity == filters.severity.upper())]
        if filters.category or filters.severity:
            matching = {n for s in signals for n in s.lines}
            candidates = [r for r in candidates if r.line in matching]
        return candidates, signals

    def dashboard(self, filters: Filters):
        records, signals = self.select(filters)
        findings = tuple(s.finding for s in signals if s.suppression_reason is None)
        events = tuple(parse_line(r.evidence) for r in records)
        return DashboardData(str(self.path), len(records), findings, tuple(score_events(events)), tuple(correlate(list(findings))),
            dict(Counter(r.level for r in records)), dict(Counter(r.service for r in records)),
            dict(Counter(f.category for f in findings)), dict(Counter(f.severity for f in findings)),
            events=events, raw_lines=tuple(r.evidence for r in records), sampled_lines=self.sampled_lines, truncated_lines=self.truncated_lines)


def investigate_file(path: Path, tuning: Tuning | None = None, indicators: set[str] | None = None, *, year: int | None = None):
    from collections import deque
    tuning = tuning or Tuning()
    retained = deque()
    size = total = truncated = 0
    for item in iter_bounded_lines(path, 16384):
        total += 1
        truncated += int(item.truncated)
        record = make_record(total, item.text, year)
        retained.append(record)
        size += len(record.evidence.encode("utf-8"))
        while len(retained) > 10000 or size > 8_000_000:
            size -= len(retained.popleft().evidence.encode("utf-8"))
    records = list(retained)
    state = AnalysisState(auth_window_seconds=tuning.login_window_seconds, timestamp_year_hint=year)
    for record in records:
        state.process(record.evidence)
    signals = []
    evidence_index = defaultdict(list)
    windows_index = defaultdict(list)
    for record in records:
        evidence_index[record.evidence[:500]].append(record.line)
        win = parse_windows_security_line(record.evidence)
        if win:
            signal = signal_for_event(win)
            if signal:
                windows_index[signal.evidence[:500]].append(record.line)
    for finding in state.findings():
        fragment = finding.evidence.split("latest=", 1)[-1]
        matches = tuple(evidence_index.get(fragment, windows_index.get(fragment, []))[-100:])
        if matches:
            signals.append(Signal(finding, matches))
    signals.extend(extra_signals(records, tuning, indicators or set()))
    tuned = []
    for signal in signals[:10000]:
        reason = next((e["reason"] for e in tuning.exceptions if e["category"].casefold() == signal.finding.category.casefold()
                       and e["contains"].casefold() in signal.finding.evidence.casefold()), None)
        tuned.append(replace(signal, suppression_reason=redact_sensitive(reason) if reason else None))
    return Investigation(path, records, tuned, total, truncated, total - len(records), tuning,
                         max(0, len(signals) - 10000) + state.dropped_findings)


def fingerprint(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
        after = os.fstat(handle.fileno())
    current = path.stat()
    def metadata(item):
        return item.st_size, item.st_mtime_ns, item.st_ctime_ns, item.st_ino
    if metadata(before) != metadata(after) or metadata(after) != metadata(current):
        raise ValueError("Source changed during fingerprinting; retry on a stable copy")
    return {"source": str(path.resolve()), "sha256": digest.hexdigest(), "size_bytes": after.st_size,
            "recorded_at": datetime.now(timezone.utc).isoformat()}


def record_integrity(path: Path, baseline: Path):
    if path.resolve() == baseline.resolve():
        raise ValueError("Baseline cannot overwrite source")
    payload = fingerprint(path)
    with os.fdopen(os.open(baseline, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return payload


def check_integrity(path: Path, baseline: Path):
    if baseline.stat().st_size > 10000:
        raise ValueError("Invalid integrity baseline size")
    saved = json.loads(baseline.read_text(encoding="utf-8"))
    if not isinstance(saved, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(saved.get("sha256", ""))):
        raise ValueError("Invalid SHA-256 baseline")
    current = fingerprint(path)
    if saved.get("source") != current["source"]:
        raise ValueError("Baseline belongs to another source path")
    return {"status": "UNCHANGED" if current["sha256"] == saved["sha256"] else "CHANGED",
            "baseline": saved, "current": current,
            "note": "A change can be normal log growth. Hashes are not signed proof of provenance."}


def export_evidence(investigation: Investigation, filters: Filters, output: Path):
    if output.resolve() == investigation.path.resolve():
        raise ValueError("Export cannot overwrite source")
    records, signals = investigation.select(filters)
    payload = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
               "source_fingerprint_at_export": fingerprint(investigation.path), "filters": asdict(filters),
               "total_source_lines": investigation.total_lines, "retained_lines": len(investigation.records),
               "sampled_lines": investigation.sampled_lines, "truncated_lines": investigation.truncated_lines,
               "omitted_signals": investigation.omitted_signals,
               "tuning": asdict(investigation.tuning), "events": [asdict(r) for r in records],
               "findings": [asdict(s) for s in signals],
               "note": "Redacted retained evidence, not a complete source copy. Suppressed findings remain included. Fingerprint is taken at export, not at analysis."}
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as handle:
        handle.write(redact_sensitive(json.dumps(payload, indent=2, ensure_ascii=False)))
    return output
