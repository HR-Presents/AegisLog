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
