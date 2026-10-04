from __future__ import annotations

import re
from .safe_json import loads as safe_json_loads
from dataclasses import dataclass


WINDOWS_SECURITY_EVENT = re.compile(
    r"^(?P<timestamp>\S+)\s+Microsoft-Windows-Security-Auditing\[(?P<event_id>\d+)\]:\s+"
    r"(?P<level>\S+)\s*(?P<message>.*)$",
    re.IGNORECASE,
)

FIELD_PATTERNS = {
    "subject_sid": (re.compile(r"\b(?:Security ID|SubjectUserSid):\s*(?P<value>S-\d+(?:-\d+)+)\b", re.I),),
    "account": (
        re.compile(r"\bAccount Name:\s*(?P<value>[^\s]+)", re.IGNORECASE),
        re.compile(r"\bTarget User Name:\s*(?P<value>[^\s]+)", re.IGNORECASE),
        re.compile(r"\bNew Account Name:\s*(?P<value>[^\s]+)", re.IGNORECASE),
    ),
    "source_ip": (
        re.compile(r"\bSource Network Address:\s*(?P<value>[^\s]+)", re.IGNORECASE),
        re.compile(r"\bIpAddress:\s*(?P<value>[^\s]+)", re.IGNORECASE),
    ),
    "workstation": (
        re.compile(r"\bWorkstation Name:\s*(?P<value>[^\s]+)", re.IGNORECASE),
        re.compile(r"\bWorkstationName:\s*(?P<value>[^\s]+)", re.IGNORECASE),
    ),
    "process": (
        re.compile(r"\bNew Process Name:\s*(?P<value>.+?)(?=\s+(?:Token Elevation Type|Mandatory Label|Creator Process Name|Command Line):|$)", re.IGNORECASE),
    ),
}


@dataclass(frozen=True)
class WindowsSecurityEvent:
    event_id: int
    timestamp: str
    message: str
    account: str | None = None
    source_ip: str | None = None
    workstation: str | None = None
    process: str | None = None
    subject_sid: str | None = None
    actor_account: str | None = None
    logon_id: str | None = None
    host: str | None = None


@dataclass(frozen=True)
class SecuritySignal:
    severity: str
    category: str
    title: str
    evidence: str
    recommendation: str


EVENT_CONTEXT: dict[int, tuple[str, str, str, str]] = {
    4624: (
        "INFO", "authentication", "Windows successful logon recorded",
        "Validate the account and logon type; a successful logon alone does not establish unauthorized access.",
    ),
    4625: (
        "MEDIUM", "authentication", "Windows failed logon",
        "Review the target account, source address/workstation, logon type, and nearby successful logons.",
    ),
    4672: (
        "MEDIUM", "privilege", "Special privileges assigned to a new logon",
        "Confirm the privileged account and correlate this session with process creation and administrative activity.",
    ),
    4688: (
        "INFO", "process", "Windows process creation recorded",
        "Review the process path, parent process, account, and command line when process auditing is enabled.",
    ),
    4720: (
        "HIGH", "account", "Windows user account created",
        "Validate that the new account was authorized and review the actor, target account, and subsequent group membership changes.",
    ),
    4728: (
        "HIGH", "privilege", "Member added to a privileged/global security group",
        "Validate the membership change and review the initiating account and affected group.",
    ),
    4732: (
        "HIGH", "privilege", "Member added to a local security group",
        "Validate the local group membership change, especially for Administrators or other privileged groups.",
    ),
    4740: (
        "MEDIUM", "authentication", "Windows account lockout",
        "Review repeated failed logons for the locked account and correlate the caller computer or source system.",
    ),
    1102: (
        "CRITICAL", "audit", "Windows Security audit log was cleared",
        "Treat this as high-priority evidence: identify the account that cleared the log and preserve surrounding telemetry.",
    ),
}


def _field(message: str, name: str) -> str | None:
    for pattern in FIELD_PATTERNS[name]:
        match = pattern.search(message)
        if match:
            value = match.group("value").strip().strip(".,;")
            if value and value not in {"-", "::1", "127.0.0.1"}:
                return value
    return None


def parse_windows_security_line(line: str) -> WindowsSecurityEvent | None:
    match = WINDOWS_SECURITY_EVENT.match(line.strip())
    if not match:
        return None
    message = match.group("message").strip()
    event_id = int(match.group('event_id'))
    plain, marker, encoded = message.rpartition(' | AEGIS_EVENT_DATA=')
    fields = None
    if marker:
        try:
            candidate = safe_json_loads(encoded)
        except (ValueError, TypeError, RecursionError):
            pass
        else:
            if isinstance(candidate, dict):
                fields = candidate
                message = plain
    def value(name):
        raw = fields.get(name) if fields is not None else None
        return str(raw)[:512] if isinstance(raw, (str, int)) and str(raw) not in {'', '-'} else None
    targeted = event_id in {4624, 4625, 4720, 4740}
    account = value('TargetUserName' if targeted else 'SubjectUserName')
    if event_id in {4728, 4732}:
        account = value('MemberName') or value('MemberSid')
    return WindowsSecurityEvent(
        event_id=event_id,
        timestamp=match.group("timestamp"),
        message=message,
        account=account if fields is not None else _field(message, "account"),
        source_ip=value('IpAddress') if fields is not None else _field(message, "source_ip"),
        workstation=value('WorkstationName') if fields is not None else _field(message, "workstation"),
        process=value('NewProcessName') if fields is not None else _field(message, "process"),
        subject_sid=(value('SubjectUserSid') if fields is not None else _field(message, "subject_sid")) or None,
        actor_account=value('SubjectUserName'),
        logon_id=value('TargetLogonId' if event_id == 4624 else 'SubjectLogonId'),
        host=value('Computer'),
    )


def signal_for_event(event: WindowsSecurityEvent) -> SecuritySignal | None:
    context = EVENT_CONTEXT.get(event.event_id)
    if context is None:
        return None
    severity, category, title, recommendation = context
    if event.event_id == 4672 and event.subject_sid in {"S-1-5-18", "S-1-5-19", "S-1-5-20"}:
        severity = "INFO"
        title = "Built-in service account privileged logon"
        recommendation = "Retained baseline evidence for a built-in service SID. Review unexpected privileges and related logon/process activity; this event alone does not indicate compromise."
    parts = [f"Event ID {event.event_id}"]
    if event.subject_sid:
        parts.append(f"subject_sid={event.subject_sid}")
    if event.account:
        parts.append(f"account={event.account}")
    if event.actor_account:
        parts.append(f"actor_account={event.actor_account}")
    if event.source_ip:
        parts.append(f"source_ip={event.source_ip}")
    if event.workstation:
        parts.append(f"workstation={event.workstation}")
    if event.process:
        parts.append(f"process={event.process}")
    parts.append(event.message[:300])
    evidence = f'{event.timestamp} Microsoft-Windows-Security-Auditing[{event.event_id}]: INFO ' + ' | '.join(parts)
    return SecuritySignal(severity, category, title, evidence, recommendation)
