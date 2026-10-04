"""Verify public demo expectations and build a reproducible downloadable pack."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import tempfile
import zipfile

from aegislog.dashboard import analyze_dashboard
from aegislog.reporting import write_html_report


def build(source: Path, output: Path) -> str:
    expected = json.loads((source / "expected-results.json").read_text(encoding="utf-8"))
    for name, case in expected["cases"].items():
        path = source / name
        before = path.read_bytes()
        data = analyze_dashboard(path)
        actual = {
            "records": data.records,
            "recognized": data.recognized_records,
            "findings": len(data.findings),
            "incidents": len(data.incidents),
            "severities": data.severities,
            "titles": sorted(item.title for item in data.findings),
        }
        if actual != case:
            raise ValueError(f"{name}: expected {case}, got {actual}")
        if data.source_sha256 != hashlib.sha256(before).hexdigest():
            raise ValueError(f"{name}: source digest mismatch")
        with tempfile.TemporaryDirectory() as directory:
            report = write_html_report(data, Path(directory))
            appendix = report.with_name(report.stem + "-appendix.html")
            if not report.is_file() or not appendix.is_file():
                raise ValueError("Summary or full report missing")
            full = appendix.read_text(encoding="utf-8")
            for title in case["titles"]:
                if title not in full:
                    raise ValueError(f"Missing retained rule title: {title}")
        if path.read_bytes() != before:
            raise ValueError(f"{name}: source was modified")
        print(f"Verified {name}: {actual}")
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(["README.md", "expected-results.json", *expected["cases"]]):
            info = zipfile.ZipInfo("AegisLog-First-Investigation-Demo/" + name, (2026, 10, 4, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (source / name).read_bytes())
    content = payload.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    name = "AegisLog-First-Investigation-Demo.zip"
    (output / name).write_bytes(content)
    (output / (name + ".sha256")).write_text(f"{digest}  {name}\n", encoding="ascii")
    committed = source / name
    if committed.exists() and committed.read_bytes() != content:
        raise ValueError("Committed demo ZIP differs from verified sources")
    checksum = source / (name + ".sha256")
    if checksum.exists() and checksum.read_text(encoding="ascii") != f"{digest}  {name}\n":
        raise ValueError("Committed demo checksum differs")
    (output / "blob.json").write_text(json.dumps({
        "encoding": "base64", "content": base64.b64encode(content).decode("ascii"),
    }), encoding="ascii")
    print(f"DEMO_SHA256={digest}")
    return digest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("docs/demo"))
    parser.add_argument("--output", type=Path, default=Path("out/demo"))
    args = parser.parse_args()
    build(args.source, args.output)
