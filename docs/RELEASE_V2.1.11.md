# AegisLog v2.1.11

This release packages the approved report redesign in the Windows executable, ZIP and Python wheel.

- White document pages, black text, light sea-blue boxes and side rules.
- Larger transparent AegisLog logo, aligned metrics and framed findings.
- Summary links to full retained evidence; original rule provenance and every retained finding reference remain available.
- UTC finding chronology, unmatched incident evidence, source SHA-256, retention statistics and parser/collection limits.
- Browser-expandable supporting distributions and rarity context; compact print explicitly notes their omission.
- Natural pagination for large evidence sets, with all 80 long finding references checked in a printed regression fixture.
- README report guidance and installation instructions updated.

The detection engine and read-only source handling are unchanged. Findings and grouped signals are investigation leads, not proof of compromise. Format recognition does not establish complete detection coverage. Rarity scores are sample statistics, not attack probabilities. The three-page training sample does not impose a page limit on real investigations.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog-AI/releases/download/v2.1.11/aegislog_ai-2.1.11-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.11-Windows.zip` and run `dist\AegisLog.exe start`.

Generate fresh reports after updating. Existing saved HTML/PDF files remain unchanged. Do not combine pipx `--force` with `--pip-args="--force-reinstall"`.

The Windows executable is unsigned and not Authenticode-signed. SHA-256 checksums and build provenance do not provide publisher signing. Independent real-world evaluation and broader device acceptance remain external work.

**MADE BY HR-PRESENTS**
