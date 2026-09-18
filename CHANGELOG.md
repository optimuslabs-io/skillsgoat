# Changelog

Notable changes to SkillsGoat. Dates are release dates.

## 0.4.0 - 2026-09-18

Three new attack families and one scanner added to the ledger. The collection grows from 76 to 87 single-skill fixtures and from 35 to 37 compound chains.

### Added

- **Provenance and time (V14, V15, and a temporal sleeper).** Attacks where the file a scanner reads is not the code that runs:
  - Reconstruction-from-reference: the skill tells the agent to rebuild it from an external link, so nothing installs for a scanner to see.
  - Out-of-band distribution: a raw `git clone` or a hand-dragged folder skips the marketplace scan.
  - Time-delayed sleeper: benign when reviewed, then fetches and runs a payload after a set date.
- **Skills over MCP (V16).** Skills served over MCP Resources under SEP-2640, now Final: a dynamic-body sleeper whose review fetch and run fetch return different code, and an `allowed-tools` request that widens host permissions over the MCP origin. Threat model in `docs/THREAT_MODEL_MCP_SKILLS.md`.
- Mondoo SkillCheck in the scanner ledger, with a note on why a hash-reputation scanner reads every fixture it has not ingested as clean.
- A benign twin for each new family, so the false-positive rate stays measurable.

### Fixed

- The reconstruction, temporal, and dynamic fixtures no longer print their payload in the scanned file, so each one matches its own answer key (raised in Copilot review).
- The `--index-only` and `--goat` linkers work again; the package stopped hiding `discover_entries` and `discover_chains`.

## 0.3.0 - 2026-09-09

First public release. 76 single-skill fixtures (66 malicious, 10 benign) and 35 compound chains, each labeled with the correct verdict. Scanning runs blind by default, so a scanner cannot pass by reading the label. Every payload is inert.
