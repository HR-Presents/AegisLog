# Your first AegisLog investigation

AegisLog reads logs locally, highlights rule-backed investigation leads, and creates an HTML summary plus a full evidence report. It does not change the source or repair your computer.

## 1. Install and open

**Windows without Python:** [download the Windows ZIP](https://github.com/HR-Presents/AegisLog-AI/releases/download/v2.1.16/AegisLog-v2.1.16-Windows.zip), extract it, and open `AegisLog.exe`. The executable is currently unsigned; verify the release checksum before running it.

**Python 3.10 or newer:** use these commands in your terminal. On Windows, use `python` when it works; substitute `py` if that is your installed launcher.

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
python -m pipx install "https://github.com/HR-Presents/AegisLog-AI/releases/download/v2.1.16/aegislog_ai-2.1.16-py3-none-any.whl"
```

Close the terminal and open a new one so PATH updates take effect:

```powershell
aegislog --version
aegislog start
```

If Windows still cannot find the command, run `& "$env:USERPROFILE\.local\bin\aegislog.exe" start` in PowerShell. See [installation and troubleshooting](INSTALL.md) for other setups.

## 2. Analyze the demo

[Download the demo pack](https://github.com/HR-Presents/AegisLog-AI/raw/refs/heads/main/docs/demo/AegisLog-First-Investigation-Demo.zip) and extract it. Select **01 Analyze**, then drag `first-investigation.log` into the prompt or paste its full path.

Expect **9 records, 9 recognized records, 2 findings and 1 incident group**: one HIGH authentication burst containing six failures, and one MEDIUM operational timeout. These are synthetic training signals, not observations about your computer. Read the pack's README and expected-results.json.

For a quick check without downloading anything, select **07 Demo**. That separate built-in fixture has 7 records and omits timestamp years; its results differ from this pack.

## 3. Open and understand the report

Select **O Reports** when offered, or return home and press **R Reports**. Open the generated summary in your browser, then follow its full investigation link for retained evidence and collection limits. Keep both HTML files in the same folder.

Read the recommendation beside each finding. Findings require context; an incident group does not establish a shared cause. For a PDF, use the report's print button and turn off browser headers and footers.

## 4. Try your own source

Select **01** for an existing text log, **F** to discover files in a folder, or **C Check Computer** for accessible native sources. Review recognized-record counts and collection limits. Security Event Logs may require administrator access; ordinary file analysis does not.

For live monitoring, choose **02** and a growing log. Static demo files do not produce new events by themselves. B or Escape stops a live view; Ctrl+C also stops live monitoring.

## 5. Return to your terminal

Press **B** to return, then **Q** at home to quit. Your normal terminal prompt returns. AegisLog is not installed as a background service by this guide.

[Command reference](COMMANDS.md) · [Detection rules](RULES.md) · [First-user checklist](FIRST_USER_CHECKLIST.md)
