from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_TARGET = "e7af0798c731720690f298c093deec74f42fa56a"
EXE_SHA256 = "c16c944415bcd929c1b53588f60c3f920a3ca4abcc8923c745ca1594329c66a2"


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v217_is_current_published_stable() -> None:
    project_status = _text("docs/PROJECT_STATUS.md")
    roadmap = _text("docs/ROADMAP.md")
    docs_index = _text("docs/README.md")

    assert "current published stable release is **v2.1.7**" in project_status
    assert "**Published stable:** v2.1.7" in project_status
    assert "currently released as **v2.1.7**" in roadmap
    assert "v2.1.7 — current stable release" in roadmap
    assert "[v2.1.7 release notes](RELEASE_V2.1.7.md)" in docs_index


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
