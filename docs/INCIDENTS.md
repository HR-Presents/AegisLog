# Incident correlation

`aegislog incidents FILE` groups deterministic findings by category and assigns each group a stable short ID derived from its category and leading finding. The incident severity is the highest severity among grouped findings.

This is deliberately simple in V0.2. Future versions should correlate by time window, host, user, process, source address, service, and causal sequence, then persist incident state between runs.

## Consistent identity and retained scope

Report incident references and `incidents` / `investigate` use the same correlation IDs. Investigation timelines and entity views use bounded retained excerpts (up to 10,000 records and 8 MB), not a complete copy of arbitrarily large logs. Legacy baseline, behavior and indicator commands use similarly bounded recent samples. Heuristic confidence values are not calibrated attack probabilities.
