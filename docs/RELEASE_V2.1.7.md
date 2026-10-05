# AegisLog v2.1.7

This release brings the approved terminal home layout, an optional beginner walkthrough, and the selected terminal-mark logo for README and reports.

- Home adapts to available height and keeps actions visible at the six checked laptop terminal sizes. Wide terminals retain the original ASCII logo; very small terminals retain scrolling.
- G Beginner explains workflow choices, asks before running an exact synthetic demo, explains results, and guides users to opening their first report. Back and Quit use existing navigation.
- README provides the whole-project overview and six workflow/architecture diagrams.
- Approved terminal-mark image appears in README, summary, full retained-evidence and folder reports. Terminal branding is unchanged.
- Logo is packaged and embedded into generated HTML so report branding works offline; the printed demo summary remains two pages in automated Chromium review.

Regenerate reports after updating: existing saved reports retain their original content. Source logs are handled read-only. Findings, incident grouping and rarity support review rather than proving an attack. Tests and detection evaluations use synthetic regression evidence; they do not establish real-world detection accuracy.

The Windows executable is unsigned. Published SHA-256 checksums and build provenance are separate from Authenticode signing. Previous releases remain available.

## Install or upgrade with pipx

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog/releases/download/v2.1.7/aegislog_ai-2.1.7-py3-none-any.whl"
aegislog --version
aegislog start
```

Use `py` instead of `python` when appropriate. Close and reopen the terminal after pipx PATH setup. Do not combine `--force` with `--pip-args="--force-reinstall"`.
