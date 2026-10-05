# AegisLog v2.1.14

This release bundles evidence-grouping, privacy and live-monitor reliability fixes while preserving the approved terminal and report designs.

- Keep changes to different Windows target groups separate in terminal triage and report presentation groups; preserve all evidence references.
- Redact separator and camel-case variants of sensitive JSON keys, including nested objects and arrays. Credential redaction remains best-effort, not anonymization.
- Read live file identity, prefix and content through one handle to avoid mixing rotated file generations. Handle disappearance at open as a missing source. Concurrent in-place writes are not atomic snapshots.
- Reject baseline comparisons with different native collection windows or event limits. Different returned counts remain comparable when settings match.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog-AI/releases/download/v2.1.14/aegislog_ai-2.1.14-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.14-Windows.zip` and run `dist\AegisLog.exe start`. Generate fresh reports after updating. Saved reports and source logs remain unchanged. Do not combine pipx `--force` with `--pip-args="--force-reinstall"`.

Free, local and terminal-first. No browser dashboard, paid service or remote AI dependency is added. The Windows executable is unsigned and not Authenticode-signed. SHA-256 checksums verify bytes, not publisher identity. Findings remain investigation leads rather than proof of compromise. Synthetic regression results do not establish real-world detection effectiveness; independent labeled validation remains outstanding.

**MADE BY HR-PRESENTS**
