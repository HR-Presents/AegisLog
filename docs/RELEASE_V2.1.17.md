# AegisLog v2.1.17

This release packages the merged final-audit safeguards. Existing report appearance, built-in detection rules, logo, terminal navigation and free local operation are preserved.

- Enforce the whole-JSON buffer budget during reading, including files that grow after the initial size check. Oversized containers continue through line-oriented parsing without dropping buffered records or breaking the source hash.
- Bound custom rule-pack reads to 1 MB, 32 files, 100 rules per pack and 200 rules total, with JSON nesting limits and atomic rejection of invalid packs.
- Reject custom regex groups, repetition, lookarounds and backreferences before execution. Literals, anchors, classes, dot tokens, alternatives and escaped metacharacters remain supported. Existing custom packs using rejected syntax must be rewritten; built-in detectors are unaffected. Use `--no-plugins` to exclude custom packs.
- Refresh current resource-limit and branch-protection documentation.

Validation includes 689 passing regression tests, including growing-file hashing, custom-rule rejection, supported syntax, nesting, pack limits and atomic loading. Synthetic detection evaluation checks regression consistency; it does not establish real-world accuracy. Hosted Windows and package checks verify supported installation and command flows, not every physical screen or terminal setup.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog/releases/download/v2.1.17/aegislog_ai-2.1.17-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.17-Windows.zip` and run `dist\AegisLog.exe start`. Do not combine pipx `--force` with `--pip-args="--force-reinstall"`. Generate fresh reports after updating; previously saved reports remain unchanged.

The Windows executable remains unsigned. Verify the matching release SHA-256 checksums; checksums identify bytes, not publisher identity. No browser dashboard, paid service, remote AI dependency, automatic remediation or host permission bypass is added. Findings remain investigation leads, not proof of compromise.

Build commit: `63448e60ab2c905355d6dda8bab2837a7a106058`. Executable SHA-256: `4f22fb571cd47935c24e8a8ce7a3089f35caf8f715aefdac3454483a4f21d22f`. The [review manifest](../packaging/release-review.json) records all seven asset digests.

**MADE BY HR-PRESENTS**
