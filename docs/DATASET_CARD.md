# Dataset Card — SkillsGoat collection (v1)

**Version:** 0.4.1 (Phase 2.5)
**Collection:** `pasture/` — 101 atomic entries + 39 compound chains
**License:** MIT (see LICENSE)

## Intended use
Benchmarking AI agent-skill scanners (static + LLM) against labeled ground
truth. Scores are citable only when produced via `goat scan --blind`
(`blind: true`).

## Labels
- `verdict`: `malicious` | `benign` (future: `suspicious`)
- `categories`: slugs from `taxonomy.yaml`
- `severity`: low|medium|high|critical (omitted for benign)
- `maps`: OWASP AST10 / SkillSpector / V-codes
- Phase 0 fields: `lifecycle_stage`, `attack_vs_posture`, `injection_sites`,
  `risk_tier`
- Phase 2.5 field: `label_provenance` — `maintainer-reviewed` |
  `independent-review` | `derived-from-incident` | `synthetic`

## Label provenance (third-party labeling)
Benign entries are reviewed by maintainers and, where possible, cross-checked
against independent scanner outputs. Malicious entries are either derived from
documented incidents (see `derived-from-incident`) or synthetically constructed
to target a specific evasion family (`synthetic`). No benign class is labeled
by a scanner under test (OASB lesson).

## Construction pipeline
1. Define attack family in `taxonomy.yaml` + `docs/EVASION_MATRIX.md`.
2. Scaffold entry (`goat new`), author payload in `skill/`.
3. Write ground truth in `expected.yaml` outside `skill/`.
4. Embed `GOAT-CANARY-*` / `GOAT-CHAIN-*` token (plaintext-greppable).
5. Validate with `goat lint` and `goat selftest`.
6. Score scanners via `goat scan --blind`.

## Safety
All endpoints are inert (`*.example`, RFC 5737 ranges). Payloads are markers,
not malware. Run only in a sandbox (docs/SAFETY.md).

## Provenance
Generated/scored with the `goat` harness. Blind staging hashes fixture dirs
and strips canaries. Matrices include `blind`, `blind_salt`, `canary_token`.
