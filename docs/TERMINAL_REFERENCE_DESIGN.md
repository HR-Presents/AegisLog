# Terminal reference design

The development dashboard follows the supplied terminal references: black/dark surface, thin neutral borders, cyan section headings, mint activity/status bars, coral/red event sparklines, and orange warning values. Warm colours indicate severity; charts use observed telemetry only.

Analysis and live monitoring show horizontal distributions, vertical minute-activity bars, a compact sparkline, and a dot plot of the same counts. Timestamp offsets are normalized to UTC before minute grouping. All activity charts describe retained timestamped telemetry; missing timestamps do not become fabricated activity.

Wide terminals place related distributions beside each other. Narrow terminals stack sections. Unicode-capable colour terminals use filled blocks; non-colour/text rendering has ASCII fallbacks. Live signal sparklines show twelve arrival-time buckets with current/baseline rates alongside them. Gauges label elevated-finding share and rolling-window capacity explicitly; neither is a claim of compromise.

The home menu preserves existing command shortcuts and shows actual report/config paths. It cannot report host CPU, RAM, temperature or weather because those metrics are not collected by this product.

## Windows acceptance

No new stable release is implied by this development change. Build the Windows PR artifact and review home, analysis, live and multi-source views at 80, 120 and 180 columns. Check colour rendering, font glyphs, source paths, findings, Ctrl+C exit and resizing. Compare against the supplied references and preserve screenshots only after verifying the build/commit. Current historical v2.1.3 visual acceptance status remains unchanged until this review is complete.

## Rendered development previews

These images render the actual Rich output using a synthetic QA fixture. They are layout previews, not real Windows screenshots or real operational findings.

![Home layout](assets/screenshots/reference-home-qa.png)
![Analysis layout](assets/screenshots/reference-analysis-qa.png)
![Live layout](assets/screenshots/reference-live-qa.png)

## Interactive navigation

The `start` shell redraws its UTC clock every second while preserving typed menu input. Short terminals use a compact home so input controls stay visible; resizing redraws the layout. Select a menu number or command and press Enter.

Input workspaces accept `b`/`back` to return and `q`/`quit` to close, including profile and native-source choice prompts. Completed pages show Back and Quit controls. File analysis offers `r`/`refresh` to reread the source and regenerate its HTML report. Saved-file charts show recorded event times and do not invent new activity.

File, multi-source, and native live monitors accept B or Escape to stop/back, Q to quit, and Ctrl+C to stop safely. A terminal keyboard is required for single-key controls; redirected input retains Ctrl+C handling. Live views refresh their clock and telemetry at the configured polling interval; new findings depend on newly collected events. No source file or host setting is changed.

Keyboard checks cover editing, choice-prompt cancellation, immediate monitor interruption, and static refresh. Actual Windows font, colour, keyboard and resizing acceptance still requires the packaged build.
