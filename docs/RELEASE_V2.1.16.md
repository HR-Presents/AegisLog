# AegisLog v2.1.16

This release delivers the approved native-report corrections through the normal Windows and Python downloads.

- Preserve the native collection time window, returned count and count-limit warning in both the investigation summary and complete evidence report.
- Let supporting context flow after findings rather than forcing a mostly empty overflow page. A Chromium print regression verifies a synthetic 300-record, four-finding, three-group report fits two A4 pages with all groups and scope preserved. Other data and print settings may require more pages.
- Explain explicit Volsnap Event 36 shadow-copy storage-limit observations with specific review guidance. Original detector titles and retained evidence remain preserved.
- Keep the approved logo, black text, sea-blue boxes, side-by-side evidence and maker signature. Remove redundant collection/empty-incident wording.

## Install or upgrade

```powershell
python -m pipx install --force "https://github.com/HR-Presents/AegisLog/releases/download/v2.1.16/aegislog_ai-2.1.16-py3-none-any.whl"
aegislog --version
aegislog doctor
aegislog start
```

Without Python, extract `AegisLog-v2.1.16-Windows.zip` and run `dist\AegisLog.exe start`. Generate a fresh report after updating. Saved reports are unchanged. In the PDF print dialog, use A4, 100% scale and turn off browser Headers and footers. Do not combine pipx `--force` with `--pip-args="--force-reinstall"`.

Free, local and terminal-first. No browser dashboard, paid service or remote AI dependency is added. The Windows executable is unsigned and not Authenticode-signed. SHA-256 checksums verify bytes, not publisher identity. Findings remain investigation leads rather than proof of compromise. Synthetic regression and hosted-runner usability checks do not establish independent real-world detection effectiveness or every physical-PC/terminal combination. Independent labeled validation and repository protection remain owner/external work.

Build commit: `f511c971ca19bfb3560a65c1f3681ff3a9b1ace5`. Executable SHA-256: `632675414cbb4720152bcab403f944f990b0d32d5facf796e41094635a710a91`. The [review manifest](../packaging/release-review.json) records all seven verified asset digests.

**MADE BY HR-PRESENTS**
