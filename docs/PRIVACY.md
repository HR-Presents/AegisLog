# Privacy model

Public AegisLog commands perform parsing, detection, correlation, rarity scoring and report generation locally. They do not send investigation evidence to an AI provider. Historical provider modules are not part of the supported public workflow.

Installation and explicitly requested update checks contact package or release hosts. Local analysis does not require these requests. Reports, case metadata, baselines and exported evidence are written to local storage; they can contain account names, addresses, paths and other sensitive identifiers.

Secret redaction is best effort, not a guarantee. Review exports before sharing. The aggregate sharing summary omits raw evidence and named identifiers, but counts can still disclose operational information. Preserve original logs under your own retention and access policies.
