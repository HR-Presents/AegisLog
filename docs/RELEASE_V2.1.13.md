# AegisLog v2.1.13

This release improves Windows detection precision and evidence correlation while preserving the approved terminal and report designs.

- Classify group membership changes using explicit group SIDs; retain standard Users changes as informational evidence and disclose unknown privilege scope.
- Separate authentication bursts by observed target host. Windows failure-to-success sequences require an explicit recording computer and timezone.
- Stop session context at the next reuse of a logon ID; skip ambiguous duplicate anchors.
- Present confidence as an uncalibrated heuristic score, not attack probability.
- Document actual detection scope in [Detection coverage](DETECTION_COVERAGE.md).

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog/releases/download/v2.1.13/aegislog_ai-2.1.13-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.13-Windows.zip` and run `dist\AegisLog.exe start`. Generate fresh reports after updating. Saved reports and source logs remain unchanged. Do not combine pipx `--force` with `--pip-args="--force-reinstall"`.

Free, local and terminal-first. No browser dashboard, paid service or remote AI dependency is added. The Windows executable is unsigned and not Authenticode-signed. SHA-256 checksums verify bytes, not publisher identity. Findings remain investigation leads rather than proof of compromise. Synthetic regression results do not establish real-world detection effectiveness; independent labeled validation remains outstanding.

**MADE BY HR-PRESENTS**

Build commit: `47561ba2d6c4089bffd94279668de729ed161a39`

Executable SHA-256: `d32c1d0d3f9bc812b986ca5de6c91cce7c8ffefd5310d49eda0dc3d2d7c02f8a`

The exact seven-asset digest manifest is recorded in [release-review.json](../packaging/release-review.json).
