# AegisLog Windows build

Extract the entire ZIP. Open PowerShell in the extracted folder:

```powershell
.\dist\AegisLog.exe start
```

The home uses terminal dimensions. Maximize the window or reduce the terminal font size to see more panels. PgUp/PgDn scroll, Home/End jump, 09 opens Help, Q quits. Live views accept B or Escape to stop and Q to quit.

## Included demo

The `demo` folder contains a synthetic log, exact indicator watchlist and detection tuning. Start an interactive investigation:

```powershell
.\dist\AegisLog.exe security .\demo\security-demo.log --interactive --watchlist .\demo\watchlist-demo.txt
```

D shows finding evidence and recommendations. T shows the account timeline. F filters; X clears filters. C loads `demo/tuning-demo.json`. V shows scope and suppressions. E creates a new JSON export; O opens the HTML report. P replays the selected file. R refreshes. B returns; Q quits.

From home, P opens built-in demo replay immediately. This is recorded sample activity, not a live collector.

## Acceptance walkthrough

1. Resize between a short laptop window and a maximized window. Confirm the logo, panels, controls and typed input remain usable.
2. Analyze the demo (01), monitor it (02), and inspect multiple source copies (03). Live rates fall when no new events arrive.
3. Inspect native logs (04) and native monitoring (05); unavailable sources should explain the reason. Access depends on OS permissions and Docker availability.
4. Open incidents (06), demo (07), health (08), and Help (09). Test Back and Quit in each workflow.
5. Verify D/T/F/E/O in the security workbench, and compare source line references against the demo log.

Reports and exports are local. Rolling retention and displayed chart slices are labelled. Findings require investigation; they are not proof of compromise.

This is a development build of version 2.1.4. Its build status and source commit are available in the linked GitHub workflow. The checksum file applies to `dist/AegisLog.exe`.

## Guided investigations

From the terminal home, choose **C Check Computer** to discover readable native sources and select the last hour, 24 hours or 7 days. Known log files are analyzed in full. Choose **F Scan Folder** for file discovery and a batch overview, and **R Reports** to open saved HTML reports. Q returns to your terminal.

From PowerShell: `AegisLog.exe check-computer`. Reports remain on disk after quitting.
