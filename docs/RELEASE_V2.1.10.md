# AegisLog v2.1.10

This release packages the investigation and support improvements while preserving the approved terminal and report designs.

- Grouped review with first/last retained occurrence times, explanations, alternatives and recommended next steps.
- Explicit host/logon-ID/time-bounded Windows session context and informational successful logon records.
- Docker json-file and ECS application message adapters; unknown schemas remain visibly unrecognized.
- Search newly saved cases by source, finding title, severity or date and reopen reports.
- Static/folder processing counts and cancellation polling during oversized line discard.
- Baseline detector labels classified as newly observed, recurring or not observed in the current sample.
- Complete aggregate sharing preview before saving, runtime-only diagnostics and opt-in GitHub update checks.
- Extended regression tests, static benchmarks and Windows executable command checks.

Context links and sample differences do not establish compromise, shared cause or incident resolution. Format recognition does not establish complete detection coverage. Maintained synthetic evaluations are regression evidence, not independent real-world accuracy measurements. Case metadata and private baselines contain identifiers. The sharing copy omits identifiers, but aggregate counts can remain sensitive.

The Windows executable is unsigned and not Authenticode-signed. Checksums and provenance do not provide publisher signing. Independent evaluation and broader device acceptance remain external work.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog/releases/download/v2.1.10/aegislog_ai-2.1.10-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.10-Windows.zip` and run `dist\AegisLog.exe start`.

New commands: `review <path>`, `cases --query <text>`, `diagnostics --output support.json` and `update-check`. The update check contacts GitHub only when requested, sends no logs or configuration, and never installs automatically. See [workflow guidance](INVESTIGATION_WORKFLOWS.md) for limits and examples.

Generate new reports and activity baselines to use indexing and signal comparisons; existing files remain unchanged. Reopen the terminal after pipx PATH setup. Do not combine pipx `--force` with `--pip-args="--force-reinstall"`.

**MADE BY HR-PRESENTS**
