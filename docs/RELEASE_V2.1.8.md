# AegisLog v2.1.8

This release publishes the editorial investigation report redesign and synchronized terminal documentation.

- Larger approved transparent logo, black body text, light sea-blue accents, and a restrained report header.
- Clear assessment, compact metrics strip, distinct evidence/next-action sections, and MADE BY HR-PRESENTS closing credit.
- Direct counts for small samples and UTC timelines only when resolved retained timestamps support them; gaps and missing-time limits are disclosed.
- Larger supporting print text and PDF guards against an orphan closing signature.
- Updated README, installation, user guide, report guide, and branding; obsolete AI Analyst menu instructions removed.
- Existing terminal workflows and the removal of the D browser dashboard are preserved.

Generate a new report after updating. Existing saved HTML/PDF files do not change. Source logs remain read-only. Findings and incident groups require review; they do not prove compromise or a shared cause. Synthetic evaluations are regression evidence, not independently measured real-world detection accuracy.

The Windows executable is unsigned and not Authenticode-signed. Checksums and build provenance are separate from publisher signing. Automated Windows smoke tests do not replace final interactive acceptance on your computer.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog/releases/download/v2.1.8/aegislog_ai-2.1.8-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

For Windows without Python, extract the release ZIP and run `dist\AegisLog.exe start`. Reopen the terminal after pipx PATH setup. Do not combine pipx --force with --pip-args="--force-reinstall".

**MADE BY HR-PRESENTS**
