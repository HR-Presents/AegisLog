# AegisLog v2.1.9

This release packages the approved company-facing report design for Windows and Python installations.

- Specific opening assessment, concise observed evidence beside recommended reviews, and separate supporting activity and collection scope.
- Transparent AegisLog logo, black text, light sea-blue accents and MADE BY HR-PRESENTS closing credit.
- Five main full-report navigation choices; original detector rule labels appear only when presentation names differ.
- Compact technical appendix for source identity and retention statistics, with all retained evidence and stable references preserved.
- One synthetic-data notice, explicit timestamp limitations, Windows diagnostic cautions and severity-prioritized incident previews.

The summary is bounded; use the complete report for all retained evidence. Findings and incident groups are investigation leads, not proof of compromise or a shared cause. A result with no matching rules does not establish a clean system or complete collection. Detection rules and source handling are unchanged. Synthetic evaluations are regression evidence, not independent real-world accuracy measurements.

The Windows executable is unsigned and not Authenticode-signed. Checksums and build provenance do not provide publisher signing. Automated Windows checks do not replace final interactive acceptance on your computer.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog-AI/releases/download/v2.1.9/aegislog_ai-2.1.9-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.9-Windows.zip` and run `dist\AegisLog.exe start`. Generate new reports after updating; existing HTML/PDF files keep their old design. Source logs remain read-only.

Reopen the terminal after pipx PATH setup. Do not combine pipx `--force` with `--pip-args="--force-reinstall"`.

**MADE BY HR-PRESENTS**
