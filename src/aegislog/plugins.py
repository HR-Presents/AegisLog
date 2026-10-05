from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import config_dir
from .engine import Finding
from .safe_json import loads as safe_json_loads

MAX_PACK_BYTES = 1_000_000
MAX_PACKS = 32
MAX_RULES_PER_PACK = 100
MAX_RULES = 200


def _validate_pattern(pattern: str) -> None:
    """Allow fixed-width regex tokens; reject backtracking repetition constructs."""
    escaped, in_class = False, False
    for char in pattern:
        if escaped:
            if char.isdigit():
                raise ValueError("custom patterns cannot contain backreferences")
            escaped = False
        elif char == "\\":
            escaped = True
        elif in_class:
            if char == "]":
                in_class = False
        elif char == "[":
            in_class = True
        elif char in "()*+?{":
            raise ValueError("custom patterns support literals, anchors, classes and alternatives; repetition and groups are disabled")



@dataclass(frozen=True)
class PluginRule:
    id: str
    severity: str
    category: str
    title: str
    pattern: re.Pattern[str]
    recommendation: str
    source: str


def plugin_dir() -> Path:
    path = config_dir() / "rules.d"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _compile_rule(raw: dict, source: str) -> PluginRule:
    required = {"id", "severity", "category", "title", "pattern", "recommendation"}
    missing = required - raw.keys()
    if missing: raise ValueError(f"{source}: missing rule fields: {', '.join(sorted(missing))}")
    severity = str(raw["severity"]).upper()
    if severity not in {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}: raise ValueError(f"{source}: invalid severity {severity}")
    pattern = str(raw["pattern"])
    if len(pattern) > 500: raise ValueError(f"{source}: rule pattern is too long")
    _validate_pattern(pattern)
    return PluginRule(str(raw["id"]), severity, str(raw["category"]), str(raw["title"]), re.compile(pattern, re.I), str(raw["recommendation"]), source)


def load_rules(directory: Path | None = None) -> tuple[list[PluginRule], list[str]]:
    """Load declarative JSON rule packs. Plugins are data, not executable code."""
    root = directory or plugin_dir(); rules: list[PluginRule] = []; errors: list[str] = []
    for index, path in enumerate(root.glob("*.json")):
        if index >= MAX_PACKS:
            errors.append(f"rule pack limit reached ({MAX_PACKS}); additional packs were not loaded")
            break
        try:
            with path.open('rb') as handle:
                content = handle.read(MAX_PACK_BYTES + 1)
            if len(content) > MAX_PACK_BYTES:
                raise ValueError(f"rule pack exceeds {MAX_PACK_BYTES} bytes")
            payload = safe_json_loads(content.decode('utf-8'))
            raw_rules = payload.get("rules") if isinstance(payload, dict) else payload
            if not isinstance(raw_rules, list):
                raise ValueError("rule pack must be a list or contain a 'rules' list")
            if len(raw_rules) > MAX_RULES_PER_PACK or len(rules) + len(raw_rules) > MAX_RULES:
                raise ValueError("rule count limit exceeded (100 per pack, 200 total)")
            pending = []
            for item in raw_rules:
                if not isinstance(item, dict):
                    raise ValueError("every rule must be an object")
                pending.append(_compile_rule(item, path.name))
            rules.extend(pending)
        except (OSError, ValueError, RecursionError, re.error) as exc:
            errors.append(f"{path.name}: {exc}")
    return rules, errors


class RuleFindings(list):
    """Retained custom findings with an explicit omission count."""
    omitted = 0


def apply_rules(lines: list[str], rules: list[PluginRule]) -> list[Finding]:
    from .sanitize import redact_sensitive
    findings = RuleFindings()
    for raw in lines:
        line = redact_sensitive(raw.strip())
        if not line:
            continue
        for rule in rules:
            if not rule.pattern.search(line):
                continue
            if len(findings) >= 5000:
                findings.omitted += 1
            else:
                findings.append(Finding(rule.severity, rule.category, rule.title, line[:500], rule.recommendation))
    return findings
