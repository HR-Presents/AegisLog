from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_TARGET = "1eb0a4a4124599544b3608eb84582979770e4a04"
EXE_SHA256 = "c16c944415bcd929c1b53588f60c3f920a3ca4abcc8923c745ca1594329c66a2"


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_current_published_stable() -> None:
    project_status = _text("docs/PROJECT_STATUS.md")
    roadmap = _text("docs/ROADMAP.md")
    docs_index = _text("docs/README.md")

    assert "current published stable release is **v2.1.14**" in project_status
    assert "**Published stable:** v2.1.14" in project_status
    assert "currently released as **v2.1.14**" in roadmap
    assert "v2.1.14 — current stable release" in roadmap
    assert "[v2.1.14 release notes](RELEASE_V2.1.14.md)" in docs_index


def test_v216_release_target_and_checksum_are_recorded() -> None:
    project_status = _text("docs/PROJECT_STATUS.md")

    assert RELEASE_TARGET in project_status
    assert EXE_SHA256 in project_status
    assert "v2.1.6" in project_status
    assert "AegisLog.exe.sha256" in project_status


def test_v216_keeps_security_and_evidence_boundaries() -> None:
    project_status = _text("docs/PROJECT_STATUS.md")
    roadmap = _text("docs/ROADMAP.md")

    assert "unsigned" in project_status.lower()
    assert "synthetic regression evidence" in project_status.lower()
    assert "real-world" in roadmap.lower()
    assert "AI Analyst" in project_status


def test_current_release_identity_matches_publication_guard() -> None:
    import re
    status = _text("docs/PROJECT_STATUS.md")
    version = re.search(r'current published stable release is \*\*(v[\d.]+)\*\*', status).group(1)
    line = next(line for line in status.splitlines() if line.startswith(f'The {version} build target is '))
    commit, checksum = re.findall(r'`([a-f0-9]{40}|[a-f0-9]{64})`', line)
    import json
    manifest = json.loads(_text('packaging/release-review.json'))
    if manifest['tag'] == version:
        assert manifest['commit'] == commit
        assert manifest['assets']['AegisLog.exe'] == f'sha256:{checksum}'
    else:
        # A reviewed draft can precede publication; stable links must not move early.
        source_version = re.search(r'__version__ = "([\d.]+)"', _text('src/aegislog/__init__.py')).group(1)
        assert manifest['tag'] == f'v{source_version}'
        assert tuple(map(int, source_version.split('.'))) > tuple(map(int, version[1:].split('.')))
        assert f"# AegisLog {manifest['tag']}" in _text(f'docs/RELEASE_V{source_version}.md')
        assert re.fullmatch(r'[a-f0-9]{40}', manifest['commit'])
        assert re.fullmatch(r'sha256:[a-f0-9]{64}', manifest['assets']['AegisLog.exe'])
