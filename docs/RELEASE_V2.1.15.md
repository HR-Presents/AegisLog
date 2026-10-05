# AegisLog v2.1.15

This release includes bounded baseline loading and the latest compatibility and validation improvements. The approved terminal and report designs remain unchanged.

- Enforce the 2 MB baseline limit during the read itself, before UTF-8/JSON decoding.
- Validate Python 3.10–3.14 on Linux and Python 3.14 Windows commands; check isolated installed wheels on Windows 3.10 and 3.14 in paths with spaces and Unicode characters.
- Extend terminal viewport regressions and show the existing Beginner action consistently in the full utility panel. Add a portable repeated streaming benchmark with processing, retention and source-integrity checks.
- Use exact count ratios for evaluation gates and disclose category-per-case metric scope and class balance.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog/releases/download/v2.1.15/aegislog_ai-2.1.15-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.15-Windows.zip` and run `dist\AegisLog.exe start`. Generate fresh reports after updating. Saved reports and source logs remain unchanged. Do not combine pipx `--force` with `--pip-args="--force-reinstall"`.

Free, local and terminal-first. No browser dashboard, paid service or remote AI dependency is added. The Windows executable is unsigned and not Authenticode-signed. SHA-256 checksums verify bytes, not publisher identity. Findings remain investigation leads rather than proof of compromise. Synthetic regression and hosted-runner usability checks do not establish independent real-world detection effectiveness or every physical-PC/terminal combination. Independent labeled validation and repository protection remain owner/external work.

Build commit: `00d2c688d7f97e1e192f7af2a509e2a0b638d292`. Executable SHA-256: `3f69333b68890ede08c409de731aeee702e85bf44a10f25752dfe2d4012003f1`. The [review manifest](../packaging/release-review.json) records all seven verified asset digests.

**MADE BY HR-PRESENTS**
