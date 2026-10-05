# AegisLog v2.1.12

This maintenance release includes the repository audit fixes while preserving the approved terminal layout and report design.

- Prevent input sources from being overwritten by report sidecars, baselines or evidence outputs, including hard-link aliases.
- Use consistent incident IDs in reports and investigation commands.
- Keep yearless syslog timestamps unresolved unless an explicit year is supplied; preserve absolute investigation timestamps.
- Include local custom-rule findings in reports and disclose omitted findings.
- Distinguish same-named live sources and normalize known JSON log objects consistently across analysis modes.
- Bound legacy file readers, watch ingestion and recursive discovery.
- Correct issue templates, links and privacy/detection documentation; disable obsolete release jobs.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog-AI/releases/download/v2.1.12/aegislog_ai-2.1.12-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.12-Windows.zip` and run `dist\AegisLog.exe start`. Generate fresh reports after updating; saved HTML/PDF files remain unchanged. Do not add `--pip-args="--force-reinstall"` to pipx `--force`.

The Windows executable is unsigned and not Authenticode-signed. SHA-256 checksums verify bytes, not publisher identity. Detection and correlation remain deterministic investigation aids; findings do not prove compromise. Synthetic regression results do not establish real-world detection effectiveness. Branch protection, signing and independent real-world validation remain external work.

**MADE BY HR-PRESENTS**

Build commit: `b8ed619b8fc45da9099cb6a14ff0d923c8ebb0c7`

Executable SHA-256: `935f5a7380e2d7e134f6f7ca6b0bb44bf311d2d2d00556ce5ade3fad9032fb4f`

The exact seven-asset digest manifest is recorded in [release-review.json](../packaging/release-review.json). The release page includes matching checksum files.
