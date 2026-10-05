# Detection coverage and interpretation

AegisLog is a free, local, read-only investigation tool. These are supported investigation signals, not guaranteed threat coverage. Format recognition is separate from detection recall.

| Signal | Current evidence scope | Important limitation |
|---|---|---|
| Authentication failure bursts | Source address and observed target host; explicit time window where resolved | Can aggregate different accounts on the same target; the displayed latest account is representative, not the entire target set |
| Failure followed by successful login | Workbench/live extra signals: same account, address and target host, configured threshold/window | Windows needs an explicit recording computer and timestamp zone; client workstation alone does not establish target identity |
| Successful Windows logon / process creation | 4624 / 4688 retained as INFO | Normal activity alone is not an escalation |
| Built-in service privileged logon | 4672 with service SIDs S-1-5-18/19/20 retained as INFO | Account name alone does not establish built-in identity; unexpected related activity still needs review |
| Security group membership change | 4728 / 4732, observed target group SID | Administrators and domain-relative 512/518/519 are HIGH; standard Users SID is INFO; other/missing SIDs remain MEDIUM pending privilege review |
| Account creation, lockout, audit clearing | Selected Windows event IDs with extracted fields | Authorization and collector completeness need separate verification |
| Selected suspicious process/web patterns | Pattern matches in retained messages or command lines | Workbench extras and core rules have distinct scope; authorized administration may also match |
| Suricata alerts | Recognized upstream alert signature/severity | Relays an IDS lead; does not inspect packets or independently validate the signature |
| Operational errors / Windows fault reports | Recognized error and report-submission records | Not automatically security events; repeated submissions need original failure timing |
| Rarity | Concerning event classes in retained sample | Not attack probability, confidence or independently trained ML |

## Correlation safeguards

Windows membership incidents preserve target group context. Authentication bursts separate observed target hosts even when the source IP matches. Workbench success sequences require the same account/address/target and resolved timestamps. Session context requires host plus logon ID; it stops at the next observed logon reusing that ID. Ambiguous same-time anchors are not assigned context. Missing/truncated/evicted evidence can limit every correlation.

Generic inputs with missing host or time context remain limited. Do not infer a same-host attack, elapsed-time burst or shared cause when the required fields are absent. Source-address bursts may represent several accounts; successful-login correlation is a narrower, account-specific signal.

## Confidence and severity

Stored legacy `confidence` fields remain compatible. Terminal confidence values are labeled heuristic scores out of 100. These scores are calculated from severity and available evidence/context; they are not calibrated probabilities. ATT&CK mappings are interpretive context, not proof that a technique occurred. INFO evidence remains retained rather than silently discarded.

## Evidence required for stronger claims

Synthetic fixtures test documented behavior and benign alternatives. They are not independent real-world validation. An external evaluation needs authorized labeled data, a documented sampling/labeling method, supported-source coverage, per-category false positives/misses, precision/recall with uncertainty, and a tested commit. No such external result is claimed by this change.

Microsoft references:

- [Windows security identifiers](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/understand-security-identifiers)
- [Event 4732: local group membership change](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4732)

The approved terminal and report designs, free distribution, and removed browser dashboard remain unchanged. New source changes do not modify previously published v2.1.12 downloads.
