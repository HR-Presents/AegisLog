from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess  # nosec B404 - required for fixed, argument-list, read-only native collectors
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


class CollectorError(RuntimeError):
    """Raised when a native source cannot be read safely."""


@dataclass(frozen=True)
class NativeSource:
    name: str
    label: str
    available: bool
    detail: str


def _run(command: list[str], timeout: int = 15, include_stderr: bool = False) -> str:
    try:
        result = subprocess.run(  # nosec B603 - shell is never used; commands are constructed as argument lists
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CollectorError(str(exc)) from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "collector command failed").strip()
        raise CollectorError(detail[:500])
    return result.stdout + (result.stderr if include_stderr else "")


def _windows_timestamp(value: object) -> str:
    text = str(value or "").strip()
    match = re.fullmatch(r"/Date\((-?\d+)(?:[+-]\d{4})?\)/", text)
    if not match:
        return text
    try:
        stamp = datetime.fromtimestamp(int(match.group(1)) / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return text
    return stamp.isoformat(timespec="seconds").replace("+00:00", "Z")


def windows_event_logs(limit: int = 300, channel: str = "System", since_minutes: int | None = None) -> list[str]:
    if os.name != "nt":
        raise CollectorError("Windows Event Logs are only available on Windows")
    safe_channels = {"System", "Application", "Security"}
    if channel not in safe_channels:
        raise CollectorError("channel must be System, Application, or Security")
    count = max(1, min(int(limit), 2000))
    if since_minutes is not None and since_minutes not in {60, 1440, 10080}:
        raise CollectorError("unsupported time window")
    query = f"-FilterHashtable @{{LogName='{channel}'; StartTime=(Get-Date).AddMinutes(-{since_minutes})}}" if since_minutes else f"-LogName '{channel}'"
    script = (
        f"Get-WinEvent {query} -MaxEvents {count} -ErrorAction Stop | "
        "Sort-Object TimeCreated | ForEach-Object { "
        "$event = $_; [xml]$xml = $event.ToXml(); $fields = @{}; "
        "foreach ($data in $xml.Event.EventData.Data) { "
        "if ($data.Name) { $fields[[string]$data.Name] = [string]$data.'#text' } }; "
        "if ($xml.Event.UserData) { foreach ($data in $xml.Event.UserData.SelectNodes('.//*[not(*)]')) { "
        "$fields[[string]$data.LocalName] = [string]$data.InnerText } }; "
        "[pscustomobject]@{ TimeCreated=$event.TimeCreated.ToUniversalTime().ToString('o'); "
        "Id=$event.Id; Level=$event.Level; LevelDisplayName=$event.LevelDisplayName; Computer=$event.MachineName; "
        "ProviderName=$event.ProviderName; Message=$event.Message; EventData=$fields } "
        "} | ConvertTo-Json -Depth 5 -Compress"
    )
    try:
        raw = _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], timeout=30).strip()
    except CollectorError as exc:
        detail = str(exc)
        if since_minutes is not None and ("NoMatchingEventsFound" in detail or "No events were found" in detail):
            return []
        if channel == "Security" and (
            "UnauthorizedAccessException" in detail
            or "unauthorized operation" in detail.lower()
            or "access is denied" in detail.lower()
        ):
            raise CollectorError(
                "Windows Security Event Log access was denied. Reopen AegisLog with 'Run as administrator' "
                "only when you want to inspect this protected channel, then retry. No system settings were changed."
            ) from exc
        raise
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CollectorError("Windows returned invalid event data") from exc
    records = payload if isinstance(payload, list) else [payload]
    lines: list[str] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        timestamp = _windows_timestamp(item.get("TimeCreated"))
        level = {1: 'CRITICAL', 2: 'ERROR', 3: 'WARNING', 4: 'INFO', 5: 'VERBOSE'}.get(
            item.get('Level'), str(item.get("LevelDisplayName") or "INFO").upper()
        )
        provider = str(item.get("ProviderName") or "windows")
        event_id = str(item.get("Id") or "")
        message = " ".join(str(item.get("Message") or "").split())
        fields = item.get('EventData')
        fields = dict(fields) if isinstance(fields, dict) else {}
        if item.get('Computer'):
            fields['Computer'] = str(item['Computer'])
        if isinstance(fields, dict) and fields:
            message += ' | AEGIS_EVENT_DATA=' + json.dumps(fields, ensure_ascii=True, separators=(',', ':'))
        lines.append(f"{timestamp} {provider}[{event_id}]: {level} {message}\n")
    return lines


def journald_logs(limit: int = 300, since_minutes: int | None = None) -> list[str]:
    if platform.system() != "Linux":
        raise CollectorError("journald is only available on Linux")
    count = max(1, min(int(limit), 5000))
    if since_minutes is not None and since_minutes not in {60, 1440, 10080}:
        raise CollectorError("unsupported time window")
    command = ["journalctl", "--no-pager", "-n", str(count), "-o", "short-iso"]
    if since_minutes:
        command += ["--since", f"{since_minutes} minutes ago"]
    raw = _run(command, timeout=30)
    return [line + "\n" for line in raw.splitlines() if line.strip()]


def docker_logs(container: str, limit: int = 300) -> list[str]:
    name = container.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
        raise CollectorError("provide one Docker container name or ID")
    count = max(1, min(int(limit), 5000))
    raw = _run(["docker", "logs", "--timestamps", "--tail", str(count), name], timeout=30, include_stderr=True)
    lines = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        stamp, separator, message = line.partition(' ')
        if separator and re.match(r'^\d{4}-\d{2}-\d{2}T', stamp):
            lines.append(f'{stamp} docker.{name}: {message}\n')
        else:
            lines.append(f'docker/{name}: {line}\n')
    return lines


def _docker_status() -> NativeSource:
    if shutil.which("docker") is None:
        return NativeSource("docker", "Docker logs", False, "Docker CLI not found")
    try:
        _run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=5)
    except CollectorError:
        return NativeSource("docker", "Docker logs", False, "Docker CLI found; engine unavailable or access denied")
    return NativeSource("docker", "Docker logs", True, "Docker CLI and engine accessible")


def source_status() -> list[NativeSource]:
    system = platform.system()
    return [
        NativeSource("windows", "Windows Event Logs", system == "Windows", "System/Application/Security channels"),
        NativeSource("journald", "Linux journald", system == "Linux", "journalctl read-only snapshot"),
        _docker_status(),
    ]


def collect(source: str, *, limit: int = 300, channel: str = "System", container: str = "", since_minutes: int | None = None) -> list[str]:
    time_options = {"since_minutes": since_minutes} if since_minutes is not None else {}
    collectors: dict[str, Callable[[], list[str]]] = {
        "windows": lambda: windows_event_logs(limit=limit, channel=channel, **time_options),
        "journald": lambda: journald_logs(limit=limit, **time_options),
        "docker": lambda: docker_logs(container=container, limit=limit),
    }
    try:
        collector = collectors[source]
    except KeyError as exc:
        raise CollectorError(f"unknown native source: {source}") from exc
    return collector()
